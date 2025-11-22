"""
산책 기록 샘플 데이터 삭제 스크립트

사용법:
    python scripts/delete_sample_walks.py [pet_id]
    
예시:
    python scripts/delete_sample_walks.py 1
    # pet_id=1의 모든 산책 기록 삭제
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db import SessionLocal
from app.models.walk import Walk
from app.models.pet import Pet


def delete_walks(pet_id: int, confirm: bool = False):
    """특정 반려동물의 모든 산책 기록 삭제"""
    db = SessionLocal()
    
    try:
        # pet_id 유효성 검사
        pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
        if not pet:
            print(f"[오류] pet_id={pet_id}인 반려동물을 찾을 수 없습니다.")
            return False
        
        # 삭제할 기록 개수 확인
        walks = db.query(Walk).filter(Walk.pet_id == pet_id).all()
        count = len(walks)
        
        if count == 0:
            print(f"[OK] pet_id={pet_id} ({pet.name})의 산책 기록이 없습니다.")
            return True
        
        if not confirm:
            print(f"[경고] pet_id={pet_id} ({pet.name})의 산책 기록 {count}개를 삭제하려고 합니다.")
            print("정말 삭제하시겠습니까? (yes/no): ", end="")
            response = input().strip().lower()
            if response not in ["yes", "y"]:
                print("[취소] 취소되었습니다.")
                return False
        
        # 삭제 실행
        for walk in walks:
            db.delete(walk)
        
        db.commit()
        print(f"[성공] {count}개의 산책 기록이 삭제되었습니다!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/delete_sample_walks.py <pet_id>")
        print("\n예시:")
        print("  python scripts/delete_sample_walks.py 1")
        sys.exit(1)
    
    try:
        pet_id = int(sys.argv[1])
    except ValueError:
        print("[오류] pet_id는 숫자여야 합니다.")
        sys.exit(1)
    
    success = delete_walks(pet_id)
    sys.exit(0 if success else 1)

