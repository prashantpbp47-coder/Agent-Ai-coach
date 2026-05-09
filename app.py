"""
PRIYA AI v4.0 - Prashant Chandratre ji ki AI Sales Assistant
Clean deploy-ready code for Render
Outgoing calls: 9 AM - 8 PM only
"""

from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
import openai
import os
import json
import random
import requests
from datetime import datetime, date

app = Flask(__name__)

# ── ENVIRONMENT VARIABLES ─────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_API_KEY     = os.environ.get("TWILIO_API_KEY", "")
TWILIO_API_SECRET  = os.environ.get("TWILIO_API_SECRET", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "+917709446589")
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", "")
PRASHANT_NUMBER    = os.environ.get("PRASHANT_NUMBER", "+917709446589")
PRASHANT_WA        = os.environ.get("PRASHANT_WHATSAPP", "+917709446589")
UPLOAD_PASSWORD    = os.environ.get("UPLOAD_PASSWORD", "agentguru2024")
DAILY_TARGET       = int(os.environ.get("DAILY_TARGET", "300000"))
INTERAKT_KEY       = os.environ.get("INTERAKT_API_KEY", "")

openai.api_key = OPENAI_API_KEY

try:
    twilio_client = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
except Exception:
    twilio_client = None

# ── PRASHANT PROFILE ──────────────────────────────────────────
PRASHANT = {
    "name": "Prashant Dinkar Chandratre",
    "role": "IRM - PB Partners (Policybazaar)",
    "irm_code": "IRM169896",
    "phone": "7709446589",
    "wa": "wa.me/7709446589",
    "email": "prashantchandratre@pbpartners.com",
    "note": "PBPartners is a brand under Policybazaar Insurance Broker Pvt. Ltd."
}

# ── CALLING HOURS: 9 AM to 8 PM ──────────────────────────────
def is_calling_hours():
    h = datetime.now().hour
    return 9 <= h < 20  # 9:00 AM to 8:00 PM

# ── AGENT LIST (10 agents from your data) ────────────────────
AGENTS = [
    {"agent_id": "IP175831", "name": "BHAVSAR DHIRAJ ANIL",        "phone": "+918830819624", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP226792", "name": "SANDEEP ASHOK GAIKWAD",      "phone": "+918855858540", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP249200", "name": "Viraj Vaibhav Bhanage",      "phone": "+919823280440", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP249232", "name": "ANKUSH PANDHARINATH JAGTAP", "phone": "+918575757875", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP272307", "name": "MANISHA GOKUL WANKHEDE",     "phone": "+919762206575", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP293595", "name": "RATNA AMOL RAUT",            "phone": "+919011917669", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP251027", "name": "NIKITA AMEET MULEY",         "phone": "+918055181585", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP273040", "name": "RUGVED MOHAN KHADILKAR",     "phone": "+917276715028", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP182887", "name": "RUSHIKESH S AHIRRAO",        "phone": "+919372552917", "line": "Motor", "onboarding": "Done"},
    {"agent_id": "IP170917", "name": "JYOTI ROHIT NIRBHAVANE",     "phone": "+917020001759", "line": "Motor", "onboarding": "Done"},
]

# ── IN-MEMORY STATE ───────────────────────────────────────────
conversations = {}
active_leads  = {}
today_biz = {
    "date": str(date.today()),
    "total_premium": 0,
    "total_policies": 0,
    "target": DAILY_TARGET,
    "agents_called": [],
    "agent_data": {},
}

# ── HELPERS ───────────────────────────────────────────────────
def find_agent(phone):
    clean = phone.replace("+91", "").strip()[-10:]
    return next((a for a in AGENTS if a["phone"].replace("+91", "")[-10:] == clean), None)

def first_name(name):
    return name.split()[0].title()

def greeting():
    h = datetime.now().hour
    if h < 12:  return "Good morning"
    if h < 17:  return "Namaste"
    return "Good evening"

def send_whatsapp(phone, msg):
    if not phone:
        return False
    if not phone.startswith("+"):
        phone = "+91" + phone[-10:]
    # Try Interakt first
    if INTERAKT_KEY:
        try:
            r = requests.post(
                "https://api.interakt.ai/v1/public/message/",
                json={"fullPhoneNumber": phone, "callbackData": "priya",
                      "type": "Text", "data": {"message": msg}},
                headers={"Authorization": f"Basic {INTERAKT_KEY}",
                         "Content-Type": "application/json"},
                timeout=10
            )
            if r.status_code in [200, 201]:
                return True
        except Exception:
            pass
    # Fallback: Twilio SMS
    try:
        if twilio_client:
            twilio_client.messages.create(
                body=msg[:1600], from_=TWILIO_FROM_NUMBER, to=phone)
            return True
    except Exception as e:
        print(f"WA/SMS error: {e}")
    return False

def notify_prashant(msg):
    return send_whatsapp(PRASHANT_WA, msg)

def make_call(phone, twiml_url):
    if not twilio_client:
        return None
    try:
        return twilio_client.calls.create(
            to=phone,
            from_=TWILIO_FROM_NUMBER,
            url=twiml_url,
            method="POST",
            status_callback=f"https://{get_host()}/call-status",
            status_callback_method="POST"
        )
    except Exception as e:
        print(f"Call error: {e}")
        return None

def get_host():
    return os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost:8000")

# ── QUOTATION CALCULATOR ──────────────────────────────────────
def calc_quote(vehicle_type, policy_type, year, idv=0, ncb_years=0, has_claim=False):
    age = datetime.now().year - int(year) if year else 3
    is_car = vehicle_type.lower() in ["car", "motor", "4wheeler"]

    if not idv or idv == 0:
        idv = max(100000, 500000 - (age * 50000)) if is_car else max(30000, 100000 - (age * 10000))
    idv = int(idv)

    od = int(idv * (0.035 if is_car else 0.03))
    tp = (3416 if idv > 300000 else 2094) if is_car else (1854 if idv > 75000 else 1366)

    ncb_pct = {0: 0, 1: 20, 2: 25, 3: 35, 4: 45, 5: 50}.get(min(ncb_years, 5), 0)
    ncb_disc = int(od * ncb_pct / 100) if not has_claim else 0

    pt = policy_type.lower()
    if "third" in pt or pt == "tp":
        gst = int(tp * 0.18)
        return {
            "policy_type": "Third Party Only",
            "tp": tp, "gst": gst, "total": tp + gst, "idv": idv
        }
    elif "zero" in pt:
        zd = int(idv * 0.015)
        net = od - ncb_disc + tp + zd
        gst = int(net * 0.18)
        return {
            "policy_type": "Zero Depreciation",
            "idv": idv, "od": od, "tp": tp, "ncb": ncb_disc,
            "zd": zd, "net": net, "gst": gst, "total": net + gst
        }
    else:
        net = od - ncb_disc + tp
        gst = int(net * 0.18)
        zd_opt = net + int(idv * 0.015) + int((net + int(idv * 0.015)) * 0.18)
        return {
            "policy_type": "Comprehensive",
            "idv": idv, "od": od, "tp": tp, "ncb": ncb_disc,
            "net": net, "gst": gst, "total": net + gst,
            "with_zero_dep": zd_opt
        }

def quote_message(agent_name, customer_name, reg_no, vehicle_type, q):
    fn = first_name(agent_name)
    lines = [
        "🚗 *INSURANCE QUOTATION*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"👤 *Agent:* {fn} ji",
        f"👤 *Customer:* {customer_name or 'N/A'}",
        f"🚗 *Vehicle:* {vehicle_type} {reg_no or ''}",
        f"📋 *Policy:* {q.get('policy_type', '')}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    if q.get("idv"):    lines.append(f"💰 IDV: ₹{q['idv']:,}")
    if q.get("od"):     lines.append(f"📊 OD: ₹{q['od']:,}")
    if q.get("tp"):     lines.append(f"⚖️ TP: ₹{q['tp']:,}")
    if q.get("ncb"):    lines.append(f"✅ NCB Discount: -₹{q['ncb']:,}")
    if q.get("zd"):     lines.append(f"🛡️ Zero Dep: ₹{q['zd']:,}")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        f"💳 GST 18%: ₹{q.get('gst', 0):,}",
        f"💰 *TOTAL: ₹{q.get('total', 0):,}*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🤖 Priya AI | {PRASHANT['name']}",
        "✅ Login at pbpartners.com to issue policy",
    ]
    if q.get("with_zero_dep"):
        lines.append(f"💡 With Zero Dep: ₹{q['with_zero_dep']:,}")
    return "\n".join(lines)

# ── PRIYA AI SYSTEM PROMPT ────────────────────────────────────
PRIYA_SYSTEM = f"""Tu "Priya" hai — {PRASHANT['name']} ji ki Personal AI Sales Assistant.
IRM Code: {PRASHANT['irm_code']}

IDENTITY:
- Naam: Priya | 4 saal insurance experience
- Hindi + Marathi dono mein baat kar sakti hai
- Warm, professional, persistent

SALES FLOW (ek ek step):
1. "Aaj koi business hai? Customer ready hai?"
2. "Car hai ki Bike?"
3. "Policy type: Comprehensive / Third Party / Zero Dep?"
4. "RC photo WhatsApp karo {PRASHANT['phone']} pe. Ya reg number batao."
5. "Purani policy hai? Pichle saal claim tha?" (NCB ke liye)
6. "Customer ka naam aur mobile number?"
7. "Main quotation nikal kar WhatsApp karti hoon — 2 minute!"

PERSONALITY:
- 2-3 sentences max per reply
- Never give up on a sale
- Always end with a question to keep conversation going

TRANSFER:
- "Prashant ji se baat karni hai" sune to call transfer karo

PB KNOWLEDGE:
- Motor/Bike/Health/Life insurance
- NCB, Zero Dep, IDV, Comprehensive
- Commission 15-25%
- Payment link through app
- Policy issuance on pbpartners.com
"""

# ── AI REPLY ──────────────────────────────────────────────────
def priya_reply(user_msg, agent, call_sid, ctype="sales"):
    try:
        if call_sid not in conversations:
            conversations[call_sid] = []
        conversations[call_sid].append({"role": "user", "content": user_msg})

        agent_ctx = ""
        if agent:
            agent_ctx = f"\nCurrent Agent: {agent['name']} ({agent['agent_id']}) | {agent['line']} | Onboarding: {agent['onboarding']}"

        system = PRIYA_SYSTEM + agent_ctx

        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system},
                      *conversations[call_sid][-8:]],
            max_tokens=150,
            temperature=0.75
        )
        reply = resp.choices[0].message.content.strip()
        conversations[call_sid].append({"role": "assistant", "content": reply})

        # Check for transfer intent
        transfer = any(w in user_msg.lower() for w in
                       ["prashant", "transfer", "manager", "प्रशांत", "sahab"])
        return reply, transfer

    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Maafi, thodi technical problem. Phir se bolein please.", False

# ── CALL TRANSFER ─────────────────────────────────────────────
def do_transfer():
    resp = VoiceResponse()
    resp.say("Ek second, Prashant ji se connect karti hoon.",
             voice="Polly.Aditi", language="hi-IN")
    d = Dial(caller_id=TWILIO_FROM_NUMBER, timeout=30)
    d.number(PRASHANT_NUMBER)
    resp.append(d)
    resp.say("Prashant ji abhi available nahi. Main unhe message karti hoon.",
             voice="Polly.Aditi", language="hi-IN")
    return Response(str(resp), mimetype="text/xml")

# ── ROUTES ────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Priya AI v4.0 Active ✅",
        "host": get_host(),
        "agents": len(AGENTS),
        "calling_hours": "9:00 AM — 8:00 PM",
        "today": {
            "target": f"₹{today_biz['target']:,}",
            "achieved": f"₹{today_biz['total_premium']:,}",
            "policies": today_biz["total_policies"],
        },
        "pages": {
            "/quote-form":           "💰 Quote Generator",
            "/daily-report":         "📊 Daily Report",
            "/agents":               "👥 Agent List",
            "/call-all":             "📞 Call All Agents (POST)",
            "/marketing-page":       "🎯 Marketing Page",
        }
    })

# ── INCOMING CALL ─────────────────────────────────────────────
@app.route("/incoming-call", methods=["POST"])
def incoming_call():
    caller   = request.form.get("From", "")
    call_sid = request.form.get("CallSid", "")
    agent    = find_agent(caller)

    if agent:
        fn = first_name(agent["name"])
        intro = (f"{greeting()} {fn} ji! Main Priya hoon, "
                 f"Prashant ji ki AI assistant. "
                 f"Aaj koi Motor insurance business hai? "
                 f"Customer ready ho toh details do, main quotation nikalungi!")
    else:
        intro = (f"{greeting()}! Main Priya hoon, Prashant Chandratre ji ki AI. "
                 f"Aap PB Partners agent hain? Aaj koi business hai?")

    aid = agent["agent_id"] if agent else ""
    resp = VoiceResponse()
    g = Gather(
        input="speech",
        language="hi-IN",
        speech_timeout="auto",
        action=f"/handle-speech?aid={aid}&caller={caller}",
        method="POST"
    )
    g.say(intro, voice="Polly.Aditi", language="hi-IN")
    resp.append(g)
    resp.say("Response nahi mila. Please call karein.", voice="Polly.Aditi", language="hi-IN")
    return Response(str(resp), mimetype="text/xml")

# ── HANDLE SPEECH ─────────────────────────────────────────────
@app.route("/handle-speech", methods=["POST"])
def handle_speech():
    speech   = request.form.get("SpeechResult", "")
    aid      = request.args.get("aid", "")
    caller   = request.args.get("caller", "")
    call_sid = request.form.get("CallSid", "")

    agent = next((a for a in AGENTS if a["agent_id"] == aid), None)

    if not speech:
        resp = VoiceResponse()
        g = Gather(
            input="speech", language="hi-IN", speech_timeout="auto",
            action=f"/handle-speech?aid={aid}&caller={caller}", method="POST"
        )
        g.say("Samajh nahi aaya. Phir se bolein please.",
              voice="Polly.Aditi", language="hi-IN")
        resp.append(g)
        return Response(str(resp), mimetype="text/xml")

    if any(w in speech.lower() for w in ["prashant", "transfer", "manager", "sahab"]):
        return do_transfer()

    ai_reply, need_transfer = priya_reply(speech, agent, call_sid)

    if need_transfer:
        return do_transfer()

    resp = VoiceResponse()
    g = Gather(
        input="speech", language="hi-IN", speech_timeout="auto",
        action=f"/handle-speech?aid={aid}&caller={caller}", method="POST"
    )
    g.say(ai_reply, voice="Polly.Aditi", language="hi-IN")
    resp.append(g)
    return Response(str(resp), mimetype="text/xml")

# ── CALL STATUS ───────────────────────────────────────────────
@app.route("/call-status", methods=["POST"])
def call_status():
    to_num = request.form.get("To", "")
    status = request.form.get("CallStatus", "")
    print(f"📊 Call to {to_num}: {status}")
    return "", 200

# ── OUTBOUND CALL HANDLER ─────────────────────────────────────
@app.route("/outbound-handler", methods=["POST"])
def outbound_handler():
    aid  = request.args.get("aid", "")
    name = request.args.get("name", "Agent")
    fn   = first_name(name)

    intro = (f"{greeting()} {fn} ji! Main Priya hoon, Prashant ji ki AI. "
             f"Aaj koi Motor insurance business hai? "
             f"Customer ready ho toh RC details do, main quotation nikalungi!")

    resp = VoiceResponse()
    g = Gather(
        input="speech", language="hi-IN", speech_timeout="auto",
        action=f"/handle-speech?aid={aid}&caller=", method="POST"
    )
    g.say(intro, voice="Polly.Aditi", language="hi-IN")
    resp.append(g)
    resp.say("Koi response nahi. Prashant ji se baat karein.",
             voice="Polly.Aditi", language="hi-IN")
    return Response(str(resp), mimetype="text/xml")

# ── CALL ALL AGENTS ───────────────────────────────────────────
@app.route("/call-all", methods=["POST"])
def call_all():
    if not is_calling_hours():
        now = datetime.now().strftime("%I:%M %p")
        return jsonify({
            "error": "Calling hours: 9:00 AM — 8:00 PM only",
            "current_time": now,
            "allowed": "9:00 AM to 8:00 PM"
        }), 403

    data  = request.json or {}
    limit = int(data.get("limit", len(AGENTS)))
    host  = get_host()
    results = []

    for agent in AGENTS[:limit]:
        fn  = first_name(agent["name"])
        url = f"https://{host}/outbound-handler?aid={agent['agent_id']}&name={fn}"
        c   = make_call(agent["phone"], url)

        if c:
            today_biz["agents_called"].append(agent["agent_id"])
            results.append({"agent": agent["name"], "phone": agent["phone"],
                            "status": "calling", "sid": c.sid})
        else:
            results.append({"agent": agent["name"], "phone": agent["phone"],
                            "status": "failed"})

    called = len([r for r in results if r["status"] == "calling"])
    notify_prashant(
        f"📞 Priya ne {called}/{len(AGENTS)} agents ko call kiya!\n"
        f"⏰ {datetime.now().strftime('%I:%M %p')}"
    )
    return jsonify({"success": True, "called": called,
                    "total": len(AGENTS), "results": results})

# ── SINGLE AGENT CALL ─────────────────────────────────────────
@app.route("/make-call", methods=["POST"])
def make_single_call():
    if not is_calling_hours():
        return jsonify({"error": "Calling hours: 9 AM — 8 PM only"}), 403

    data  = request.json or {}
    phone = str(data.get("phone", ""))
    name  = data.get("name", "Agent")
    aid   = data.get("agent_id", "")

    if len(phone) == 10:
        phone = "+91" + phone

    fn   = first_name(name)
    host = get_host()
    url  = f"https://{host}/outbound-handler?aid={aid}&name={fn}"
    c    = make_call(phone, url)

    return jsonify({"success": bool(c), "call_sid": c.sid if c else None,
                    "agent": name, "phone": phone})

# ── QUOTE REQUEST API ─────────────────────────────────────────
@app.route("/quote-request", methods=["POST"])
def quote_request():
    data = request.json or {}
    aid  = data.get("agent_id", "")
    agent = next((a for a in AGENTS if a["agent_id"] == aid), None)

    q = calc_quote(
        vehicle_type = data.get("vehicle_type", "car"),
        policy_type  = data.get("policy_type", "comprehensive"),
        year         = data.get("year", datetime.now().year - 3),
        idv          = data.get("idv", 0),
        ncb_years    = data.get("ncb_years", 0),
        has_claim    = data.get("has_claim", False)
    )

    wa_sent = False
    if agent:
        msg = quote_message(
            agent["name"],
            data.get("customer_name", ""),
            data.get("reg_number", ""),
            data.get("vehicle_type", ""),
            q
        )
        wa_sent = send_whatsapp(agent["phone"], msg)
        notify_prashant(
            f"📋 NEW QUOTE\n{agent['name']}\n"
            f"{data.get('customer_name','N/A')} | {data.get('customer_mobile','N/A')}\n"
            f"{data.get('vehicle_type','')} {data.get('reg_number','')}\n"
            f"₹{q.get('total',0):,}"
        )
        key = f"{aid}_{datetime.now().strftime('%H%M%S')}"
        active_leads[key] = {
            "agent": agent["name"], "case": data,
            "quote": q, "time": datetime.now().strftime("%H:%M"),
            "date": str(date.today())
        }

    return jsonify({"success": True, "quotation": q, "wa_sent": wa_sent,
                    "agent": agent["name"] if agent else "Unknown"})

# ── QUOTE FORM (UI) ───────────────────────────────────────────
@app.route("/quote-form", methods=["GET"])
def quote_form():
    opts = "".join([
        f'<option value="{a["agent_id"]}">{first_name(a["name"])} ({a["agent_id"]})</option>'
        for a in AGENTS
    ])
    return f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Priya — Quote</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial;background:#0d0d0d;color:#F0F0F0;padding:20px;max-width:500px;margin:0 auto;}}
h1{{color:#E8521A;margin-bottom:4px;font-size:20px;}}
.sub{{color:#909090;font-size:12px;margin-bottom:18px;}}
.card{{background:#1c1c1c;border:1px solid rgba(232,82,26,.2);border-radius:14px;padding:16px;margin-bottom:12px;}}
.ct{{font-size:10px;font-weight:700;color:#E8521A;text-transform:uppercase;margin-bottom:10px;}}
.f2{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.fr{{margin-bottom:10px;}}
label{{display:block;font-size:11px;color:#909090;margin-bottom:4px;}}
input,select{{width:100%;background:#252525;border:1px solid rgba(255,255,255,.1);border-radius:9px;padding:10px 12px;color:#F0F0F0;font-size:14px;outline:none;}}
input:focus,select:focus{{border-color:#E8521A;}}
.btn{{width:100%;background:#E8521A;border:none;border-radius:12px;padding:14px;color:#fff;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:12px;}}
.result{{background:rgba(0,200,83,.08);border:1px solid rgba(0,200,83,.3);border-radius:12px;padding:16px;display:none;}}
.rrow{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px;}}
.rrow:last-child{{border:none;}}
.rv{{font-weight:700;color:#00C853;}}
.big{{font-size:32px;font-weight:900;color:#00C853;text-align:center;margin:10px 0;}}
.links{{display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap;}}
.link{{color:#E8521A;text-decoration:none;font-size:12px;padding:6px 12px;background:#252525;border-radius:8px;}}
</style></head><body>
<h1>🤖 Priya — Quote Generator</h1>
<p class="sub">Prashant Chandratre ji | IRM169896 | Motor Insurance</p>

<div class="card"><div class="ct">👤 Agent & Customer</div>
  <div class="fr"><label>Agent</label><select id="ai">{opts}</select></div>
  <div class="f2">
    <div class="fr"><label>Customer Name</label><input id="cn" placeholder="Rahul Kumar"></div>
    <div class="fr"><label>Mobile</label><input id="cm" type="tel" placeholder="9876543210"></div>
  </div>
</div>

<div class="card"><div class="ct">🚗 Vehicle Details</div>
  <div class="f2">
    <div class="fr"><label>Type</label><select id="vt">
      <option value="Car">🚗 Car</option>
      <option value="Bike">🏍️ Bike</option>
    </select></div>
    <div class="fr"><label>Year</label><input id="vy" type="number" placeholder="2021"></div>
  </div>
  <div class="fr"><label>Reg Number</label>
    <input id="rn" placeholder="MH01AB1234" oninput="this.value=this.value.toUpperCase()">
  </div>
  <div class="fr"><label>IDV (optional)</label>
    <input id="idv" type="number" placeholder="Auto calculate">
  </div>
</div>

<div class="card"><div class="ct">📋 Policy Details</div>
  <div class="fr"><label>Policy Type</label><select id="pt">
    <option value="Comprehensive">Comprehensive (First Party)</option>
    <option value="ZeroDep">Zero Depreciation (Best)</option>
    <option value="ThirdParty">Third Party Only</option>
  </select></div>
  <div class="f2">
    <div class="fr"><label>NCB Years</label><select id="nc">
      <option value="0">0 — New/Claim</option>
      <option value="1">1yr — 20% off</option>
      <option value="2">2yr — 25% off</option>
      <option value="3">3yr — 35% off</option>
      <option value="4">4yr — 45% off</option>
      <option value="5">5yr — 50% off</option>
    </select></div>
    <div class="fr"><label>Claim Last Year?</label><select id="cl">
      <option value="false">No (NCB milega)</option>
      <option value="true">Yes</option>
    </select></div>
  </div>
</div>

<button class="btn" onclick="generate()">🚀 Generate + Send WhatsApp</button>

<div class="result" id="result">
  <div style="color:#00C853;font-weight:800;margin-bottom:10px;" id="ptype">💰 Quotation</div>
  <div id="rows"></div>
  <div class="big" id="total">₹0</div>
  <div style="text-align:center;font-size:12px;color:#909090;margin-top:6px;" id="status">Processing...</div>
</div>

<div class="links">
  <a href="/agents" class="link">👥 Agents</a>
  <a href="/daily-report" class="link">📊 Report</a>
  <a href="/marketing-page" class="link">🎯 Marketing</a>
</div>

<script>
async function generate() {{
  const btn = document.querySelector(".btn");
  btn.textContent = "⏳ Generating..."; btn.disabled = true;
  try {{
    const res = await fetch("/quote-request", {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{
        agent_id:       document.getElementById("ai").value,
        vehicle_type:   document.getElementById("vt").value,
        policy_type:    document.getElementById("pt").value,
        year:           parseInt(document.getElementById("vy").value) || 2021,
        reg_number:     document.getElementById("rn").value,
        customer_name:  document.getElementById("cn").value,
        customer_mobile:document.getElementById("cm").value,
        ncb_years:      parseInt(document.getElementById("nc").value),
        has_claim:      document.getElementById("cl").value === "true",
        idv:            parseInt(document.getElementById("idv").value) || 0
      }})
    }});
    const d = await res.json();
    const q = d.quotation;
    document.getElementById("ptype").textContent = "💰 " + q.policy_type;
    let rows = "";
    if (q.idv)  rows += `<div class="rrow"><span>IDV</span><span class="rv">₹${{q.idv.toLocaleString("en-IN")}}</span></div>`;
    if (q.od)   rows += `<div class="rrow"><span>OD Premium</span><span>₹${{q.od.toLocaleString("en-IN")}}</span></div>`;
    if (q.tp)   rows += `<div class="rrow"><span>TP Premium</span><span>₹${{q.tp.toLocaleString("en-IN")}}</span></div>`;
    if (q.ncb)  rows += `<div class="rrow"><span>NCB Discount</span><span style="color:#00C853;">-₹${{q.ncb.toLocaleString("en-IN")}}</span></div>`;
    if (q.zd)   rows += `<div class="rrow"><span>Zero Dep</span><span>₹${{q.zd.toLocaleString("en-IN")}}</span></div>`;
    if (q.gst)  rows += `<div class="rrow"><span>GST 18%</span><span>₹${{q.gst.toLocaleString("en-IN")}}</span></div>`;
    if (q.with_zero_dep) rows += `<div class="rrow"><span>💡 With Zero Dep</span><span>₹${{q.with_zero_dep.toLocaleString("en-IN")}}</span></div>`;
    document.getElementById("rows").innerHTML = rows;
    document.getElementById("total").textContent = "₹" + q.total.toLocaleString("en-IN");
    document.getElementById("status").textContent = d.wa_sent ? "✅ WhatsApp sent!" : "⚠️ Quote ready (send manually)";
    document.getElementById("result").style.display = "block";
  }} catch(e) {{
    alert("Error: " + e.message);
  }} finally {{
    btn.textContent = "🚀 Generate + Send WhatsApp"; btn.disabled = false;
  }}
}}
</script></body></html>'''

# ── AGENTS PAGE ───────────────────────────────────────────────
@app.route("/agents", methods=["GET"])
def agents_page():
    rows = ""
    for i, a in enumerate(AGENTS, 1):
        today_p = today_biz["agent_data"].get(a["agent_id"], {}).get("premium", 0)
        rows += (f'<tr><td>{i}</td>'
                 f'<td><b>{first_name(a["name"])}</b><br><small style="color:#909090">{a["name"]}</small></td>'
                 f'<td style="color:#E8521A;">{a["phone"]}</td>'
                 f'<td style="color:#909090;">{a["agent_id"]}</td>'
                 f'<td>{a["line"]}</td>'
                 f'<td><span style="color:#00C853;">{a["onboarding"]}</span></td>'
                 f'<td style="color:#00C853;">₹{today_p:,}</td>'
                 f'<td><a href="#" onclick="callAgent(\'{a["agent_id"]}\',\'{a["phone"]}\',\'{first_name(a["name"])}\')" style="color:#E8521A;">📞</a></td>'
                 f'</tr>')
    return f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Priya — Agents</title>
<style>
body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;padding:20px;}}
h1{{color:#E8521A;margin-bottom:12px;}}
.top{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}}
.btn{{background:#E8521A;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;cursor:pointer;border:none;}}
.btn2{{background:#252525;border:1px solid rgba(255,255,255,.1);color:#F0F0F0;}}
.stats{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}}
.stat{{background:#1c1c1c;border-radius:10px;padding:11px 16px;}}
.sn{{font-size:20px;font-weight:900;color:#E8521A;}}
.sl{{font-size:11px;color:#909090;}}
table{{width:100%;border-collapse:collapse;font-size:12px;}}
th{{background:#1c1c1c;padding:9px 10px;text-align:left;font-size:10px;text-transform:uppercase;color:#909090;}}
td{{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.05);}}
small{{font-size:10px;}}
</style></head><body>
<h1>🤖 Priya AI — Agent Panel</h1>
<div class="stats">
  <div class="stat"><div class="sn">{len(AGENTS)}</div><div class="sl">Total Agents</div></div>
  <div class="stat"><div class="sn" style="color:#00C853;">{len([a for a in AGENTS if a["onboarding"]=="Done"])}</div><div class="sl">Active</div></div>
  <div class="stat"><div class="sn">₹{today_biz["total_premium"]:,}</div><div class="sl">Today Business</div></div>
  <div class="stat"><div class="sn">{len(active_leads)}</div><div class="sl">Leads</div></div>
</div>
<div class="top">
  <button class="btn" onclick="callAll()">📞 Call All Now</button>
  <a href="/quote-form" class="btn" style="text-decoration:none;">💰 Quote</a>
  <a href="/daily-report" class="btn btn2" style="text-decoration:none;">📊 Report</a>
  <a href="/marketing-page" class="btn btn2" style="text-decoration:none;">🎯 Marketing</a>
</div>
<table>
<thead><tr><th>#</th><th>Name</th><th>Phone</th><th>Code</th><th>Line</th><th>Status</th><th>Today ₹</th><th>Call</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<script>
function callAll() {{
  if (!confirm("Priya will call all {len(AGENTS)} agents now?")) return;
  fetch("/call-all", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{limit:{len(AGENTS)}}})  }})
    .then(r=>r.json())
    .then(d=>alert("✅ Calling " + d.called + "/" + d.total + " agents!"))
    .catch(e=>alert("Error: "+e.message));
}}
function callAgent(aid, phone, name) {{
  if (!confirm("Call " + name + "?")) return;
  fetch("/make-call", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{agent_id:aid,phone:phone,name:name}})}})
    .then(r=>r.json())
    .then(d=>alert(d.success?"✅ Calling "+name+"!":"❌ Failed — Check calling hours (9AM-8PM)"))
    .catch(e=>alert("Error: "+e.message));
}}
</script></body></html>'''

# ── DAILY REPORT ──────────────────────────────────────────────
@app.route("/daily-report", methods=["GET", "POST"])
def daily_report():
    tp   = today_biz["total_premium"]
    tpl  = today_biz["total_policies"]
    tgt  = today_biz["target"]
    gap  = tgt - tp
    pct  = round((tp / tgt * 100), 1) if tgt > 0 else 0

    report = (
        f"📊 PRIYA AI DAILY REPORT\n"
        f"{today_biz['date']} | {datetime.now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 TARGET:   ₹{tgt:,}\n"
        f"💰 ACHIEVED: ₹{tp:,} ({pct}%)\n"
        f"📋 POLICIES: {tpl}\n"
        f"📱 LEADS:    {len(active_leads)}\n"
        f"⚠️ GAP:      ₹{gap:,}\n"
        f"👥 AGENTS:   {len(AGENTS)}\n"
        f"📞 CALLED:   {len(today_biz['agents_called'])}"
    )

    if request.method == "POST" or request.args.get("send") == "true":
        notify_prashant(report)

    return jsonify({
        "date": today_biz["date"],
        "target": tgt, "achieved": tp,
        "policies": tpl, "leads": len(active_leads),
        "gap": gap, "percentage": pct,
        "agents_called": len(today_biz["agents_called"]),
        "report_text": report
    })

# ── MARKETING PAGE ────────────────────────────────────────────
@app.route("/marketing-page", methods=["GET"])
def marketing_page():
    return f'''<!DOCTYPE html><html lang="hi"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PB Partners — Join FREE</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial;background:#0a1628;color:#F0F0F0;}}
.hero{{background:linear-gradient(135deg,#003087,#0066CC);padding:32px 20px 40px;text-align:center;}}
.badge{{background:#FFD700;color:#003087;font-weight:900;font-size:14px;border-radius:99px;padding:8px 20px;display:inline-block;margin-bottom:12px;}}
.ht{{font-size:26px;font-weight:900;color:#fff;margin-bottom:6px;line-height:1.3;}}
.hs{{font-size:13px;color:rgba(255,255,255,.85);}}
.content{{padding:20px;max-width:500px;margin:0 auto;}}
.card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:16px;margin-bottom:14px;}}
.ct{{font-size:10px;font-weight:700;color:#FFD700;text-transform:uppercase;margin-bottom:10px;}}
.benefits{{display:grid;grid-template-columns:1fr 1fr;gap:9px;}}
.benefit{{background:rgba(255,255,255,.07);border-radius:11px;padding:12px;text-align:center;}}
.bico{{font-size:24px;margin-bottom:5px;}}
.btxt{{font-size:12px;font-weight:700;}}
.di{{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06);}}
.di:last-child{{border:none;}}
.di span{{font-size:20px;width:28px;text-align:center;flex-shrink:0;}}
.dn{{font-size:13px;font-weight:700;}}
.dd{{font-size:11px;color:#A0A0A0;}}
.cta{{display:block;width:100%;border-radius:13px;padding:15px;font-size:15px;font-weight:900;text-decoration:none;text-align:center;margin-bottom:10px;}}
.cta-c{{background:linear-gradient(135deg,#003087,#0066CC);color:#fff;}}
.cta-w{{background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;}}
.note{{font-size:10px;color:#606060;text-align:center;margin-top:12px;line-height:1.6;}}
</style></head><body>
<div class="hero">
  <div class="badge">🎉 100% FREE — No Charges</div>
  <div class="ht">Insurance Agent Bano<br>Ghar Se Kamao!</div>
  <div class="hs">Free Training • Achha Commission • Policybazaar ka Bharosa</div>
</div>
<div class="content">
  <div class="card"><div class="ct">📞 Contact</div>
    <div class="di"><span>👤</span><div><div class="dn">{PRASHANT["name"]}</div><div class="dd">{PRASHANT["role"]}</div></div></div>
    <div class="di"><span>📞</span><div><div class="dn">{PRASHANT["phone"]}</div></div></div>
    <div class="di"><span>💬</span><div><div class="dn">{PRASHANT["wa"]}</div></div></div>
  </div>
  <div class="card"><div class="ct">✨ Benefits</div>
    <div class="benefits">
      <div class="benefit"><div class="bico">🆓</div><div class="btxt">100% FREE</div></div>
      <div class="benefit"><div class="bico">🏠</div><div class="btxt">Ghar Se Kaam</div></div>
      <div class="benefit"><div class="bico">💰</div><div class="btxt">Achha Commission</div></div>
      <div class="benefit"><div class="bico">📚</div><div class="btxt">Free Training</div></div>
      <div class="benefit"><div class="bico">⏰</div><div class="btxt">Flexible Time</div></div>
      <div class="benefit"><div class="bico">🏆</div><div class="btxt">India #1 Platform</div></div>
    </div>
  </div>
  <div class="card"><div class="ct">📋 Documents Required</div>
    <div class="di"><span>🪪</span><div><div class="dn">PAN Card</div><div class="dd">Clear photo</div></div></div>
    <div class="di"><span>🪪</span><div><div class="dn">Aadhaar Card</div><div class="dd">Front + Back</div></div></div>
    <div class="di"><span>🏦</span><div><div class="dn">Bank Account</div><div class="dd">Cancelled cheque</div></div></div>
    <div class="di"><span>📄</span><div><div class="dn">10th Certificate</div><div class="dd">Education proof</div></div></div>
    <div class="di"><span>📱</span><div><div class="dn">Mobile Number</div><div class="dd">Aadhaar linked</div></div></div>
    <div class="di"><span>📧</span><div><div class="dn">Email ID</div><div class="dd">Active email</div></div></div>
    <div class="di"><span>🤳</span><div><div class="dn">Selfie</div><div class="dd">Live photo</div></div></div>
  </div>
  <a href="tel:+91{PRASHANT['phone']}" class="cta cta-c">📞 Call Now — {PRASHANT['phone']}</a>
  <a href="{PRASHANT['wa']}" class="cta cta-w">💬 WhatsApp — Join Now!</a>
  <div class="note">{PRASHANT["note"]}<br>Powered by Priya AI — {PRASHANT["name"]} ji ki Personal AI</div>
</div></body></html>'''

# ── HEALTH CHECK ──────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🤖 Priya AI v4.0 — Port {port} — {len(AGENTS)} agents loaded")
    app.run(host="0.0.0.0", port=port, debug=False)
