from fastapi import FastAPI
from app.domains.auth.router.auth_router import router as auth_router
from app.domains.pets.router.register_router import router as pet_register_router
from app.domains.pets.router.share_request_router import router as pet_share_router
from app.domains.pets.router.my_pets_router import router as my_pets_router
from app.domains.walk.router.recommendation_router import router as walk_recommendation_router
from app.domains.record.router.walk_router import router as record_walk_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Take a Paw API 🐾",
        version="1.0.0",
        description="Backend API for Take a Paw mobile app"
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
