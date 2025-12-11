from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional
from firebase_admin import auth as firebase_auth

from app.core.firebase import verify_firebase_token, send_push_notification, send_push_notification_to_multiple
from app.domains.auth.exception import auth_error
from app.domains.auth.repository.auth_repository import AuthRepository
from app.domains.notifications.repository.notification_repository import NotificationRepository
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
from app.models.notification import Notification, NotificationType
from app.models.notification_reads import NotificationRead
from app.models.user import User
from app.domains.users.repository.user_repository import UserRepository


class AuthService:

    @staticmethod
    def login(request: Request, authorization: Optional[str], db: Session):

        # 1) Authorization 헤더 확인
        if authorization is None:
            return auth_error("AUTH_401_1", request.url.path)

        if not authorization.startswith("Bearer "):
            return auth_error("AUTH_401_2", request.url.path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return auth_error("AUTH_401_3", request.url.path)

        id_token = parts[1]

        # 2) Firebase 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return auth_error("AUTH_401_4", request.url.path)

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
            return auth_error("AUTH_400_1", request.url.path)

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
            return auth_error("AUTH_500_1", request.url.path)

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
            return auth_error("AUTH_401_1", path)

        if not authorization.startswith("Bearer "):
            return auth_error("AUTH_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return auth_error("AUTH_401_3", path)

        id_token = parts[1]

        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return auth_error("AUTH_401_4", path)

        firebase_uid = decoded.get("uid")
        if not firebase_uid:
            return auth_error("AUTH_404_1", path)

        # 2) 사용자 조회
        repo = AuthRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)
        if not user:
            return auth_error("AUTH_404_1", path)

        user_id = user.user_id

        try:
            notif_repo = NotificationRepository(db)
            user_repo = UserRepository(db)
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
                            return auth_error("AUTH_404_2", path)

                        # 신규 owner 지정
                        new_owner_member.role = MemberRole.OWNER

                        # 해당 가족의 모든 펫 owner 변경
                        db.query(Pet).filter(Pet.family_id == family_id).update(
                            {Pet.owner_id: new_owner_member.user_id},
                            synchronize_session=False
                        )

                        # 신규 오너에게 알림 + FCM 푸시
                        title = "가족 소유권이 양도되었습니다"
                        msg = f"{user.nickname or '이전 소유자'}님이 가족 소유권을 양도했습니다."
                        notif_repo.create_notification(
                            family_id=family_id,
                            target_user_id=new_owner_member.user_id,
                            related_pet_id=None,
                            related_user_id=user_id,
                            notif_type=NotificationType.FAMILY_ROLE_CHANGED,
                            title=title,
                            message=msg,
                        )
                        new_owner_tokens = user_repo.get_active_fcm_tokens_for_users(
                            [new_owner_member.user_id]
                        )
                        if new_owner_tokens:
                            result = send_push_notification_to_multiple(
                                fcm_tokens=new_owner_tokens,
                                title=title,
                                body=msg,
                                data={
                                    "type": "FAMILY_ROLE_CHANGED",
                                    "family_id": str(family_id),
                                    "new_owner_id": str(new_owner_member.user_id),
                                    "previous_owner_id": str(user_id),
                                },
                            )
                            if result.get("invalid_tokens"):
                                user_repo.remove_fcm_tokens(result["invalid_tokens"])

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

            # 사용자 개인이 생성한 펫 공유 요청/연관 알림 제거 (requester FK 제약 해소)
            share_req_ids = [
                rid for (rid,) in db.query(PetShareRequest.request_id)
                .filter(PetShareRequest.requester_id == user_id)
                .all()
            ]
            if share_req_ids:
                notif_ids = [
                    n for (n,) in db.query(Notification.notification_id)
                    .filter(Notification.related_request_id.in_(share_req_ids))
                    .all()
                ]
                if notif_ids:
                    db.query(NotificationRead).filter(
                        NotificationRead.notification_id.in_(notif_ids)
                    ).delete(synchronize_session=False)
                    db.query(Notification).filter(
                        Notification.notification_id.in_(notif_ids)
                    ).delete(synchronize_session=False)
                db.query(PetShareRequest).filter(
                    PetShareRequest.request_id.in_(share_req_ids)
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
                return auth_error("AUTH_500_2", path)

            db.commit()

            return {
                "success": True,
                "message": "회원탈퇴가 정상적으로 처리되었습니다."
            }

        except Exception as e:
            print("AUTH_DELETE_ERROR:", e)
            db.rollback()
            return auth_error("AUTH_500_1", path)

    @staticmethod
    def _delete_family_and_pets(db: Session, family_id: int):
        """
        가족 단위 삭제 (펫 및 연관 데이터 모두 제거)
        """
        # 가족 전체 알림/읽음 삭제 (family_id FK 때문에 마지막에 막히는 문제 방지)
        family_notif_ids = [
            n for (n,) in db.query(Notification.notification_id)
            .filter(Notification.family_id == family_id)
            .all()
        ]
        if family_notif_ids:
            db.query(NotificationRead).filter(
                NotificationRead.notification_id.in_(family_notif_ids)
            ).delete(synchronize_session=False)
            db.query(Notification).filter(
                Notification.notification_id.in_(family_notif_ids)
            ).delete(synchronize_session=False)

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
