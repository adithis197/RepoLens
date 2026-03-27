"""
Pydantic request/response models for the API.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AnalyzeRequest(BaseModel):
    repo_url: str
    token_budget: Optional[int] = 8000


class EvidenceEntry(BaseModel):
    node_id: str
    file: str
    start_line: int
    end_line: int


class AnalyzeResponse(BaseModel):
    repo_summary: str
    tech_stack: List[str]
    main_modules: List[str]
    architecture_mermaid: str
    flow_mermaid: List[str]
    evidence_map: List[EvidenceEntry]
