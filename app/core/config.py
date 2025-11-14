from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    FIREBASE_CREDENTIALS: str

    class Config:
        env_file = ".env"     # 프로젝트 루트에 있는 .env 자동 로딩

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy에서 사용할 MySQL 연결 URL 생성"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

# settings 객체를 import하면 바로 사용할 수 있음
settings = Settings()
