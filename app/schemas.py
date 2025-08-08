from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str = Field(..., description="Stable identifier for the test case")
    title: str
    objective: Optional[str] = None
    preconditions: List[str] = Field(default_factory=list)
    steps: List[str]
    expected_result: str
    priority: str = Field("Medium", description="Priority: High | Medium | Low")
    type: str = Field("Functional", description="Type: Functional | Negative | Boundary | Performance | Security | Accessibility | Usability | Other")
    tags: List[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    summary: str
    source_summary: Optional[str] = None
    test_cases: List[TestCase]