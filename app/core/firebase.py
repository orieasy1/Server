import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings

# Firebase Credential 파일 경로 로드
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)

# 앱 초기화 (중복 초기화 방지)
if not firebase_admin._apps:
    firebase_app = firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str):
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None
