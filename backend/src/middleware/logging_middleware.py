import time
import uuid
import logging
from fastapi import Request

logger = logging.getLogger("http")

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={
                "request_id": request_id,
                "process_time": process_time,
            }
        )

        return response

    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)

        logger.error(
            f"{request.method} {request.url.path} -> ERROR",
            exc_info=True,
            extra={
                "request_id": request_id,
                "process_time": process_time,
            }
        )

        raise