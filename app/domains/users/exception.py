from dataclasses import dataclass
from typing import Dict

from app.core.error_handler import error_response
from app.schemas.error_schema import ErrorResponse


@dataclass(frozen=True)
class UserError:
    status: int
    code: str
    reason: str

    def to_dict(self, path: str) -> Dict:
        return {
            "success": False,
            "status": self.status,
            "code": self.code,
            "reason": self.reason,
            "timeStamp": "...",
            "path": path,
        }


USER_ERRORS: Dict[str, UserError] = {
    # GET /me
    "USER_GET_401_1": UserError(401, "USER_GET_401_1", "Authorization 헤더가 필요합니다."),
    "USER_GET_401_2": UserError(401, "USER_GET_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "USER_GET_401_3": UserError(401, "USER_GET_401_3", "Authorization 헤더 형식이 잘못되었습니다."),
    "USER_GET_401_4": UserError(401, "USER_GET_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다."),
    "USER_GET_404_1": UserError(404, "USER_GET_404_1", "해당 사용자를 찾을 수 없습니다."),
    "USER_GET_500_2": UserError(500, "USER_GET_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다."),

    # PATCH /me
    "USER_EDIT_401_1": UserError(401, "USER_EDIT_401_1", "Authorization 헤더가 필요합니다."),
    "USER_EDIT_401_2": UserError(401, "USER_EDIT_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "USER_EDIT_401_3": UserError(401, "USER_EDIT_401_3", "Authorization 헤더 형식이 잘못되었습니다."),
    "USER_EDIT_401_4": UserError(401, "USER_EDIT_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다."),
    "USER_EDIT_404_1": UserError(404, "USER_EDIT_404_1", "해당 사용자를 찾을 수 없습니다."),
    "USER_EDIT_400_1": UserError(400, "USER_EDIT_400_1", "수정할 필드가 존재하지 않습니다."),
    "USER_EDIT_400_3": UserError(400, "USER_EDIT_400_3", "전화번호 형식이 올바르지 않습니다."),
    "USER_EDIT_500_1": UserError(500, "USER_EDIT_500_1", "사용자 정보를 수정하는 중 오류가 발생했습니다."),
    "USER_EDIT_500_2": UserError(500, "USER_EDIT_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다."),

    # PUT /me/fcm-token
    "FCM_401_1": UserError(401, "FCM_401_1", "Authorization 헤더가 필요합니다."),
    "FCM_401_2": UserError(401, "FCM_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "FCM_401_3": UserError(401, "FCM_401_3", "Authorization 헤더 형식이 잘못되었습니다."),
    "FCM_401_4": UserError(401, "FCM_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다."),
    "FCM_404_1": UserError(404, "FCM_404_1", "해당 사용자를 찾을 수 없습니다."),
    "FCM_500_1": UserError(500, "FCM_500_1", "FCM 토큰 업데이트 중 오류가 발생했습니다."),
    "FCM_500_2": UserError(500, "FCM_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다."),
}


def user_error(code: str, path: str):
    err = USER_ERRORS.get(code)
    if not err:
        return error_response(500, "USER_EDIT_500_1", "서버 내부 오류가 발생했습니다.", path)
    return error_response(err.status, err.code, err.reason, path)


def _examples_for_codes(path: str, codes: Dict[str, UserError]) -> Dict:
    return {
        code: {"value": err.to_dict(path)}
        for code, err in codes.items()
    }


USER_GET_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_GET_401_1": USER_ERRORS["USER_GET_401_1"],
                    "USER_GET_401_2": USER_ERRORS["USER_GET_401_2"],
                    "USER_GET_401_3": USER_ERRORS["USER_GET_401_3"],
                    "USER_GET_401_4": USER_ERRORS["USER_GET_401_4"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "사용자 없음",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_GET_404_1": USER_ERRORS["USER_GET_404_1"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_GET_500_2": USER_ERRORS["USER_GET_500_2"],
                })
            }
        },
    },
}


USER_EDIT_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_EDIT_400_1": USER_ERRORS["USER_EDIT_400_1"],
                    "USER_EDIT_400_3": USER_ERRORS["USER_EDIT_400_3"],
                })
            }
        },
    },
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_EDIT_401_1": USER_ERRORS["USER_EDIT_401_1"],
                    "USER_EDIT_401_2": USER_ERRORS["USER_EDIT_401_2"],
                    "USER_EDIT_401_3": USER_ERRORS["USER_EDIT_401_3"],
                    "USER_EDIT_401_4": USER_ERRORS["USER_EDIT_401_4"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "사용자 없음",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_EDIT_404_1": USER_ERRORS["USER_EDIT_404_1"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me", {
                    "USER_EDIT_500_1": USER_ERRORS["USER_EDIT_500_1"],
                    "USER_EDIT_500_2": USER_ERRORS["USER_EDIT_500_2"],
                })
            }
        },
    },
}


FCM_UPDATE_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me/fcm-token", {
                    "FCM_401_1": USER_ERRORS["FCM_401_1"],
                    "FCM_401_2": USER_ERRORS["FCM_401_2"],
                    "FCM_401_3": USER_ERRORS["FCM_401_3"],
                    "FCM_401_4": USER_ERRORS["FCM_401_4"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "사용자 없음",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me/fcm-token", {
                    "FCM_404_1": USER_ERRORS["FCM_404_1"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples_for_codes("/api/v1/users/me/fcm-token", {
                    "FCM_500_1": USER_ERRORS["FCM_500_1"],
                    "FCM_500_2": USER_ERRORS["FCM_500_2"],
                })
            }
        },
    },
}
