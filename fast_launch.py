"""PartnersHub AI fast-launch layer.

Additive layer for the existing Flask app. It focuses on the actual Phase-1
business goal: agent activity, WhatsApp nurturing, new-agent lead capture,
PBPartners quotation hand-off, and AI-written follow-up messages.

Run with: gunicorn fast_launch:application
"""

import os
from datetime import datetime, date

import requests
from flask import request, jsonify, redirect

from app import app, AGENTS

PBPARTNERS_URL = os.getenv("PBPARTNERS_URL", "https://www.pbpartners.com/")
FAST_LAUNCH_KEY = os.getenv("FAST_LAUNCH_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY", "")
INTERAKT_URL = "https://api.interakt.ai/v1/public/message/"


def _authorized():
    if not FAST_LAUNCH_KEY:
        return False
    supplied = request.headers.get("X-API-Key") or request.args.get("key", "")
    return supplied == FAST_LAUNCH_KEY


def _phone(value):
    value = str(value or "").strip()
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


def _interakt_template(name, phone, language="marathi"):
    """Send an approved WhatsApp template for proactive/outside-24h contact."""
    if not INTERAKT_API_KEY:
        return {"status": "failed", "error": "INTERAKT_API_KEY not configured"}

    clean_phone = _phone(phone)
    template_name = (
        os.getenv("INTERAKT_TEMPLATE_MARATHI", "daily_motor_support_marathi")
        if language.lower().startswith("mar")
        else os.getenv("INTERAKT_TEMPLATE_HINDI", "daily_motor_support_hindi")
    )
    language_code = "mr" if language.lower().startswith("mar") else "hi"

    payload = {
        "countryCode": "+91",
        "phoneNumber": clean_phone,
        "type": "Template",
        "template": {"name": template_name, "languageCode": language_code},
    }
    try:
        r = requests.post(
            INTERAKT_URL,
            json=payload,
            headers={
                "Authorization": f"Basic {INTERAKT_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        try:
            body = r.json()
        except Exception:
            body = {"text": r.text[:500]}
        return {
            "name": name,
            "phone": clean_phone,
            "template": template_name,
            "language": language_code,
            "status": "sent" if r.status_code in (200, 201) else "failed",
            "status_code": r.status_code,
            "response": body,
        }
    except Exception as exc:
        return {"name": name, "phone": clean_phone, "status": "failed", "error": str(exc)}


def _ai_message(quote_text, customer_name="Customer", language="marathi"):
    """Turn the agent's PBPartners quotation text into a safe follow-up."""
    if not OPENAI_API_KEY:
        return _fallback_message(customer_name, language)

    prompt = f"""Create a short WhatsApp-ready insurance quotation follow-up.
Language: {language}. Customer: {customer_name}.
The quotation was generated on PBPartners.com by the agent. Do not invent
premium, coverage, insurer, IDV, discount, payment link or policy details.
Use only the supplied quotation text. Be polite and sales-focused. End with
one clear call-to-action. Do not claim Priya issued the policy.

Quotation text:
{quote_text[:8000]}
"""
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": "You are Priya AI, a professional insurance sales assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 300,
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_message(customer_name, language)


def _fallback_message(customer_name, language):
    lang = language.lower()
    if lang.startswith("mar"):
        return (f"नमस्कार {customer_name} जी 🙏\n\nआपल्या वाहनाचा insurance quotation PBPartners वरून तयार करण्यात आला आहे.\n"
                "कृपया quotation पाहून policy पुढे करायची असल्यास मला कळवा.\n\nधन्यवाद – Priya AI")
    if lang.startswith("hin"):
        return (f"नमस्ते {customer_name} जी 🙏\n\nआपके वाहन का insurance quotation PBPartners पर तैयार किया गया है।\n"
                "कृपया quotation देखकर policy आगे बढ़ानी हो तो बताइए।\n\nधन्यवाद – Priya AI")
    return (f"Hello {customer_name} ji 👋\n\nYour motor insurance quotation has been generated on PBPartners.\n"
            "Please review it and let me know if you want to proceed.\n\n– Priya AI")


@app.get("/pbpartners")
def pbpartners_redirect():
    return redirect(PBPARTNERS_URL, code=302)


@app.get("/api/fast-health")
def fast_health():
    return jsonify({
        "status": "ok",
        "service": "PartnersHub AI fast launch",
        "date": str(date.today()),
        "agents_loaded": len(AGENTS),
        "interakt_configured": bool(INTERAKT_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "pbpartners_url": PBPARTNERS_URL,
    })


@app.post("/api/lead")
def capture_lead():
    data = request.get_json(silent=True) or {}
    missing = [x for x in ("name", "phone") if not str(data.get(x, "")).strip()]
    if missing:
        return jsonify({"ok": False, "missing": missing}), 400

    lead = {
        "name": str(data.get("name"))[:120],
        "phone": _phone(data.get("phone")),
        "city": str(data.get("city", ""))[:80],
        "source": str(data.get("source", "partnershub"))[:80],
        "interest": str(data.get("interest", "agent"))[:50],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    app.config.setdefault("FAST_LEADS", []).append(lead)
    return jsonify({"ok": True, "lead": lead})


@app.get("/api/leads")
def list_leads():
    if not _authorized():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"count": len(app.config.get("FAST_LEADS", [])), "leads": app.config.get("FAST_LEADS", [])})


@app.post("/api/new-agent")
def new_agent_lead():
    data = request.get_json(silent=True) or {}
    data["interest"] = "new_agent"
    data["source"] = data.get("source", "PartnersHub AI")
    missing = [x for x in ("name", "phone") if not str(data.get(x, "")).strip()]
    if missing:
        return jsonify({"ok": False, "missing": missing}), 400
    lead = {
        "name": str(data.get("name"))[:120],
        "phone": _phone(data.get("phone")),
        "city": str(data.get("city", ""))[:80],
        "source": str(data.get("source"))[:80],
        "interest": "new_agent",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    app.config.setdefault("FAST_LEADS", []).append(lead)
    return jsonify({"ok": True, "lead": lead})


@app.post("/api/quote-message")
def quote_message_api():
    data = request.get_json(silent=True) or {}
    quote_text = str(data.get("quote_text", "")).strip()
    if not quote_text:
        return jsonify({"ok": False, "error": "quote_text is required"}), 400
    customer = str(data.get("customer_name", "Customer"))[:120]
    language = str(data.get("language", "marathi"))[:20]
    return jsonify({
        "ok": True,
        "message": _ai_message(quote_text, customer, language),
        "pbpartners_url": PBPARTNERS_URL,
    })


@app.post("/api/daily-nurture")
def daily_nurture():
    """Send one approved Interakt template to a controlled batch.

    Call this endpoint from Hostinger cron in batches (normally 25). This is
    deliberately external-cron driven so a web-process restart cannot lose a
    scheduled job.
    """
    if not _authorized():
        return jsonify({"error": "Unauthorized"}), 401
    if not INTERAKT_API_KEY:
        return jsonify({"error": "INTERAKT_API_KEY is not configured"}), 503

    data = request.get_json(silent=True) or {}
    batch_size = max(1, min(int(data.get("batch_size", 25)), 50))
    offset = max(0, int(data.get("offset", 0)))
    language = str(data.get("language", "marathi")).lower()

    try:
        # Existing app already knows how to read the Google Sheet.
        from app import fetch_agents_from_sheet
        agents = fetch_agents_from_sheet()
    except Exception:
        agents = []

    if not agents:
        agents = [{"name": a["name"], "phone": a["phone"], "language": language, "ip_code": a["agent_id"]} for a in AGENTS]

    batch = agents[offset:offset + batch_size]
    results = [_interakt_template(a["name"], a["phone"], a.get("language", language) or language) for a in batch]
    sent = sum(1 for x in results if x.get("status") == "sent")
    return jsonify({
        "ok": True,
        "offset": offset,
        "batch_size": batch_size,
        "next_offset": offset + len(batch) if batch else None,
        "total_source_agents": len(agents),
        "sent": sent,
        "failed": len(results) - sent,
        "results": results,
    })


@app.get("/sales")
def sales_dashboard():
    target = int(os.getenv("DAILY_TARGET", "500000"))
    return f'''<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>PartnersHub AI — Sales Command</title><style>body{{font-family:Arial;background:#07111f;color:#fff;max-width:900px;margin:auto;padding:18px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.card{{background:#111d2e;border:1px solid #26364d;border-radius:16px;padding:18px}}.big{{font-size:30px;font-weight:800}}.btn{{display:inline-block;padding:12px 16px;border-radius:10px;background:#ff6b1a;color:#fff;text-decoration:none;margin:5px 5px 0 0}}small{{color:#9fb0c4}}</style></head><body><h1>🤖 Priya AI — Sales Command</h1><p><small>Daily business target: ₹{target:,}</small></p><div class="grid"><div class="card"><small>Agents loaded</small><div class="big">{len(AGENTS)}</div></div><div class="card"><small>PBPartners quotation</small><div class="big">LIVE LINK</div></div><div class="card"><small>Daily nurture</small><div class="big">25 / batch</div></div><div class="card"><small>New agent leads</small><div class="big">ACTIVE</div></div></div><p><a class="btn" href="/pbpartners">Open PBPartners</a><a class="btn" href="/agents">Agent Panel</a><a class="btn" href="/marketing-page">Find New Agents</a></p><p><small>Quotation is generated on PBPartners. Priya AI prepares the follow-up/customer message from the quotation data supplied by the agent.</small></p></body></html>'''


application = app
