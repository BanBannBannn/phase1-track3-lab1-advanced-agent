from __future__ import annotations
from typing import Literal, Optional, TypedDict
from pydantic import BaseModel, Field

class ContextChunk(BaseModel):
    title: str
    text: str

class QAExample(BaseModel):
    qid: str
    difficulty: Literal["easy", "medium", "hard"]
    question: str
    gold_answer: str
    context: list[ContextChunk]

class JudgeResult(BaseModel):
    # Đảm bảo có 'score' và 'reason' vì AttemptTrace đang gọi judge.score và judge.reason
    score: int = Field(..., description="Điểm đánh giá chất lượng (ví dụ: 0 hoặc 1)")
    reason: str = Field(..., description="Lý do chi tiết (critique) giải thích tại sao đạt mức điểm này")
    is_perfect: bool = Field(default=False, description="Cờ đánh dấu câu trả lời đã hoàn hảo chưa")

class ReflectionEntry(BaseModel):
    attempt_id: int
    failure_reason: str = Field(default="", description="Lý do chi tiết (critique) giải thích tại sao đạt mức điểm này")
    lesson: str = Field(default="", description="Bài học rút ra từ lỗi sai (root cause)")
    strategy: str = Field(default="", description="Chiến thuật/hành động cụ thể cho lượt thử tiếp theo")
    
    # Optional: If you still want 'content', make it optional or give it a default value
    # so Pydantic doesn't crash if mock_runtime.py omits it.
    content: str = Field(default="", description="Toàn bộ nội dung trả về từ Reflector")
    
class AttemptTrace(BaseModel):
    attempt_id: int
    answer: str
    score: int
    reason: str
    reflection: Optional[ReflectionEntry] = None
    token_estimate: int = 0
    latency_ms: int = 0

class RunRecord(BaseModel):
    qid: str
    question: str
    gold_answer: str
    agent_type: Literal["react", "reflexion"]
    predicted_answer: str
    is_correct: bool
    attempts: int
    token_estimate: int
    latency_ms: int
    failure_mode: Literal["none", "entity_drift", "incomplete_multi_hop", "wrong_final_answer", "looping", "reflection_overfit"]
    reflections: list[ReflectionEntry] = Field(default_factory=list)
    traces: list[AttemptTrace] = Field(default_factory=list)

class ReportPayload(BaseModel):
    meta: dict
    summary: dict
    failure_modes: dict
    examples: list[dict]
    extensions: list[str]
    discussion: str

class ReflexionState(TypedDict):
    question: str
    context: list[str]
    trajectory: list[str]
    reflection_memory: list[str]
    attempt_count: int
    success: bool
    final_answer: str