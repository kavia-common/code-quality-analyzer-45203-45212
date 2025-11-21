from fastapi import APIRouter, HTTPException
from fastapi import status

from ..schemas.analysis import AnalyzeRequest, AnalyzeResponse
from ..services.analyzer import analyze_code

router = APIRouter(prefix="", tags=["analysis"])


# PUBLIC_INTERFACE
@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze submitted code",
    description="""
Submit code and get potential bug findings.

Example curl:
  curl -s -X POST http://localhost:3001/analyze \\
    -H 'Content-Type: application/json' \\
    -d '{"code":"print(\\"debug\\")\\n# TODO fix\\n","language":"python"}'
""",
    responses={
        200: {"description": "Analysis completed"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal processing error"},
    },
)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze user-submitted code using a lightweight static analysis pass.

    Args:
        request: AnalyzeRequest containing code and optional language.

    Returns:
        AnalyzeResponse with findings and summary.
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code must be a non-empty string.")

    try:
        findings, summary = analyze_code(request.code, request.language)
        return AnalyzeResponse(findings=findings, summary=summary)
    except HTTPException:
        # Re-raise controlled HTTP errors
        raise
    except Exception as exc:
        # Unexpected error path
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
