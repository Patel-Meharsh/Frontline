from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MessageCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    customer_email: EmailStr
    message_text: str = Field(min_length=1, max_length=20_000)
    model_config = ConfigDict(str_strip_whitespace=True)


class CustomerMessageReceipt(BaseModel):
    id: int
    processing_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StaffLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class StaffResponse(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    staff: StaffResponse


class DecisionResponse(BaseModel):
    id: int
    message_id: int
    category: str
    priority: str
    summary: str
    suggested_action: str
    needs_human: bool
    confidence: float
    model_name: str
    tokens_used: int
    latency_sec: float
    processing_route: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: EmailStr
    message_text: str
    processing_status: str
    review_status: str
    created_at: datetime
    decision: DecisionResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int


class ReviewUpdate(BaseModel):
    status: Literal["new", "in_review", "resolved"]
    notes: str | None = Field(default=None, max_length=4000)
