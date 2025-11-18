from fastapi import FastAPI
from app.domains.auth.router.auth_router import router as auth_router
from app.domains.pets.router.register_router import router as pet_register_router
from app.domains.pets.router.share_request_router import router as pet_share_router
from app.domains.pets.router.my_pets_router import router as my_pets_router
from app.domains.walk.router.recommendation_router import router as walk_recommendation_router
from app.domains.record.router.walk_router import router as record_walk_router
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
            {"name": "Pet", "description": "반려동물 등록/조회/수정/삭제 API"},
            {"name": "Walk", "description": "산책 기록 API"},
            {"name": "Family", "description": "가족 그룹 관리 API"},
        ]
    )

    # 🟢 라우터 등록
    app.include_router(auth_router)

    # Pets APIs
    app.include_router(pet_register_router)
    app.include_router(pet_share_router)
    app.include_router(my_pets_router)

    # Walk Recommendation/Domain API
    app.include_router(walk_recommendation_router)

    # Record APIs
    app.include_router(record_walk_router)

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
        title="TakeAPaw API",
        version="1.0.0",
        description="반려동물 관리 서비스 TakeAPaw API 문서",
        routes=app.routes,
    )

    # 🔥 Swagger에 BearerAuth 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # 🔥 모든 API에 BearerAuth 기본 적용
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi    