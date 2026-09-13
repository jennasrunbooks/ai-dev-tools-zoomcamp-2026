from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.errors import ApiException
from app.routers import waitlist
from app.store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.seed_demo_data()
    yield


app = FastAPI(title="WaitFlow API", version="1.0.0", lifespan=lifespan)

# Vite dev server origin (docs/spec.md 5.4) — frontend and backend run as
# separate dev servers locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiException)
def handle_api_exception(request: Request, exc: ApiException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(waitlist.router)
