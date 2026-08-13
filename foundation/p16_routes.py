"""P16 provider-neutral Priya reasoning router."""
import json
import os
import time
from datetime import datetime, timezone

import requests
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent
from .models_p14 import AgentTargetPlan, UserAgentLink
from .models_p15 import AIKnowledgeSource, AITask
from .models_p16 import AIProviderCall
from .security import current_user, require_auth

bp = Blueprint("p16_ai", __name__, url_prefix="/api/p16")


def _provider_config(provider):
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "https://api.openai.com/v1/chat/completions"
    if provider == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY"), os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"), "https://api.deepseek.com/chat/completions"
    raise ValueError("unsupported_provider")


def _chat(provider, messages, temperature=0.2):
    api_key, model, url = _provider_config(provider)
    if not api_key:
        raise RuntimeError(f"{provider}_api_key_missing")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}
    started = time.perf_counter()
    response = requests.post(url, headers=headers, json=payload, timeout=int(os.getenv("AI_TIMEOUT_SECONDS", "30")))
    latency = int((time.perf_counter() - started) * 1000)
    data = response.json() if response.content else {}
    text = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content")
    usage = data.get("usage") or {}
    return response.status_code, latency, model, text, usage, data.get("id"), data


def _safe_context(plan, agent, knowledge):
    # The RM aggregate target is intentionally excluded from Agent-facing AI context.
    return {
        "agent_name": agent.name,
        "agent_target": plan.target_amount,
        "agent_completion": plan.completion_amount,
        "target_gap": max(plan.target_amount - plan.completion_amount, 0),
        "tier": plan.tier,
        "club": plan.club_name,
        "approved_knowledge": knowledge,
    }


def _provider_chain(preferred=None, fallback=None):
    first = (preferred or os.getenv("AI_PROVIDER", "openai")).lower()
    second = (fallback or os.getenv("AI_FALLBACK_PROVIDER", "deepseek")).lower()
    return [first] if first == second else [first, second]


@bp.get("/health")
@require_auth
def health():
    return jsonify({
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "deepseek_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "fallback": os.getenv("AI_FALLBACK_PROVIDER", "deepseek"),
    })


@bp.post("/reason")
@require_auth
def reason():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages_required"}), 400
    task_id = data.get("task_id")
    preferred = str(data.get("provider") or os.getenv("AI_PROVIDER", "openai")).lower()
    attempted = []
    for candidate in _provider_chain(preferred, data.get("fallback_provider")):
        attempted.append(candidate)
        try:
            status, latency, model, text, usage, request_id, raw = _chat(candidate, messages, float(data.get("temperature", 0.2)))
            db.session.add(AIProviderCall(task_id=task_id, provider=candidate, model=model, status="success" if status < 400 else "failed", http_status=status, latency_ms=latency, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"), provider_request_id=request_id, error_message=None if status < 400 else str(raw)[:2000]))
            db.session.commit()
            if status < 400 and text is not None:
                return jsonify({"provider": candidate, "model": model, "fallback_used": candidate != preferred, "text": text, "usage": usage, "request_id": request_id})
        except Exception as exc:
            db.session.add(AIProviderCall(task_id=task_id, provider=candidate, model=os.getenv("OPENAI_MODEL" if candidate == "openai" else "DEEPSEEK_MODEL", "unknown"), status="error", error_message=str(exc)[:2000]))
            db.session.commit()
    return jsonify({"error": "all_ai_providers_failed", "attempted": attempted}), 503


@bp.post("/priya/agent-coach")
@require_auth
def priya_agent_coach():
    """Create a grounded agent-facing coaching task using only the agent's own target context."""
    user = current_user()
    agent_id = request.args.get("agent_id")
    if not agent_id:
        return jsonify({"error": "agent_id_required"}), 400

    is_rm_or_admin = any(role.name in {"ADMIN", "RM"} for role in user.roles)
    if not is_rm_or_admin:
        link = db.session.execute(select(UserAgentLink).filter_by(user_id=user.id, agent_id=agent_id)).scalar_one_or_none()
        if not link:
            return jsonify({"error": "forbidden"}), 403

    today = datetime.now(timezone.utc).date()
    plan = db.session.execute(select(AgentTargetPlan).where(AgentTargetPlan.agent_id == agent_id, AgentTargetPlan.target_date == today).limit(1)).scalar_one_or_none()
    agent = db.session.get(Agent, agent_id)
    if not plan or not agent:
        return jsonify({"error": "today_target_not_found"}), 404

    sources = db.session.execute(select(AIKnowledgeSource).where(AIKnowledgeSource.status == "active").limit(5)).scalars().all()
    context = _safe_context(plan, agent, [{"title": s.title, "content": s.content[:1200], "source_uri": s.source_uri} for s in sources])
    messages = [
        {"role": "system", "content": "You are Priya, an insurance-agent growth coach. Use only supplied facts and approved knowledge. Never expose RM aggregate targets and never invent insurer pricing. Return JSON with action, reason, message, follow_up_hours."},
        {"role": "user", "content": "Prepare today's individualized coaching and WhatsApp-ready message. Context: " + json.dumps(context, ensure_ascii=False)},
    ]

    task = AITask(skill_code="agent_coach", task_type="agent_daily_coach", agent_id=agent_id, input_json=json.dumps(context, ensure_ascii=False), status="queued", created_by=user.id)
    db.session.add(task)
    db.session.flush()

    attempted = []
    preferred = request.args.get("provider")
    fallback = request.args.get("fallback_provider")
    for candidate in _provider_chain(preferred, fallback):
        attempted.append(candidate)
        try:
            status, latency, model, text, usage, request_id, raw = _chat(candidate, messages)
            db.session.add(AIProviderCall(task_id=task.id, provider=candidate, model=model, status="success" if status < 400 else "failed", http_status=status, latency_ms=latency, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"), provider_request_id=request_id, error_message=None if status < 400 else str(raw)[:2000]))
            if status < 400 and text:
                task.status = "completed"
                task.output_json = json.dumps({"text": text, "provider": candidate, "model": model}, ensure_ascii=False)
                db.session.commit()
                return jsonify({"task_id": task.id, "provider": candidate, "fallback_used": candidate != (preferred or os.getenv("AI_PROVIDER", "openai")), "text": text})
        except Exception as exc:
            db.session.add(AIProviderCall(task_id=task.id, provider=candidate, model=os.getenv("OPENAI_MODEL" if candidate == "openai" else "DEEPSEEK_MODEL", "unknown"), status="error", error_message=str(exc)[:2000]))

    task.status = "failed"
    task.output_json = json.dumps({"error": "all_ai_providers_failed", "attempted": attempted})
    db.session.commit()
    return jsonify({"task_id": task.id, "error": "all_ai_providers_failed", "attempted": attempted}), 503
