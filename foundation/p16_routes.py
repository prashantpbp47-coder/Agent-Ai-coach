"""P16 provider-neutral Priya reasoning router."""
import os
import time

import requests
from flask import Blueprint, jsonify, request

from .db import db
from .models_p16 import AIProviderCall
from .security import require_auth

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
    provider = str(data.get("provider") or os.getenv("AI_PROVIDER", "openai")).lower()
    fallback = str(data.get("fallback_provider") or os.getenv("AI_FALLBACK_PROVIDER", "deepseek")).lower()
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages_required"}), 400
    task_id = data.get("task_id")
    attempted = []
    for candidate in [provider, fallback]:
        if candidate in attempted:
            continue
        attempted.append(candidate)
        try:
            status, latency, model, text, usage, request_id, raw = _chat(candidate, messages, float(data.get("temperature", 0.2)))
            audit = AIProviderCall(task_id=task_id, provider=candidate, model=model, status="success" if status < 400 else "failed", http_status=status, latency_ms=latency, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"), provider_request_id=request_id, error_message=None if status < 400 else str(raw)[:2000])
            db.session.add(audit); db.session.commit()
            if status < 400 and text is not None:
                return jsonify({"provider": candidate, "model": model, "fallback_used": candidate != provider, "text": text, "usage": usage, "request_id": request_id})
        except Exception as exc:
            db.session.add(AIProviderCall(task_id=task_id, provider=candidate, model=os.getenv("OPENAI_MODEL" if candidate == "openai" else "DEEPSEEK_MODEL", "unknown"), status="error", error_message=str(exc)[:2000])); db.session.commit()
    return jsonify({"error": "all_ai_providers_failed", "attempted": attempted}), 503
