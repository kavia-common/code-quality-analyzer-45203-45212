from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .routers.analysis import router as analysis_router
from .routers.health import router as health_router
from .core.errors import register_exception_handlers

# Initialize FastAPI app with OpenAPI metadata and tags
app = FastAPI(
    title="Bug Detector Backend",
    description=(
        "A FastAPI service that analyzes user-submitted code to detect potential issues. "
        "Provides a simple rule-based static analysis for Python and JavaScript."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "Readiness and service metadata"},
        {"name": "analysis", "description": "Code analysis endpoints"},
    ],
)

# Basic, permissive CORS for integration (adjust origins in deployment if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to known frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized error handlers
register_exception_handlers(app)

# Routers
app.include_router(health_router)
app.include_router(analysis_router)


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["health"],
    summary="Health Check (root)",
    description="Simple readiness endpoint. Returns status ok.",
    response_model=dict,
    responses={200: {"description": "Service is healthy"}},
)
def root_health_check():
    """
    Root health check for compatibility with existing probes.

    Returns:
        JSON with status: "ok"
    """
    return JSONResponse({"status": "ok"})
