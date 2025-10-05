from __future__ import annotations
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from utils.config import config

# State definition
class KBHit(BaseModel):
    retriever: str
    summary: str

class KBResult(BaseModel):
    retrieved_sources: List[KBHit] = Field(default_factory=list)
    consolidated_context: str = ""

class ActionProposal(BaseModel):
    action: str 
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = 0.0
    rationale: str = ""
    approved: Optional[bool] = None 

class TicketMeta(BaseModel):
    source: Literal["email", "chat", "web", "api", "cli"] = "email"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_id: Optional[str] = None
    locale: Optional[str] = None

class TicketState(BaseModel):
    # Input
    ticket_text: str
    meta: TicketMeta = Field(default_factory=TicketMeta)

    # Derived
    language: str = Field(default_factory=lambda: config.default_language)
    category: Literal['billing', 'technical', 'account', 'product', 'feedback', 'orders', 'compliance', 'general'] = Field(default_factory=lambda: config.default_category)
    category_conf: float = 0.0
    urgency: Literal['low', 'medium', 'high', 'critical'] = Field(default_factory=lambda: config.default_urgency)
    urgency_conf: float = 0.0

    kb_result: KBResult = Field(default_factory=KBResult)

    reply_draft: str = ""
    reply_conf: Optional[float] = 0.0

    actions: List[ActionProposal] = Field(default_factory=list)

    # Human-in-the-loop
    needs_review: bool = False
    human_feedback: Optional[str] = None  # guidance for redraft
    redraft_count: int = 0

    # Execution & results
    posted: bool = False
    escalated: bool = False

    # Control & diagnostics
    retries: Dict[str, int] = Field(default_factory=dict)  # per-node retry counts
    errors: List[str] = Field(default_factory=list)