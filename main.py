from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
from uuid import uuid4
import time

EMAIL = "23f1002228@ds.study.iitm.ac.in"

RATE_LIMIT = 9
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-g8swuy.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = defaultdict(deque)


@app.middleware("http")
async def middleware(request: Request, call_next):
    # -------- Rate Limiting --------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    bucket = clients[client_id]

    while bucket and bucket[0] <= now - WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    bucket.append(now)

    # -------- Request Context --------
    request_id = request.headers.get("X-Request-ID")

    if request_id is None:
        request_id = str(uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # IMPORTANT: Always echo it back
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }