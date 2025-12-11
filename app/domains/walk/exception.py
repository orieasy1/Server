from dataclasses import dataclass
from typing import Dict

from app.core.error_handler import error_response
from app.schemas.error_schema import ErrorResponse


@dataclass(frozen=True)
class WalkError:
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


# 사진 업로드 관련 에러 정의
PHOTO_ERRORS: Dict[str, WalkError] = {
    "WALK_PHOTO_401_1": WalkError(401, "WALK_PHOTO_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_PHOTO_401_2": WalkError(401, "WALK_PHOTO_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_PHOTO_404_1": WalkError(404, "WALK_PHOTO_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_PHOTO_404_2": WalkError(404, "WALK_PHOTO_404_2", "요청하신 산책 세션을 찾을 수 없습니다."),
    "WALK_PHOTO_400_1": WalkError(400, "WALK_PHOTO_400_1", "업로드할 이미지 파일이 필요합니다."),
    "WALK_PHOTO_400_2": WalkError(400, "WALK_PHOTO_400_2", "지원하지 않는 이미지 형식입니다. JPG 또는 PNG 파일을 업로드해주세요."),
    "WALK_PHOTO_400_3": WalkError(400, "WALK_PHOTO_400_3", "이미지 파일 크기가 허용 범위를 초과했습니다."),
    "WALK_PHOTO_400_4": WalkError(400, "WALK_PHOTO_400_4", "사진 촬영 시간이 산책 시간과 맞지 않습니다. 산책 중에 촬영한 사진만 업로드해주세요."),
    "WALK_PHOTO_409_1": WalkError(409, "WALK_PHOTO_409_1", "종료되지 않은 산책에는 인증 사진을 업로드할 수 없습니다."),
    "WALK_PHOTO_403_1": WalkError(403, "WALK_PHOTO_403_1", "해당 산책에 사진을 업로드할 권한이 없습니다."),
    "WALK_PHOTO_500_1": WalkError(500, "WALK_PHOTO_500_1", "이미지 업로드 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."),
    "WALK_PHOTO_500_2": WalkError(500, "WALK_PHOTO_500_2", "산책 사진 기록을 저장하는 중 오류가 발생했습니다."),
}

RANKING_ERRORS: Dict[str, WalkError] = {
    "WALK_RANKING_401_1": WalkError(401, "WALK_RANKING_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_RANKING_401_2": WalkError(401, "WALK_RANKING_401_2", "Authorization 형식이 잘못되었습니다."),
    "WALK_RANKING_401_3": WalkError(401, "WALK_RANKING_401_3", "DB에 사용자 정보가 존재하지 않습니다."),
    "WALK_RANKING_400_1": WalkError(400, "WALK_RANKING_400_1", "period는 weekly, monthly, total 중 하나여야 합니다."),
    "WALK_RANKING_400_2": WalkError(400, "WALK_RANKING_400_2", "family_id는 필수 값입니다."),
    "WALK_RANKING_404_1": WalkError(404, "WALK_RANKING_404_1", "해당 가족을 찾을 수 없습니다."),
    "WALK_RANKING_404_2": WalkError(404, "WALK_RANKING_404_2", "이번 기간에는 산책 기록이 존재하지 않습니다."),
    "WALK_RANKING_403_1": WalkError(403, "WALK_RANKING_403_1", "해당 가족 구성원이 아니므로 접근할 수 없습니다."),
}

RECOMMEND_ERRORS: Dict[str, WalkError] = {
    "WALK_REC_401_1": WalkError(401, "WALK_REC_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_REC_401_2": WalkError(401, "WALK_REC_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_REC_404_1": WalkError(404, "WALK_REC_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_REC_404_2": WalkError(404, "WALK_REC_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_REC_404_3": WalkError(404, "WALK_REC_404_3", "해당 반려동물의 추천 산책 정보가 아직 생성되지 않았습니다."),
    "WALK_REC_403_1": WalkError(403, "WALK_REC_403_1", "해당 반려동물의 추천 정보를 조회할 권한이 없습니다."),
    "WALK_REC_500_1": WalkError(500, "WALK_REC_500_1", "추천 산책 정보를 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."),
}

TODAY_ERRORS: Dict[str, WalkError] = {
    "WALK_TODAY_401_1": WalkError(401, "WALK_TODAY_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_TODAY_401_2": WalkError(401, "WALK_TODAY_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_TODAY_404_1": WalkError(404, "WALK_TODAY_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_TODAY_404_2": WalkError(404, "WALK_TODAY_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_TODAY_403_1": WalkError(403, "WALK_TODAY_403_1", "해당 반려동물의 산책 정보를 조회할 권한이 없습니다."),
    "WALK_TODAY_500_1": WalkError(500, "WALK_TODAY_500_1", "오늘 산책 현황을 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."),
}

def _examples(path: str, mapping: Dict[str, WalkError]) -> Dict:
    return {
        code: {"value": err.to_dict(path)}
        for code, err in mapping.items()
    }


PHOTO_UPLOAD_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_400_1": PHOTO_ERRORS["WALK_PHOTO_400_1"],
                    "WALK_PHOTO_400_2": PHOTO_ERRORS["WALK_PHOTO_400_2"],
                    "WALK_PHOTO_400_3": PHOTO_ERRORS["WALK_PHOTO_400_3"],
                    "WALK_PHOTO_400_4": PHOTO_ERRORS["WALK_PHOTO_400_4"],
                })
            }
        },
    },
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_401_1": PHOTO_ERRORS["WALK_PHOTO_401_1"],
                    "WALK_PHOTO_401_2": PHOTO_ERRORS["WALK_PHOTO_401_2"],
                })
            }
        },
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_403_1": PHOTO_ERRORS["WALK_PHOTO_403_1"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "리소스 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_404_1": PHOTO_ERRORS["WALK_PHOTO_404_1"],
                    "WALK_PHOTO_404_2": PHOTO_ERRORS["WALK_PHOTO_404_2"],
                })
            }
        },
    },
    409: {
        "model": ErrorResponse,
        "description": "중복/상태 오류",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_409_1": PHOTO_ERRORS["WALK_PHOTO_409_1"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/sessions/{walk_id}/photo", {
                    "WALK_PHOTO_500_1": PHOTO_ERRORS["WALK_PHOTO_500_1"],
                    "WALK_PHOTO_500_2": PHOTO_ERRORS["WALK_PHOTO_500_2"],
                })
            }
        },
    },
}

RECOMMEND_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
    },
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/recommendation", {
                    "WALK_REC_401_1": RECOMMEND_ERRORS["WALK_REC_401_1"],
                    "WALK_REC_401_2": RECOMMEND_ERRORS["WALK_REC_401_2"],
                })
            }
        },
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/recommendation", {
                    "WALK_REC_403_1": RECOMMEND_ERRORS["WALK_REC_403_1"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "리소스 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/recommendation", {
                    "WALK_REC_404_1": RECOMMEND_ERRORS["WALK_REC_404_1"],
                    "WALK_REC_404_2": RECOMMEND_ERRORS["WALK_REC_404_2"],
                    "WALK_REC_404_3": RECOMMEND_ERRORS["WALK_REC_404_3"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/recommendation", {
                    "WALK_REC_500_1": RECOMMEND_ERRORS["WALK_REC_500_1"],
                })
            }
        },
    },
}

# Session start/track/end Swagger 응답
SESSION_START_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    409: {"model": ErrorResponse, "description": "이미 진행 중인 산책"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

SESSION_TRACK_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
    409: {"model": ErrorResponse, "description": "이미 종료된 산책"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

SESSION_END_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
    409: {"model": ErrorResponse, "description": "이미 종료된 산책"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

SAVE_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

NOTIFY_RESPONSES = {
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

WEATHER_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패 (선택)"},
    502: {"model": ErrorResponse, "description": "외부 API 게이트웨이 오류"},
    503: {"model": ErrorResponse, "description": "외부 API 서비스 불가"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

TODAY_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/today", {
                    "WALK_TODAY_401_1": TODAY_ERRORS["WALK_TODAY_401_1"],
                    "WALK_TODAY_401_2": TODAY_ERRORS["WALK_TODAY_401_2"],
                })
            }
        },
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/today", {
                    "WALK_TODAY_403_1": TODAY_ERRORS["WALK_TODAY_403_1"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "리소스 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/today", {
                    "WALK_TODAY_404_1": TODAY_ERRORS["WALK_TODAY_404_1"],
                    "WALK_TODAY_404_2": TODAY_ERRORS["WALK_TODAY_404_2"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/today", {
                    "WALK_TODAY_500_1": TODAY_ERRORS["WALK_TODAY_500_1"],
                })
            }
        },
    },
}
# Session (start/track/end) 에러 정의
SESSION_ERRORS: Dict[str, WalkError] = {
    # start
    "WALK_START_401_1": WalkError(401, "WALK_START_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_START_401_2": WalkError(401, "WALK_START_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_START_404_1": WalkError(404, "WALK_START_404_1", "사용자를 찾을 수 없습니다."),
    "WALK_START_404_2": WalkError(404, "WALK_START_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_START_403_1": WalkError(403, "WALK_START_403_1", "해당 반려동물 산책을 시작할 권한이 없습니다."),
    "WALK_START_400_1": WalkError(400, "WALK_START_400_1", "start_lat와 start_lng는 둘 다 있거나 둘 다 없어야 합니다."),
    "WALK_START_400_2": WalkError(400, "WALK_START_400_2", "위도/경도 값이 유효 범위를 벗어났습니다."),
    "WALK_START_409_1": WalkError(409, "WALK_START_409_1", "이미 진행 중인 산책이 있습니다."),
    "WALK_START_500_1": WalkError(500, "WALK_START_500_1", "산책을 시작하는 중 오류가 발생했습니다."),

    # track
    "WALK_POINT_401_1": WalkError(401, "WALK_POINT_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_POINT_401_2": WalkError(401, "WALK_POINT_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_POINT_404_1": WalkError(404, "WALK_POINT_404_1", "사용자를 찾을 수 없습니다."),
    "WALK_POINT_404_2": WalkError(404, "WALK_POINT_404_2", "요청하신 산책 세션을 찾을 수 없습니다."),
    "WALK_POINT_403_1": WalkError(403, "WALK_POINT_403_1", "해당 산책을 기록할 권한이 없습니다."),
    "WALK_POINT_400_1": WalkError(400, "WALK_POINT_400_1", "위도/경도 값이 유효 범위를 벗어났습니다."),
    "WALK_POINT_400_2": WalkError(400, "WALK_POINT_400_2", "위도와 경도는 둘 다 있어야 합니다."),
    "WALK_POINT_409_1": WalkError(409, "WALK_POINT_409_1", "이미 종료된 산책입니다."),
    "WALK_POINT_500_1": WalkError(500, "WALK_POINT_500_1", "산책 위치를 기록하는 중 오류가 발생했습니다."),

    # end
    "WALK_END_401_1": WalkError(401, "WALK_END_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_END_401_2": WalkError(401, "WALK_END_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_END_404_1": WalkError(404, "WALK_END_404_1", "사용자를 찾을 수 없습니다."),
    "WALK_END_404_2": WalkError(404, "WALK_END_404_2", "요청하신 산책 세션을 찾을 수 없습니다."),
    "WALK_END_403_1": WalkError(403, "WALK_END_403_1", "해당 산책을 종료할 권한이 없습니다."),
    "WALK_END_400_1": WalkError(400, "WALK_END_400_1", "총 이동 거리 값이 올바르지 않습니다."),
    "WALK_END_400_2": WalkError(400, "WALK_END_400_2", "총 산책 시간 값이 올바르지 않습니다."),
    "WALK_END_409_1": WalkError(409, "WALK_END_409_1", "이미 종료된 산책 세션입니다."),
    "WALK_END_500_1": WalkError(500, "WALK_END_500_1", "산책을 종료하는 중 오류가 발생했습니다."),
}

SAVE_ERRORS: Dict[str, WalkError] = {
    "WALK_SAVE_401_1": WalkError(401, "WALK_SAVE_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_SAVE_401_2": WalkError(401, "WALK_SAVE_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_SAVE_404_1": WalkError(404, "WALK_SAVE_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_SAVE_404_2": WalkError(404, "WALK_SAVE_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_SAVE_403_1": WalkError(403, "WALK_SAVE_403_1", "해당 반려동물의 산책 기록을 저장할 권한이 없습니다."),
    "WALK_SAVE_400_1": WalkError(400, "WALK_SAVE_400_1", "종료 시간은 시작 시간보다 이후여야 합니다."),
    "WALK_SAVE_400_2": WalkError(400, "WALK_SAVE_400_2", "날짜/시간 형식이 올바르지 않습니다. ISO 8601 형식을 사용해주세요."),
    "WALK_SAVE_500_1": WalkError(500, "WALK_SAVE_500_1", "산책 기록 저장 중 오류가 발생했습니다."),
}

NOTIFY_ERRORS: Dict[str, WalkError] = {
    "WALK_NOTIFY_401_1": WalkError(401, "WALK_NOTIFY_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_NOTIFY_401_2": WalkError(401, "WALK_NOTIFY_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_NOTIFY_404_1": WalkError(404, "WALK_NOTIFY_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_NOTIFY_404_2": WalkError(404, "WALK_NOTIFY_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_NOTIFY_403_1": WalkError(403, "WALK_NOTIFY_403_1", "해당 반려동물의 산책 알림을 전송할 권한이 없습니다."),
    "WALK_NOTIFY_500_1": WalkError(500, "WALK_NOTIFY_500_1", "산책 알림 전송 중 오류가 발생했습니다."),
}

WEATHER_ERRORS: Dict[str, WalkError] = {
    "WEATHER_400_1": WalkError(400, "WEATHER_400_1", "lat와 lng 쿼리 파라미터는 필수입니다."),
    "WEATHER_400_2": WalkError(400, "WEATHER_400_2", "위도(lat)는 -90~90, 경도(lng)는 -180~180 범위여야 합니다."),
    "WEATHER_502_1": WalkError(502, "WEATHER_502_1", "외부 날씨 서비스 응답에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."),
    "WEATHER_503_1": WalkError(503, "WEATHER_503_1", "현재 날씨 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요."),
}

TODAY_ERRORS: Dict[str, WalkError] = {
    "WALK_TODAY_401_1": WalkError(401, "WALK_TODAY_401_1", "Authorization 헤더가 필요합니다."),
    "WALK_TODAY_401_2": WalkError(401, "WALK_TODAY_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "WALK_TODAY_404_1": WalkError(404, "WALK_TODAY_404_1", "해당 사용자를 찾을 수 없습니다."),
    "WALK_TODAY_404_2": WalkError(404, "WALK_TODAY_404_2", "요청하신 반려동물을 찾을 수 없습니다."),
    "WALK_TODAY_403_1": WalkError(403, "WALK_TODAY_403_1", "해당 반려동물의 산책 정보를 조회할 권한이 없습니다."),
    "WALK_TODAY_500_1": WalkError(500, "WALK_TODAY_500_1", "오늘 산책 현황을 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."),
}

WALK_ERRORS: Dict[str, WalkError] = {
    **PHOTO_ERRORS,
    **RANKING_ERRORS,
    **RECOMMEND_ERRORS,
    **SESSION_ERRORS,
    **SAVE_ERRORS,
    **NOTIFY_ERRORS,
    **WEATHER_ERRORS,
    **TODAY_ERRORS,
}

# 공통 에러 응답 생성기
def walk_error(code: str, path: str):
    err = WALK_ERRORS.get(code)
    if not err:
        return error_response(500, "WALK_PHOTO_500_2", "서버 내부 오류가 발생했습니다.", path)
    return error_response(err.status, err.code, err.reason, path)

RANKING_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "잘못된 요청",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/ranking", {
                    "WALK_RANKING_400_1": RANKING_ERRORS["WALK_RANKING_400_1"],
                    "WALK_RANKING_400_2": RANKING_ERRORS["WALK_RANKING_400_2"],
                })
            }
        },
    },
    401: {
        "model": ErrorResponse,
        "description": "인증 실패",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/ranking", {
                    "WALK_RANKING_401_1": RANKING_ERRORS["WALK_RANKING_401_1"],
                    "WALK_RANKING_401_2": RANKING_ERRORS["WALK_RANKING_401_2"],
                    "WALK_RANKING_401_3": RANKING_ERRORS["WALK_RANKING_401_3"],
                })
            }
        },
    },
    403: {
        "model": ErrorResponse,
        "description": "권한 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/ranking", {
                    "WALK_RANKING_403_1": RANKING_ERRORS["WALK_RANKING_403_1"],
                })
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "리소스 없음",
        "content": {
            "application/json": {
                "examples": _examples("/api/v1/walk/ranking", {
                    "WALK_RANKING_404_1": RANKING_ERRORS["WALK_RANKING_404_1"],
                    "WALK_RANKING_404_2": RANKING_ERRORS["WALK_RANKING_404_2"],
                })
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "서버 내부 오류",
    },
}
