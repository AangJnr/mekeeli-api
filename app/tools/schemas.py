from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    reason: str
    danger: str = "low"
