import firebase_admin
from firebase_admin import credentials, auth, storage, messaging
from app.core.config import settings
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Firebase Credential 파일 경로 로드
print(f"[INFO] Loading Firebase credentials from: {settings.FIREBASE_CREDENTIALS}")
try:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
    print(f"[INFO] Firebase credentials loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load Firebase credentials: {e}")
    raise

# Firebase Storage 버킷 이름 (환경 변수에서 가져오거나 기본값 사용)
STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "takeapaw-67bf2.appspot.com")

# 앱 초기화 (중복 초기화 방지)
if not firebase_admin._apps:
    try:
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET
        })
        print(f"[INFO] Firebase Admin SDK initialized successfully with bucket: {STORAGE_BUCKET}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Firebase Admin SDK: {e}")
        raise
else:
    print(f"[INFO] Firebase Admin SDK already initialized")


def verify_firebase_token(id_token: str):
    try:
        # check_revoked=False로 설정하여 성능 향상
        # clock_skew_seconds=60으로 시계 오차 60초까지 허용
        decoded = auth.verify_id_token(
            id_token, 
            check_revoked=False,
            clock_skew_seconds=60  # 시계 오차 60초 허용
        )
        return decoded
    except Exception as e:
        print(f"[ERROR] Firebase token verification failed: {type(e).__name__}: {str(e)}")
        # 시계 동기화 문제인 경우 추가 안내
        if "used too early" in str(e) or "clock" in str(e).lower():
            print("[HINT] This is a clock synchronization issue. Please sync your system time.")
        return None


def upload_file_to_storage(
    file_content: bytes,
    file_name: str,
    content_type: str = "image/jpeg",
    folder: str = "walk_photos"
) -> str:
    """
    Firebase Storage에 파일 업로드
    
    Returns:
        str: 업로드된 파일의 public URL
    """
    try:
        bucket = storage.bucket(STORAGE_BUCKET) if STORAGE_BUCKET else storage.bucket()
        
        # 파일 경로 생성
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_path = f"{folder}/{timestamp}_{file_name}"
        
        # Blob 생성 및 업로드
        blob = bucket.blob(blob_path)
        blob.upload_from_string(file_content, content_type=content_type)
        
        # Public URL 반환
        blob.make_public()
        return blob.public_url
        
    except Exception as e:
        print(f"STORAGE_UPLOAD_ERROR: {e}")
        raise Exception("STORAGE_UPLOAD_FAILED")


def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    FCM 푸시 알림을 전송합니다.
    
    Args:
        fcm_token: 수신자의 FCM 토큰
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터 (선택사항)
    
    Returns:
        bool: 전송 성공 여부
    """
    try:
        # 알림 메시지 구성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in (data or {}).items()},  # FCM data는 문자열만 허용
            token=fcm_token,
            # Android 전용 설정
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_notification",
                    color="#FF6B6B",
                    sound="default",
                    click_action="OPEN_NOTIFICATION",
                ),
            ),
        )
        
        # 메시지 전송
        response = messaging.send(message)
        print(f"[FCM] Successfully sent message: {response}")
        return True
        
    except messaging.UnregisteredError:
        # 토큰이 더 이상 유효하지 않음 (앱 삭제 등)
        print(f"[FCM] Token is no longer valid: {fcm_token[:20]}...")
        return False
        
    except Exception as e:
        print(f"[FCM] Error sending message: {e}")
        return False


def send_push_notification_to_multiple(
    fcm_tokens: list,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    여러 사용자에게 FCM 푸시 알림을 전송합니다.
    
    Args:
        fcm_tokens: 수신자들의 FCM 토큰 리스트
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터 (선택사항)
    
    Returns:
        Dict: 전송 결과 (success_count, failure_count, failed_tokens)
    """
    if not fcm_tokens:
        return {"success_count": 0, "failure_count": 0, "failed_tokens": []}
    
    # 유효한 토큰만 필터링
    valid_tokens = [t for t in fcm_tokens if t]
    if not valid_tokens:
        return {"success_count": 0, "failure_count": 0, "failed_tokens": []}
    
    try:
        payload_data = {k: str(v) for k, v in (data or {}).items()}
        if "type" not in payload_data:
            payload_data["type"] = payload_data.get("type", "GENERIC")

        # MulticastMessage 구성
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=payload_data,
            tokens=valid_tokens,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_notification",
                    color="#FF6B6B",
                    sound="default",
                    click_action="OPEN_NOTIFICATION",
                ),
            ),
        )
        
        # 메시지 전송
        response = messaging.send_each_for_multicast(message)
        
        # 실패한 토큰 수집
        failed_tokens = []
        invalid_tokens = []
        failure_details = []
        for idx, send_response in enumerate(response.responses):
            if not send_response.success:
                failed_tokens.append(valid_tokens[idx])
                error_obj = getattr(send_response, "exception", None)
                error_code = getattr(error_obj, "code", None)
                failure_details.append({
                    "token": valid_tokens[idx],
                    "code": error_code,
                    "exception": type(error_obj).__name__ if error_obj else "UnknownError",
                })
                if isinstance(error_obj, messaging.UnregisteredError) or error_code in (
                    "registration-token-not-registered",
                    "invalid-argument",
                ):
                    invalid_tokens.append(valid_tokens[idx])
        
        print(f"[FCM] Multicast result: {response.success_count} success, {response.failure_count} failures")
        
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "failed_tokens": failed_tokens,
            "invalid_tokens": invalid_tokens,
            "failure_details": failure_details,
        }
        
    except Exception as e:
        print(f"[FCM] Error sending multicast: {e}")
        return {
            "success_count": 0,
            "failure_count": len(valid_tokens),
            "failed_tokens": valid_tokens,
            # Do NOT mark all tokens invalid on generic errors; keep them for retry.
            "invalid_tokens": [],
            "failure_details": [{"token": t, "code": "exception", "exception": type(e).__name__} for t in valid_tokens],
        }
