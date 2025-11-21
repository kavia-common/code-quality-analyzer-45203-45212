from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


class Finding(BaseModel):
    """A single static analysis finding."""

    type: str = Field(..., description="Category or rule type, e.g., 'debug_statement', 'broad_except'")
    message: str = Field(..., description="Human-readable description of the finding")
    line: Optional[int] = Field(None, description="Line number where the issue was detected (1-based)")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity of the finding")


class Summary(BaseModel):
    """Aggregate counts by severity."""

    count_by_severity: Dict[str, int] = Field(
        ..., description="Counts of findings by severity, e.g., { 'low': 2, 'medium': 1, 'high': 0 }"
    )


class AnalyzeRequest(BaseModel):
    """Request payload for code analysis."""

    # PUBLIC_INTERFACE
    code: str = Field(..., description="Source code to analyze")
    language: Optional[str] = Field(
        default=None,
        description="Programming language hint (e.g., 'python', 'javascript'); case-insensitive",
    )


class AnalyzeResponse(BaseModel):
    """Response payload for analysis results."""

    # PUBLIC_INTERFACE
    findings: List[Finding] = Field(..., description="List of findings from analysis")
    summary: Summary = Field(..., description="Aggregated summary info")
