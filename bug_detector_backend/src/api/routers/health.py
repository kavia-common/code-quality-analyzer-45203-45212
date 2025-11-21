from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])


# PUBLIC_INTERFACE
@router.get(
    "/health",
    summary="Health Check",
    description="Readiness probe endpoint returning status ok.",
    response_model=dict,
)
def health():
    """Return health status for readiness probes."""
    return {"status": "ok"}


# PUBLIC_INTERFACE
@router.get(
    "/version",
    summary="Service Version",
    description="Returns the current service version and name.",
    response_model=dict,
)
def version():
    """Return simple service metadata."""
    return {"name": "bug-detector-backend", "version": "0.1.0"}
