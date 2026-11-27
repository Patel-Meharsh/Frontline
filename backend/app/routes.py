from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
import triage
from backend.app.db import get_db
from backend.app.models import Message, MessageReview, TriageDecision
from backend.app.schemas import MessageCreate, MessageListResponse, MessageResponse, ReviewUpdate
from backend.app.triage_service import classify_message

router = APIRouter()

@router.post("/messages", response_model=MessageResponse, status_code=201, tags=["messages"])
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    # Commit the original first: a temporary Groq outage must not lose the customer message.
    message = Message(customer_name=payload.customer_name, customer_email=str(payload.customer_email),
                      message_text=payload.message_text, processing_status="pending")
    db.add(message)
    db.commit()
    db.refresh(message)
    try:
        decision, meta = classify_message(payload.message_text)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
        decision, meta = triage.fallback_decision(error), {
            "tokens": 0, "latency_sec": 0.0, "route": "processing_fallback", "error": error
        }
    db.add(TriageDecision(
        message_id=message.id, category=decision["category"], priority=decision["priority"],
        summary=decision["summary"], suggested_action=decision["suggested_action"],
        needs_human=decision["needs_human"], confidence=decision["confidence"],
        model_name=triage.MODEL, tokens_used=int(meta.get("tokens", 0) or 0),
        latency_sec=float(meta.get("latency_sec", 0) or 0),
        processing_route=str(meta.get("route", "unknown")), error=meta.get("error"),
    ))
    message.processing_status = "failed" if meta.get("error") else "processed"
    db.commit()
    return db.execute(select(Message).options(joinedload(Message.decision)).where(Message.id == message.id)).unique().scalar_one()

@router.get("/messages", response_model=MessageListResponse, tags=["messages"])
def list_messages(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                  status: str | None = Query(None, pattern="^(new|in_review|resolved)$"),
                  db: Session = Depends(get_db)):
    query = select(Message).options(joinedload(Message.decision)).order_by(Message.created_at.desc())
    count = select(func.count(Message.id))
    if status:
        query, count = query.where(Message.review_status == status), count.where(Message.review_status == status)
    items = db.execute(query.limit(limit).offset(offset)).unique().scalars().all()
    return {"items": items, "total": db.scalar(count) or 0, "limit": limit, "offset": offset}

@router.get("/messages/{message_id}", response_model=MessageResponse, tags=["messages"])
def get_message(message_id: int, db: Session = Depends(get_db)):
    item = db.execute(select(Message).options(joinedload(Message.decision)).where(Message.id == message_id)).unique().scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return item

@router.patch("/messages/{message_id}/review", response_model=MessageResponse, tags=["reviews"])
def update_review(message_id: int, payload: ReviewUpdate, db: Session = Depends(get_db)):
    item = db.get(Message, message_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Message not found")
    item.review_status = payload.status
    db.add(MessageReview(message_id=item.id, status=payload.status,
                         reviewed_by=payload.reviewed_by, notes=payload.notes))
    db.commit()
    return get_message(message_id, db)

@router.get("/dashboard/stats", tags=["dashboard"])
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Message.id))) or 0
    new = db.scalar(select(func.count(Message.id)).where(Message.review_status == "new")) or 0
    resolved = db.scalar(select(func.count(Message.id)).where(Message.review_status == "resolved")) or 0
    needs_human = db.scalar(select(func.count(TriageDecision.id)).where(TriageDecision.needs_human.is_(True))) or 0
    priorities = db.execute(select(TriageDecision.priority, func.count(TriageDecision.id)).group_by(TriageDecision.priority)).all()
    categories = db.execute(select(TriageDecision.category, func.count(TriageDecision.id)).group_by(TriageDecision.category)).all()
    return {"total_messages": total, "new_messages": new, "resolved_messages": resolved,
            "needs_human": needs_human, "priority_breakdown": dict(priorities),
            "category_breakdown": dict(categories)}
