from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional
from firebase_admin import auth as firebase_auth

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.domains.auth.repository.auth_repository import AuthRepository
from app.models.family_member import FamilyMember, MemberRole
from app.models.family import Family
from app.models.pet import Pet
from app.models.walk import Walk
from app.models.walk_tracking_point import WalkTrackingPoint
from app.models.photo import Photo
from app.models.activity_stat import ActivityStat
from app.models.pet_walk_goal import PetWalkGoal
from app.models.pet_walk_recommendation import PetWalkRecommendation
from app.models.pet_share_request import PetShareRequest
from app.models.notification import Notification
from app.models.notification_reads import NotificationRead
from app.models.user import User


class AuthService:

    @staticmethod
    def login(request: Request, authorization: Optional[str], db: Session):

        # 1) Authorization 헤더 확인
        if authorization is None:
            return error_response(
                401, "AUTH_401_1", "Authorization 헤더가 필요합니다.", request.url.path
            )

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "AUTH_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", request.url.path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "AUTH_401_3", "Authorization 헤더 형식이 잘못되었습니다.", request.url.path
            )

        id_token = parts[1]

        # 2) Firebase 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(
                401, "AUTH_401_4", 
                "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.",
                request.url.path
            )

        firebase_uid = decoded.get("uid")
        email = decoded.get("email")
        nickname = decoded.get("name") or decoded.get("displayName")
        picture = decoded.get("picture")
        provider = decoded.get("firebase", {}).get("sign_in_provider")

        # ⭐ provider → sns(enum) 변환
        provider_map = {
            "google.com": "google",
            "apple.com": "apple",
            "oidc.kakao": "kakao",
            "custom": "kakao",
            "password": "email"
        }
        sns = provider_map.get(provider, "email")

        # 3) 필수 필드 확인
        if not firebase_uid:
            return error_response(
                400, "AUTH_400_1", "Firebase UID를 토큰에서 찾을 수 없습니다.", request.url.path
            )

        # 4) DB 접근
        repo = AuthRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        # --- 기존 유저 로그인 ---
        if user:
            return {
                "is_new_user": False,
                "user": {
                    "user_id": user.user_id,
                    "firebase_uid": user.firebase_uid,
                    "nickname": user.nickname,
                    "email": user.email,
                    "phone": user.phone,
                    "profile_img_url": user.profile_img_url,
                    "sns": user.sns
                }
            }

        # --- 신규 회원가입 ---
        try:
            new_user = repo.create_user(
                firebase_uid=firebase_uid,
                nickname=nickname or f"user_{firebase_uid[:6]}",
                email=email,
                profile_img_url=picture,
                sns=sns
            )
        except Exception as e:
            db.rollback()
            print("🔥 DB ERROR:", e)
            return error_response(
                500, "AUTH_500_1",
                "데이터베이스 처리 중 오류가 발생했습니다.",
                request.url.path
            )

        # --- 신규 회원가입 응답 ---
        return {
            "is_new_user": True,
            "user": {
                "user_id": new_user.user_id,
                "firebase_uid": new_user.firebase_uid,
                "nickname": new_user.nickname,
                "email": new_user.email,
                "phone": new_user.phone,
                "profile_img_url": new_user.profile_img_url,
                "sns": new_user.sns   
            }
        }

    @staticmethod
    def delete_account(request: Request, authorization: Optional[str], db: Session):
        path = request.url.path

        # 1) Authorization 헤더 검증
        if authorization is None:
            return error_response(401, "AUTH_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "AUTH_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "AUTH_401_3", "Authorization 헤더 형식이 잘못되었습니다.", path)

        id_token = parts[1]

        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "AUTH_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")
        if not firebase_uid:
            return error_response(404, "AUTH_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 2) 사용자 조회
        repo = AuthRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)
        if not user:
            return error_response(404, "AUTH_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        user_id = user.user_id

        try:
            # 사용자가 속한 모든 family_member 조회
            memberships = (
                db.query(FamilyMember)
                .filter(FamilyMember.user_id == user_id)
                .all()
            )

            if not memberships:
                # 가족이 없더라도 사용자만 삭제하고 종료
                db.query(User).filter(User.user_id == user_id).delete(synchronize_session=False)
                try:
                    firebase_auth.delete_user(firebase_uid)
                except firebase_auth.UserNotFoundError:
                    # 이미 Firebase에 없으면 무시하고 진행
                    print(f"AUTH_FIREBASE_DELETE_SKIP: user {firebase_uid} not found in Firebase")
                except Exception as fe:
                    print("AUTH_FIREBASE_DELETE_ERROR:", fe)
                    db.rollback()
                    return error_response(500, "AUTH_500_2", "Firebase 계정 삭제 중 오류가 발생했습니다.", path)
                db.commit()
                return {
                    "success": True,
                    "message": "회원탈퇴가 정상적으로 처리되었습니다."
                }

            for membership in memberships:
                family_id = membership.family_id

                # 가족 멤버 전체 조회 (joined_at 오름차순)
                members = (
                    db.query(FamilyMember)
                    .filter(FamilyMember.family_id == family_id)
                    .order_by(FamilyMember.joined_at.asc())
                    .all()
                )

                if not members:
                    # 가족이 없으면 스킵
                    continue

                member_count = len(members)
                is_owner = membership.role == MemberRole.OWNER

                if member_count == 1:
                    # Case 2: 본인만 존재 → 가족/펫/연관 데이터 삭제
                    AuthService._delete_family_and_pets(db, family_id)
                else:
                    if is_owner:
                        # Case 1: owner이고 멤버 2명 이상 → 소유권 이전 후 본인 탈퇴
                        new_owner_member = next((m for m in members if m.user_id != user_id), None)
                        if not new_owner_member:
                            # 이론상 발생 X
                            return error_response(404, "AUTH_404_2", "가족 정보가 손상되었거나 존재하지 않습니다.", path)

                        # 신규 owner 지정
                        new_owner_member.role = MemberRole.OWNER

                        # 해당 가족의 모든 펫 owner 변경
                        db.query(Pet).filter(Pet.family_id == family_id).update(
                            {Pet.owner_id: new_owner_member.user_id},
                            synchronize_session=False
                        )

                        # 본인 family_member 삭제
                        db.query(FamilyMember).filter(
                            FamilyMember.family_id == family_id,
                            FamilyMember.user_id == user_id
                        ).delete(synchronize_session=False)
                    else:
                        # Case 3: 단순 멤버 → 멤버십만 제거
                        db.query(FamilyMember).filter(
                            FamilyMember.family_id == family_id,
                            FamilyMember.user_id == user_id
                        ).delete(synchronize_session=False)

            # 모든 가족 처리 후 사용자 삭제
            db.query(User).filter(User.user_id == user_id).delete(synchronize_session=False)

            # Firebase 계정 삭제 (Admin SDK)
            try:
                firebase_auth.delete_user(firebase_uid)
            except firebase_auth.UserNotFoundError:
                # 이미 Firebase에 없으면 무시하고 진행
                print(f"AUTH_FIREBASE_DELETE_SKIP: user {firebase_uid} not found in Firebase")
            except Exception as fe:
                print("AUTH_FIREBASE_DELETE_ERROR:", fe)
                db.rollback()
                return error_response(500, "AUTH_500_2", "Firebase 계정 삭제 중 오류가 발생했습니다.", path)

            db.commit()

            return {
                "success": True,
                "message": "회원탈퇴가 정상적으로 처리되었습니다."
            }

        except Exception as e:
            print("AUTH_DELETE_ERROR:", e)
            db.rollback()
            return error_response(500, "AUTH_500_1", "데이터베이스 처리 중 오류가 발생했습니다.", path)

    @staticmethod
    def _delete_family_and_pets(db: Session, family_id: int):
        """
        가족 단위 삭제 (펫 및 연관 데이터 모두 제거)
        """
        # 가족의 모든 pet_id만 먼저 모은 뒤, 참조 순서대로 일괄 삭제
        pet_ids = [pid for (pid,) in db.query(Pet.pet_id).filter(Pet.family_id == family_id).all()]
        if pet_ids:
            # Walk -> TrackingPoint/Photo -> Walk -> ActivityStat -> Goals -> Recommendations -> ShareRequest/Notifications
            walk_ids = [w for (w,) in db.query(Walk.walk_id).filter(Walk.pet_id.in_(pet_ids)).all()]
            if walk_ids:
                db.query(WalkTrackingPoint).filter(WalkTrackingPoint.walk_id.in_(walk_ids)).delete(synchronize_session=False)
                db.query(Photo).filter(Photo.walk_id.in_(walk_ids)).delete(synchronize_session=False)
            db.query(Walk).filter(Walk.pet_id.in_(pet_ids)).delete(synchronize_session=False)

            db.query(ActivityStat).filter(ActivityStat.pet_id.in_(pet_ids)).delete(synchronize_session=False)
            db.query(PetWalkGoal).filter(PetWalkGoal.pet_id.in_(pet_ids)).delete(synchronize_session=False)
            db.query(PetWalkRecommendation).filter(PetWalkRecommendation.pet_id.in_(pet_ids)).delete(synchronize_session=False)

            share_ids = [sid for (sid,) in db.query(PetShareRequest.request_id).filter(PetShareRequest.pet_id.in_(pet_ids)).all()]
            if share_ids:
                notif_ids = [
                    n for (n,) in db.query(Notification.notification_id)
                    .filter(Notification.related_request_id.in_(share_ids))
                    .all()
                ]
                if notif_ids:
                    db.query(NotificationRead).filter(
                        NotificationRead.notification_id.in_(notif_ids)
                    ).delete(synchronize_session=False)
                db.query(Notification).filter(
                    Notification.related_request_id.in_(share_ids)
                ).delete(synchronize_session=False)

            db.query(PetShareRequest).filter(PetShareRequest.pet_id.in_(pet_ids)).delete(synchronize_session=False)

            notif_ids = [
                n for (n,) in db.query(Notification.notification_id)
                .filter(Notification.related_pet_id.in_(pet_ids))
                .all()
            ]
            if notif_ids:
                db.query(NotificationRead).filter(
                    NotificationRead.notification_id.in_(notif_ids)
                ).delete(synchronize_session=False)
                db.query(Notification).filter(
                    Notification.notification_id.in_(notif_ids)
                ).delete(synchronize_session=False)

            # 마지막으로 모든 펫 삭제 (bulk)
            db.query(Pet).filter(Pet.pet_id.in_(pet_ids)).delete(synchronize_session=False)

        # 가족 멤버 삭제 및 가족 삭제
        db.query(FamilyMember).filter(FamilyMember.family_id == family_id).delete(synchronize_session=False)
        db.query(Family).filter(Family.family_id == family_id).delete(synchronize_session=False)
