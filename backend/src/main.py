from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from src.middleware.logging_middleware import logging_middleware
from src.core.logging import setup_logging
from src.exception_handlers.base_exception import BaseAppException
from src.api.endpoints.auth_endpoint import auth_route
from src.api.endpoints.user_endpoint import user_route
from src.api.endpoints.category_endpoint import category_route
from src.api.endpoints.stream_endpoint import stream_route
from src.api.endpoints.donation_endpoint import donation_route
from src.core.config import settings

setup_logging()
logger = logging.getLogger("errors")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.debug,
    docs_url="/docs",
)

app.middleware("http")(logging_middleware)

@app.exception_handler(BaseAppException)
async def app_exception_handler(request, exc):
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={"path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route)
app.include_router(user_route)
app.include_router(category_route)
app.include_router(stream_route)
app.include_router(donation_route)


@app.get("/_info", status_code=200)
async def info():
    return {"app_name": settings.APP_NAME, "debug": settings.debug} 

