from fastapi import FastAPI
from app.domains.auth.router.auth_router import router as auth_router
from app.domains.pets.router.register_router import router as pet_register_router
from app.domains.pets.router.share_request_router import router as pet_share_router
from app.domains.pets.router.my_pets_router import router as my_pets_router
from app.domains.walk.router.recommendation_router import router as walk_recommendation_router
from app.domains.walk.router.walk_save_router import router as walk_save_router
from app.domains.walk.router.ranking_router import router as ranking_router
from app.domains.record.router.walk_router import router as record_walk_router
from app.domains.users.router.family_member_router import router as family_member_router
from app.domains.users.router.users_router import router as user_router
from app.domains.notifications.router.notification_router import router as notifications_router
from app.domains.notifications.router.health_router import router as health_router
from app.domains.notifications.router.weather_router import router as weather_router
from app.domains.weather.router.weather_router import router as current_weather_router


from fastapi.openapi.utils import get_openapi

def create_app() -> FastAPI:
    app = FastAPI(
        title="Take a Paw API 🐾",
        version="1.0.0",
        description="Backend API for Take a Paw mobile app",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {"name": "Auth", "description": "Firebase 인증 관련 API"},
            {"name": "Users", "description": "사용자 정보 조회/수정 API"},
            {"name": "Pet", "description": "반려동물 등록/조회/수정/삭제 API"},
            {"name": "Walk", "description": "산책 기록 API"},
            {"name": "Family", "description": "가족 그룹 관리 API"},
        ]
    )

    # 🟢 라우터 등록
    app.include_router(auth_router)

    app.include_router(user_router)
    app.include_router(family_member_router)

    # Pets APIs
    app.include_router(pet_register_router)
    app.include_router(pet_share_router)
    app.include_router(my_pets_router)

    # Walk Recommendation/Domain API
    app.include_router(walk_recommendation_router)
    app.include_router(walk_save_router)
    app.include_router(ranking_router)

    # Record APIs
    app.include_router(record_walk_router)

    # Notifications
    app.include_router(notifications_router)
    app.include_router(health_router)
    app.include_router(weather_router)
    
    # Weather API
    app.include_router(current_weather_router)


    @app.get("/")
    def root():
        return {"message": "🐾 Take a Paw API is running successfully"}

    return app


app = create_app()

# 🟢 로컬 실행용 entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Take a Paw API 🐾",
        version="1.0.0",
        description="""
        ## Take a Paw API
        
        반려동물 산책 관리 애플리케이션을 위한 백엔드 API입니다.
        
        ### 주요 기능
        - 🔐 Firebase 기반 사용자 인증
        - 🐕 반려동물 등록 및 관리
        - 🚶 산책 기록 및 추적
        - 📊 활동 통계 및 시각화
        - 📸 산책 사진 관리
        - 👨‍👩‍👧‍👦 가족 구성원 공유
        
        ### 인증
        대부분의 API는 Firebase ID 토큰을 Authorization 헤더에 포함하여 요청해야 합니다.
        일부 API(예: 날씨 조회)는 선택적 인증을 지원합니다.
        """,
        routes=app.routes,
    )

    # 🔥 Swagger에 BearerAuth 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Firebase ID 토큰을 Bearer 형식으로 전달하세요. 예: Bearer <token>"
        }
    }

    # 🔥 모든 경로에 BearerAuth를 선택적으로 적용 (각 엔드포인트에서 개별적으로 설정 가능)
    # 전역 보안은 설정하지 않고, 각 엔드포인트에서 필요시 security 파라미터로 설정

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi    