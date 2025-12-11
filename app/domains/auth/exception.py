from dataclasses import dataclass
from typing import Dict

from app.core.error_handler import error_response
from app.schemas.error_schema import ErrorResponse


@dataclass(frozen=True)
class AuthError:
    status: int
    code: str
    reason: str

    def to_dict(self, path: str) -> Dict:
        """Swagger 예시용 dict."""
        return {
            "success": False,
            "status": self.status,
            "code": self.code,
            "reason": self.reason,
            "timeStamp": "...",
            "path": path,
        }


# 도메인별 에러 정의 (Auth)
AUTH_ERRORS: Dict[str, AuthError] = {
    # 400
    "AUTH_400_1": AuthError(400, "AUTH_400_1", "Firebase UID를 토큰에서 찾을 수 없습니다."),

    # 401
    "AUTH_401_1": AuthError(401, "AUTH_401_1", "Authorization 헤더가 필요합니다."),
    "AUTH_401_2": AuthError(401, "AUTH_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "AUTH_401_3": AuthError(401, "AUTH_401_3", "Authorization 헤더 형식이 잘못되었습니다."),
    "AUTH_401_4": AuthError(401, "AUTH_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다."),

    # 404
    "AUTH_404_1": AuthError(404, "AUTH_404_1", "해당 사용자를 찾을 수 없습니다."),
    "AUTH_404_2": AuthError(404, "AUTH_404_2", "가족 정보가 손상되었거나 존재하지 않습니다."),

    # 500
    "AUTH_500_1": AuthError(500, "AUTH_500_1", "데이터베이스 처리 중 오류가 발생했습니다."),
    "AUTH_500_2": AuthError(500, "AUTH_500_2", "Firebase 계정 삭제 중 오류가 발생했습니다."),
}


def auth_error(code: str, path: str):
    """정의된 Auth 에러코드 기반 표준 에러 응답 생성."""
    err = AUTH_ERRORS.get(code)
    if not err:
        return error_response(500, "AUTH_500_2", "서버 내부 오류가 발생했습니다.", path)
    return error_response(err.status, err.code, err.reason, path)


def _examples_for_codes(path: str, codes: Dict[str, AuthError]) -> Dict:
    """Swagger examples 생성 헬퍼."""
    return {
        code: {"value": err.to_dict(path)}
        for code, err in codes.items()
    }


# Swagger responses: 로그인
AUTH_LOGIN_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/login", {
                    "AUTH_400_1": AUTH_ERRORS["AUTH_400_1"],
                })
            }
        },
    },
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/login", {
                    "AUTH_401_1": AUTH_ERRORS["AUTH_401_1"],
                    "AUTH_401_2": AUTH_ERRORS["AUTH_401_2"],
                    "AUTH_401_3": AUTH_ERRORS["AUTH_401_3"],
                    "AUTH_401_4": AUTH_ERRORS["AUTH_401_4"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/login", {
                    "AUTH_500_1": AUTH_ERRORS["AUTH_500_1"],
                })
            }
        },
    },
}


# Swagger responses: 회원탈퇴
AUTH_DELETE_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/delete", {
                    "AUTH_401_1": AUTH_ERRORS["AUTH_401_1"],
                    "AUTH_401_2": AUTH_ERRORS["AUTH_401_2"],
                    "AUTH_401_3": AUTH_ERRORS["AUTH_401_3"],
                    "AUTH_401_4": AUTH_ERRORS["AUTH_401_4"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "대상 없음",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/delete", {
                    "AUTH_404_1": AUTH_ERRORS["AUTH_404_1"],
                    "AUTH_404_2": AUTH_ERRORS["AUTH_404_2"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/auth/delete", {
                    "AUTH_500_1": AUTH_ERRORS["AUTH_500_1"],
                    "AUTH_500_2": AUTH_ERRORS["AUTH_500_2"],
                })
            }
        },
    },
}
