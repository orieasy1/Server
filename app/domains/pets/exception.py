from dataclasses import dataclass
from typing import Dict

from app.core.error_handler import error_response
from app.schemas.error_schema import ErrorResponse


@dataclass(frozen=True)
class PetError:
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


# 공통 에러 코드 정의
PET_ERRORS: Dict[str, PetError] = {
    # Register
    "PET_400_1": PetError(400, "PET_400_1", "반려동물 이름은 필수입니다."),
    "PET_400_2": PetError(400, "PET_400_2", "gender 값 오류."),
    "PET_400_5": PetError(400, "PET_400_5", "아이디는 영문+숫자 8자리여야 합니다."),
    "PET_401_1": PetError(401, "PET_401_1", "Authorization 헤더가 필요합니다."),
    "PET_401_2": PetError(401, "PET_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다."),
    "PET_409_1": PetError(409, "PET_409_1", "이미 사용 중인 pet_search_id입니다."),
    "PET_500_1": PetError(500, "PET_500_1", "반려동물 등록 중 오류."),
    "PET_500_2": PetError(500, "PET_500_2", "추천 산책 정보를 생성하는 중 오류."),
    "PET_500_3": PetError(500, "PET_500_3", "사용자 생성 중 오류가 발생했습니다."),

    # Update detail
    "PET_EDIT_401_1": PetError(401, "PET_EDIT_401_1", "Authorization 헤더가 필요합니다."),
    "PET_EDIT_401_2": PetError(401, "PET_EDIT_401_2", "Authorization 형식 오류"),
    "PET_EDIT_404_1": PetError(404, "PET_EDIT_404_1", "사용자를 찾을 수 없습니다."),
    "PET_EDIT_404_2": PetError(404, "PET_EDIT_404_2", "반려동물을 찾을 수 없습니다."),
    "PET_EDIT_403_1": PetError(403, "PET_EDIT_403_1", "펫의 주인만 수정가능합니다"),
    "PET_EDIT_400_1": PetError(400, "PET_EDIT_400_1", "수정할 항목이 없습니다."),
    "PET_EDIT_500_1": PetError(500, "PET_EDIT_500_1", "반려동물 정보를 수정하는 중 오류."),
    "PET_EDIT_500_2": PetError(500, "PET_EDIT_500_2", "추천 산책 정보 생성 실패"),

    # Update image
    "PET_IMG_401_1": PetError(401, "PET_IMG_401_1", "Authorization 헤더가 필요합니다."),
    "PET_IMG_401_2": PetError(401, "PET_IMG_401_2", "Authorization 형식 오류"),
    "PET_IMG_404_1": PetError(404, "PET_IMG_404_1", "사용자를 찾을 수 없습니다."),
    "PET_IMG_404_2": PetError(404, "PET_IMG_404_2", "반려동물을 찾을 수 없습니다."),
    "PET_IMG_403_1": PetError(403, "PET_IMG_403_1", "펫의 주인만 수정가능합니다"),
    "PET_IMG_500_2": PetError(500, "PET_IMG_500_2", "이미지 URL 저장 중 오류."),

    # Delete
    "PET_DELETE_401_1": PetError(401, "PET_DELETE_401_1", "Authorization 헤더가 필요합니다."),
    "PET_DELETE_401_2": PetError(401, "PET_DELETE_401_2", "Authorization 형식 오류"),
    "PET_DELETE_401_3": PetError(401, "PET_DELETE_401_3", "Firebase 토큰 검증 실패"),
    "PET_DELETE_404_1": PetError(404, "PET_DELETE_404_1", "사용자를 찾을 수 없습니다."),
    "PET_DELETE_404_2": PetError(404, "PET_DELETE_404_2", "반려동물을 찾을 수 없습니다."),
    "PET_DELETE_404_3": PetError(404, "PET_DELETE_404_3", "가족 구성원 정보를 찾을 수 없습니다."),
    "PET_DELETE_500_1": PetError(500, "PET_DELETE_500_1", "반려동물 삭제 중 오류 발생"),

    # Share request create
    "PET_SHARE_401_1": PetError(401, "PET_SHARE_401_1", "Authorization 헤더가 필요합니다."),
    "PET_SHARE_401_2": PetError(401, "PET_SHARE_401_2", "유효하지 않은 토큰입니다."),
    "PET_SHARE_404_2": PetError(404, "PET_SHARE_404_2", "해당 초대코드의 반려동물이 없습니다."),
    "PET_SHARE_409_1": PetError(409, "PET_SHARE_409_1", "이미 가족 구성원입니다."),
    "PET_SHARE_409_2": PetError(409, "PET_SHARE_409_2", "이미 처리 대기 중인 요청이 존재합니다."),
    "PET_SHARE_500_1": PetError(500, "PET_SHARE_500_1", "요청 생성 중 오류가 발생했습니다."),
    "PET_SHARE_500_2": PetError(500, "PET_SHARE_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다."),

    # Share approve
    "PET_SHARE_APPROVE_401_1": PetError(401, "PET_SHARE_APPROVE_401_1", "Authorization 필요"),
    "PET_SHARE_APPROVE_401_2": PetError(401, "PET_SHARE_APPROVE_401_2", "유효하지 않은 토큰입니다."),
    "PET_SHARE_APPROVE_404_1": PetError(404, "PET_SHARE_APPROVE_404_1", "사용자를 찾을 수 없습니다."),
    "PET_SHARE_APPROVE_400_1": PetError(400, "PET_SHARE_APPROVE_400_1", "status 필수"),
    "PET_SHARE_APPROVE_404_2": PetError(404, "PET_SHARE_APPROVE_404_2", "요청을 찾을 수 없습니다."),
    "PET_SHARE_APPROVE_403_1": PetError(403, "PET_SHARE_APPROVE_403_1", "owner 권한 없음"),
    "PET_SHARE_APPROVE_409_1": PetError(409, "PET_SHARE_APPROVE_409_1", "이미 처리됨"),
    "PET_SHARE_APPROVE_409_2": PetError(409, "PET_SHARE_APPROVE_409_2", "이미 가족 구성원입니다."),
    "PET_SHARE_APPROVE_500_1": PetError(500, "PET_SHARE_APPROVE_500_1", "처리 중 오류"),
}


def pet_error(code: str, path: str):
    err = PET_ERRORS.get(code)
    if not err:
        return error_response(500, "PET_500_1", "서버 내부 오류가 발생했습니다.", path)
    return error_response(err.status, err.code, err.reason, path)


def _examples(path: str, mapping: Dict[str, PetError]) -> Dict:
    return {
        code: {"value": err.to_dict(path)}
        for code, err in mapping.items()
    }


# Swagger responses
PET_CHECK_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 형식"},
    409: {"model": ErrorResponse, "description": "이미 사용 중인 아이디"},
}

PET_REGISTER_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    404: {"model": ErrorResponse, "description": "리소스를 찾을 수 없음"},
    409: {"model": ErrorResponse, "description": "중복된 초대코드"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

PET_UPDATE_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

PET_IMAGE_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}

PET_DELETE_RESPONSES = {
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    401: {"model": ErrorResponse, "description": "인증 실패"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 내부 오류"},
}
