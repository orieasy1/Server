from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db

from app.schemas.error_schema import ErrorResponse
from app.schemas.pets.pet_register_schema import PetRegisterRequest, PetRegisterResponse
from app.schemas.pets.pet_update_schema import PetUpdateRequest, PetUpdateResponse
from app.schemas.pets.pet_image_schema import PetImageResponse

from app.domains.pets.service.register_service import PetRegisterService
from app.domains.pets.service.pet_modify_service import PetModifyService
from app.domains.pets.repository.pet_repository import PetRepository
from app.core.error_handler import error_response

router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)

# ------------------------
# 0. 초대코드 중복 확인
# ------------------------
@router.get(
    "/check/{pet_search_id}",
    summary="아이디 중복 확인",
    description="반려동물 아이디가 이미 사용 중인지 확인합니다.",
    status_code=200,
    responses={
        200: {"description": "사용 가능한 아이디"},
        400: {"model": ErrorResponse, "description": "잘못된 형식"},
        409: {"model": ErrorResponse, "description": "이미 사용 중인 아이디"},
    },
)
def check_pet_search_id(
    pet_search_id: str,
    db: Session = Depends(get_db),
):
    """
    아이디 중복 확인
    
    - pet_search_id: 확인할 아이디 (8자리 영문+숫자)
    - 사용 가능하면 200, 중복이면 409 반환
    """
    import re
    
    # 형식 검증
    if not re.fullmatch(r"[A-Za-z0-9]{8}", pet_search_id):
        return error_response(400, "PET_400_5", "아이디는 영문+숫자 8자리여야 합니다.", f"/api/v1/pets/check/{pet_search_id}")
    
    pet_repo = PetRepository(db)
    if pet_repo.exists_pet_search_id(pet_search_id):
        return error_response(409, "PET_409_1", "이미 사용 중인 아이디입니다.", f"/api/v1/pets/check/{pet_search_id}")
    
    return {
        "success": True,
        "status": 200,
        "message": "사용 가능한 아이디입니다.",
        "pet_search_id": pet_search_id
    }

# ------------------------
# 1. 반려동물 등록
# ------------------------
@router.post(
    "",
    summary="반려동물 신규 등록",
    description=(
        "새로운 반려동물을 등록합니다. "
        "초대코드(pet_search_id)는 자동으로 생성되거나 제공된 값을 사용합니다."
    ),
    status_code=201,
    response_model=PetRegisterResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (필수 필드 누락, 형식 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "리소스를 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "중복된 초대코드"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def register_pet(
    request: Request,
    body: PetRegisterRequest,
    authorization: Optional[str] = Header(
        None, description="Firebase ID 토큰 (형식: Bearer <token>)"
    ),
    db: Session = Depends(get_db),
):
    """
    반려동물을 등록합니다.
    
    - 반려동물 기본 정보 (이름, 품종, 나이, 몸무게, 성별 등)를 입력받아 등록
    - 초대코드(pet_search_id)는 8자리 영문+숫자로 자동 생성 또는 제공된 값 사용
    - 등록한 사용자가 자동으로 owner로 설정됨
    """
    service = PetRegisterService(db)
    return service.register_pet(request, authorization, body)

# ------------------------
# 2. 반려동물 정보 부분 수정
# ------------------------
@router.patch(
    "/{pet_id}",
    summary="반려동물 세부 정보 부분 수정",
    description="반려동물의 정보를 부분적으로 수정합니다. 전송한 필드만 업데이트됩니다.",
    status_code=200,
    response_model=PetUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음 (소유자만 수정 가능)"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def update_pet(
    pet_id: int,
    request: Request,
    body: PetUpdateRequest,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물 정보를 부분 수정합니다.
    
    - pet_id: 수정할 반려동물 ID
    - body: 수정할 필드만 포함 (Optional 필드)
    - 권한: 해당 반려동물의 owner만 수정 가능
    - 정보 수정 시 추천 산책 정보도 자동으로 재계산될 수 있음
    """
    service = PetModifyService(db)
    return service.update_pet_detail(request, authorization, pet_id, body)

# ------------------------
# 3. 반려동물 이미지 URL 업데이트
# ------------------------
@router.post(
    "/{pet_id}/image",
    summary="반려동물 이미지 URL 업데이트",
    description="반려동물의 프로필 이미지 URL을 업데이트합니다.",
    status_code=200,
    response_model=PetImageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def update_pet_image(
    pet_id: int,
    request: Request,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물 프로필 이미지 URL을 업데이트합니다.
    
    - pet_id: 이미지를 업데이트할 반려동물 ID
    - 권한: 해당 반려동물의 owner만 수정 가능
    """
    service = PetModifyService(db)
    return service.update_pet_image(request, authorization, pet_id, body.image_url)


@router.delete(
    "/{pet_id}",
    summary="반려동물 삭제",
    description="반려동물을 삭제합니다. 관련된 모든 데이터(산책 기록, 사진 등)도 함께 삭제됩니다.",
    status_code=200,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음 (소유자만 삭제 가능)"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def delete_pet(
    pet_id: int,
    request: Request,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물을 삭제합니다.
    
    - pet_id: 삭제할 반려동물 ID
    - 권한: 해당 반려동물의 owner만 삭제 가능
    - 주의: 삭제 시 관련된 모든 데이터가 영구적으로 삭제됩니다
    """
    service = PetModifyService(db)
    return service.delete_pet(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
    )
