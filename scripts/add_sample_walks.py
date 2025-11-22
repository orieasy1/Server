"""
산책 기록 샘플 데이터 추가 스크립트

사용법:
    python scripts/add_sample_walks.py [pet_id] [user_id] [기록 개수]

예시:
    python scripts/add_sample_walks.py 1 1 10
    # pet_id=1, user_id=1에 대해 최근 10일간의 산책 기록 추가
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db import SessionLocal
from app.models.walk import Walk
from app.models.pet import Pet
from app.models.user import User


def get_random_walk_data():
    """랜덤한 산책 데이터 생성"""
    # 산책 시간: 15분 ~ 60분
    duration_min = random.randint(15, 60)
    
    # 거리: 평균 속도 3-5 km/h 가정
    avg_speed_kmh = random.uniform(3.0, 5.0)
    distance_km = round((duration_min / 60.0) * avg_speed_kmh, 2)
    
    # 칼로리: 거리 기반으로 대략 계산 (강아지 기준)
    calories = round(distance_km * 30, 2)  # 대략적인 계산
    
    # 날씨 상태
    weather_statuses = ["맑음", "흐림", "비", "눈", "바람"]
    weather_status = random.choice(weather_statuses)
    
    # 기온: -5도 ~ 25도
    weather_temp_c = round(random.uniform(-5.0, 25.0), 1)
    
    return {
        "duration_min": duration_min,
        "distance_km": distance_km,
        "calories": calories,
        "weather_status": weather_status,
        "weather_temp_c": weather_temp_c,
    }


def add_sample_walks(pet_id: int, user_id: int, num_days: int = 14, include_multiple_per_day: bool = True):
    """샘플 산책 기록 추가
    
    Args:
        pet_id: 반려동물 ID
        user_id: 사용자 ID
        num_days: 생성할 날짜 범위 (최근 N일)
        include_multiple_per_day: 하루에 여러 번 산책 포함 여부
    """
    db = SessionLocal()
    
    try:
        # pet_id와 user_id 유효성 검사
        pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
        if not pet:
            print(f"[오류] pet_id={pet_id}인 반려동물을 찾을 수 없습니다.")
            return False
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            print(f"[오류] user_id={user_id}인 사용자를 찾을 수 없습니다.")
            return False
        
        print(f"[OK] 반려동물: {pet.name} (pet_id={pet_id})")
        print(f"[OK] 사용자: {user_id}")
        print(f"[추가] 최근 {num_days}일간의 산책 기록을 생성합니다...")
        if include_multiple_per_day:
            print(f"[정보] 하루에 여러 번 산책한 경우도 포함됩니다.\n")
        else:
            print()
        
        walks_created = 0
        
        # 최근 num_days일간의 산책 기록 생성
        for day_offset in range(num_days):
            base_date = datetime.now() - timedelta(days=day_offset)
            date_str = base_date.strftime('%Y-%m-%d')
            
            # 하루에 산책할 횟수 결정 (1~3번)
            if include_multiple_per_day:
                # 확률: 1번 40%, 2번 40%, 3번 20%
                num_walks_today = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
            else:
                num_walks_today = 1
            
            # 하루에 여러 번 산책하는 경우 시간대 분산
            time_slots = []
            if num_walks_today == 1:
                # 하루 1번: 오전 8시~10시 또는 오후 2시~6시
                if random.random() < 0.5:
                    hour = random.randint(8, 10)
                else:
                    hour = random.randint(14, 18)
                minute = random.randint(0, 59)
                time_slots.append((hour, minute))
            elif num_walks_today == 2:
                # 하루 2번: 오전 1번, 오후 1번
                time_slots.append((random.randint(7, 10), random.randint(0, 59)))  # 오전
                time_slots.append((random.randint(14, 18), random.randint(0, 59)))  # 오후
            else:  # 3번
                # 하루 3번: 오전, 점심, 오후
                time_slots.append((random.randint(7, 9), random.randint(0, 59)))   # 오전
                time_slots.append((random.randint(11, 13), random.randint(0, 59))) # 점심
                time_slots.append((random.randint(15, 19), random.randint(0, 59))) # 오후
            
            # 각 산책 기록 생성
            for walk_num, (hour, minute) in enumerate(time_slots, 1):
                start_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 산책 데이터 생성
                walk_data = get_random_walk_data()
                duration_min = walk_data["duration_min"]
                end_time = start_time + timedelta(minutes=duration_min)
                
                # Walk 객체 생성
                walk = Walk(
                    pet_id=pet_id,
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_min=duration_min,
                    distance_km=Decimal(str(walk_data["distance_km"])),
                    calories=Decimal(str(walk_data["calories"])),
                    weather_status=walk_data["weather_status"],
                    weather_temp_c=Decimal(str(walk_data["weather_temp_c"])),
                )
                
                db.add(walk)
                walks_created += 1
                
                walk_label = f"{date_str} #{walk_num}" if num_walks_today > 1 else date_str
                print(f"  [{walks_created}] {walk_label} {start_time.strftime('%H:%M')} - "
                      f"{end_time.strftime('%H:%M')} | "
                      f"{walk_data['distance_km']}km, {duration_min}분, "
                      f"{walk_data['weather_status']} {walk_data['weather_temp_c']}°C")
        
        # 데이터베이스에 커밋
        db.commit()
        print(f"\n[성공] 총 {walks_created}개의 산책 기록이 추가되었습니다!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def list_available_pets():
    """사용 가능한 반려동물 목록 출력"""
    db = SessionLocal()
    try:
        pets = db.query(Pet).all()
        if not pets:
            print("등록된 반려동물이 없습니다.")
            return
        
        print("\n등록된 반려동물 목록:")
        print("-" * 60)
        for pet in pets:
            user = db.query(User).filter(User.user_id == pet.owner_id).first()
            print(f"  pet_id={pet.pet_id:2d} | {pet.name:10s} | owner_id={pet.owner_id} | "
                  f"family_id={pet.family_id}")
        print("-" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python scripts/add_sample_walks.py <pet_id> <user_id> [날짜 범위]")
        print("\n예시:")
        print("  python scripts/add_sample_walks.py 1 1")
        print("  python scripts/add_sample_walks.py 1 1 14  # 최근 14일간 (기본값)")
        print("  python scripts/add_sample_walks.py 1 1 30  # 최근 30일간")
        print("\n참고:")
        print("  - 하루에 1~3번 산책한 경우가 랜덤하게 포함됩니다.")
        print("  - pet_id 1과 2 둘 다에 대해 실행하려면 각각 실행하세요.")
        print("\n사용 가능한 반려동물 목록:")
        list_available_pets()
        sys.exit(1)
    
    try:
        pet_id = int(sys.argv[1])
        user_id = int(sys.argv[2])
        num_days = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    except ValueError:
        print("[오류] pet_id, user_id, 날짜 범위는 숫자여야 합니다.")
        sys.exit(1)
    
    success = add_sample_walks(pet_id, user_id, num_days, include_multiple_per_day=True)
    sys.exit(0 if success else 1)

