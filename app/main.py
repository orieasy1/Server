from fastapi import FastAPI
from app.domains.auth.router.auth_router import router as auth_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Take a Paw API 🐾",
        version="1.0.0",
        description="Backend API for Take a Paw mobile app"
    )

    # 🟢 라우터 등록
    app.include_router(auth_router)

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
