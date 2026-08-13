"""P17 Priya-to-messaging automation bridge."""
import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog
from .models_p7 import AgentDailyMessage
from .models_p16 import AIProviderCall
from .p16_routes import _chat, _provider_chain
from .security import current_user, require_role

bp = Blueprint("p17_priya_messaging", __name__, url_prefix="/api/p17")


def now():
    return datetime.now(timezone.utc)


def _extract_message(text: str) -> str:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("text") or text).strip()
    except Exception:
        pass
    return text.strip()


@bp.post("/agent-coach/queue")
@require_role("RM", "ADMIN")
def queue_agent_coach():
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent_id")
    if not agent_id:
        return jsonify({"error": "agent_id_required"}), 400
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"error": "agent_not_found"}), 404

    # Reuse P16 reasoning so one source of truth controls Priya's content.
    from .p16_routes import _safe_context
    from .models_p14 import AgentTargetPlan
    from .models_p15 import AIKnowledgeSource
    plan = db.session.execute(select(AgentTargetPlan).where(AgentTargetPlan.agent_id == agent_id, AgentTargetPlan.target_date == now().date()).limit(1)).scalar_one_or_none()
    if not plan:
        return jsonify({"error": "today_target_not_found"}), 404
    sources = db.session.execute(select(AIKnowledgeSource).where(AIKnowledgeSource.status == "active").limit(5)).scalars().all()
    context = _safe_context(plan, agent, [{"title": s.title, "content": s.content[:1200], "source_uri": s.source_uri} for s in sources])
    messages = [
        {"role": "system", "content": "You are Priya, an insurance-agent growth coach. Use only supplied facts and approved knowledge. Never reveal RM aggregate targets or invent insurer pricing. Return JSON with keys action, reason, message, follow_up_hours."},
        {"role": "user", "content": "Create today's concise agent WhatsApp coaching message. Context: " + json.dumps(context, ensure_ascii=False)},
    ]
    preferred = data.get("provider")
    attempted = []
    output = None
    selected = None
    task_id = None
    for candidate in _provider_chain(preferred, data.get("fallback_provider")):
        attempted.append(candidate)
        try:
            status, latency, model, text, usage, request_id, raw = _chat(candidate, messages)
            db.session.add(AIProviderCall(task_id=task_id, provider=candidate, model=model, status="success" if status < 400 else "failed", http_status=status, latency_ms=latency, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"), provider_request_id=request_id, error_message=None if status < 400 else str(raw)[:2000]))
            if status < 400 and text:
                output = text; selected = candidate; break
        except Exception as exc:
            db.session.add(AIProviderCall(task_id=task_id, provider=candidate, model="unknown", status="error", error_message=str(exc)[:2000]))
    if not output:
        db.session.rollback()
        return jsonify({"error": "all_ai_providers_failed", "attempted": attempted}), 503

    body = _extract_message(output)
    dedupe = f"p17:agent-coach:{agent_id}:{now().date().isoformat()}"
    existing = db.session.execute(select(AgentDailyMessage).filter_by(dedupe_key=dedupe)).scalar_one_or_none()
    if existing:
        db.session.commit()
        return jsonify({"message_id": existing.id, "status": existing.status, "deduplicated": True, "provider": selected})

    rm_id = plan.rm_id
    row = AgentDailyMessage(rm_id=rm_id, agent_id=agent_id, message_date=now().date(), channel="whatsapp", message_type="priya_agent_coach", body=body, status="queued", dedupe_key=dedupe)
    db.session.add(row)
    db.session.add(AuditLog(action="p17.priya.queue_agent_message", user_id=current_user().id, resource_type="agent_daily_message", resource_id=row.id, ip_address=request.remote_addr))
    db.session.commit()
    return jsonify({"message_id": row.id, "status": row.status, "provider": selected, "text": body})


@bp.post("/dispatch")
@require_role("RM", "ADMIN")
def dispatch():
    """Delegate actual delivery to P8; preserves consent, retries and provider status."""
    from .p8_routes import dispatch as p8_dispatch
    return p8_dispatch()
