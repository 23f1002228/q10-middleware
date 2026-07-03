from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
from collections import defaultdict, deque
import time

EMAIL = "23f1002228@ds.study.iitm.ac.in"

RATE_LIMIT = 9
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-g8swuy.example.com",
        # Add the exam page origin here if needed.
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = defaultdict(deque)

class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        client = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        bucket = clients[client]

        while bucket and bucket[0] <= now - WINDOW:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail":"Rate limit exceeded"}
            )

        bucket.append(now)

        request_id = request.headers.get("X-Request-ID")

        if request_id is None:
            request_id = str(uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestContextMiddleware)

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }