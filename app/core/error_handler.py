from fastapi.responses import JSONResponse
from datetime import datetime
from app.schemas.error_schema import ErrorResponse

def error_response(status: int, code: str, reason: str, path: str) -> JSONResponse:

    error = ErrorResponse(
        success=False,
        status=status,
        code=code,
        reason=reason,
        timeStamp=datetime.utcnow().isoformat(),
        path=path
    )

    return JSONResponse(
        status_code=status,
        content=error.model_dump()
    )
