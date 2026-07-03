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

# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-g8swuy.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=[
        "X-Request-ID",
        "X-Client-Id",
        "Content-Type",
    ],
    expose_headers=[
        "X-Request-ID",
    ],
)
# -----------------------------
# Rate limiter storage
# -----------------------------
clients = defaultdict(deque)



@app.middleware("http")
async def middleware(request: Request, call_next):

    # Don't rate-limit CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    # Rest of your code...

    # -----------------------------
    # Rate Limiting
    # -----------------------------
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

    # -----------------------------
    # Request Context
    # -----------------------------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Echo request id back in header
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }