from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Dial
from twilio.rest import Client
import openai, os, json, random
from datetime import datetime

app = Flask(__name__)

# ══ CONFIG ═══════════════════════════════════════════════
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_API_KEY     = os.environ.get('TWILIO_API_KEY', '')
TWILIO_API_SECRET  = os.environ.get('TWILIO_API_SECRET', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '+917709446589')
OPENAI_API_KEY     = os.environ.get('OPENAI_API_KEY', '')
MANAGER_NUMBER     = os.environ.get('MANAGER_NUMBER', '+917709446589')

openai.api_key = OPENAI_API_KEY
twilio_client  = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
conversations  = {}
agent_profiles = {}

# ══ MEGA KNOWLEDGE BASE ══════════════════════════════════
SYSTEM_KNOWLEDGE = """
Aap "PRIYA" hain — Partners HUB Intelligent Assistant.
Prashant Ji ki team ke AI voice assistant.

════════════════════════════════════
PB PARTNERS KNOWLEDGE
════════════════════════════════════

PLATFORM:
- India ka fastest growing insurance platform
- 18+ insurance companies ek jagah
- Motor, Life, Health, Travel, Home insurance
- Helpline: 1800 120 800

POSP REGISTRATION (FREE):
1. pbpartners.com par register karo
2. 15 ghante online training
3. IRDAI exam (online, easy)
4. License milega — bechna shuru!

ELIGIBILITY:
- Age: 18+ | Education: 10th pass | Investment: ZERO

MOTOR POLICY STEPS:
1. Vehicle number lo
2. App → Motor → New Policy
3. Details automatic fill
4. 18+ quotes compare
5. Customer ko best dikhao
6. Payment → PDF turant!

HEALTH POLICY STEPS:
1. Age, family details
2. Health → Compare Plans
3. Sum insured: 3L/5L/10L/25L
4. Pre-existing check
5. Payment → Policy!

LIFE INSURANCE STEPS:
1. Income × 10 = cover amount
2. Term plan best hai
3. Nominee details
4. Medical questionnaire
5. Policy 24-48 ghante

COMMISSION:
Motor: 15-20% | Health: 20-30%
Life: 25-40% | Travel: 15-25%
On-demand payout available!

COMMON PROBLEMS:
- Customer buy nahi kar raha: 24 ghante follow up, reason poocho
- Renewal: App → My Policies → Renewal
- Claim: App → Claims → New Claim → Upload docs
- KYC: Aadhaar + PAN app mein upload

════════════════════════════════════
BUSINESS MOTIVATION
════════════════════════════════════

- "Kal se zyada aaj karo!"
- "Sirf 3 calls aaj — kuch zaroor niklega!"
- "Health policy 10L = 20,000-30,000 commission!"
- "Motor renewal 15 min = 2000-5000 commission!"
- "Har NO aapko YES ke paas le jaata hai!"

INCOME IDEAS:
- WhatsApp Status mein daily tip daalo
- Festival par special messages bhejo
- Har customer se 2 referral maango
- Colony/society bulk campaign karo
- Car dealer se tie-up karo
- Office HR se group health discuss karo
- Subah 9-10 baje follow up karo — best time!

════════════════════════════════════
360° AGENT RECRUITMENT
════════════════════════════════════

Naye agents ko ye bolо:
"Namaskar Ji! Main Partners HUB se hoon.
Aap insurance mein kaam karte hain?
Humara platform unique hai — AI assistant 24/7 guide karega.
Policy banana virtual ho gaya — ghar baithe!
Zero investment, unlimited earning.
Interested? Main registration mein help karta hoon!"

KEY BENEFITS JO BATAO:
1. AI assistant milega — kabhi bhi guide karega
2. 18+ companies — best rates guaranteed
3. Virtual support — ghar se kaam
4. On-demand payout
5. Training aur support complete

════════════════════════════════════
TRAINING CURRICULUM
════════════════════════════════════

MODULE 1: Platform Use
- Dashboard, quote nikalna, policy issue

MODULE 2: Products
- Motor types, Health comparison, Life basics

MODULE 3: Sales
- Customer se baat, objection handle, closing

MODULE 4: Digital Marketing
- WhatsApp, social media, referral

MODULE 5: Income Max
- High commission products, renewals, referrals

════════════════════════════════════
PRIYA KI RULES
════════════════════════════════════

1. Hindi/Hinglish/Marathi mein baat karo
2. Phone call — MAX 2-3 sentences
3. Hamesha energetic aur warm raho
4. Business ideas proactively do
5. Naye agents recruit karne inspire karo
6. Step by step guide karo
7. Income potential hamesha yaad dilao
8. Agar frustrated agent → "TRANSFER_TO_MANAGER"

TRANSFER KAB:
- Account/payment issue
- Agent frustrated ho
- Prashant Ji maange
- 3 baar same problem
"""

# ══ VOICE HANDLERS ═══════════════════════════════════════

@app.route('/')
def home():
    return jsonify({'system': 'PRIYA — Partners HUB AI v2.0', 'status': 'Active ✅'})

@app.route('/voice', methods=['POST'])
def voice():
    response   = VoiceResponse()
    call_sid   = request.form.get('CallSid', '')
    name       = request.args.get('name', 'Agent Ji')
    ctype      = request.args.get('type', 'morning')

    conversations[call_sid] = []

    greetings = {
        'morning': (
            f"Namaskar {name} Ji! Main PRIYA hoon — Prashant Ji ki team se. "
            f"PB Partner mein policy banane ke liye virtually koi bhi madad kar sakte hain. "
            f"Kal se zyada aaj karo! Koi sawaal ya business idea chahiye?"
        ),
        'recruit': (
            f"Namaskar {name} Ji! Main Partners HUB se bol rahi hoon. "
            f"Aap insurance mein kaam karte hain — hamare AI-powered platform ke baare mein suna? "
            f"Zero investment, unlimited earning. Ek minute baat kar sakte hain?"
        ),
        'training': (
            f"Namaskar {name} Ji! Main PRIYA hoon — aapki AI training assistant. "
            f"Aaj PB Partners ka poora process seekhenge. "
            f"Kahan se shuru karein — Motor, Health ya Life?"
        ),
        'idea': (
            f"Namaskar {name} Ji! Main PRIYA hoon. "
            f"Aaj ke liye ek special business idea leke aayi hoon. "
            f"Sunna chahenge?"
        )
    }

    greeting = greetings.get(ctype, greetings['morning'])

    gather = Gather(
        input='speech',
        action=f'/gather?call_sid={call_sid}&name={name}',
        method='POST',
        language='hi-IN',
        speech_timeout='auto',
        speech_model='phone_call'
    )
    gather.say(greeting, language='hi-IN', voice='Polly.Aditi')
    response.append(gather)
    response.say("Theek hai Ji, baad mein baat karte hain. Dhanyawad!", language='hi-IN', voice='Polly.Aditi')
    return Response(str(response), mimetype='text/xml')

@app.route('/gather', methods=['POST'])
def gather_response():
    call_sid = request.args.get('call_sid', request.form.get('CallSid', ''))
    name     = request.args.get('name', 'Agent Ji')
    speech   = request.form.get('SpeechResult', '').strip()
    response = VoiceResponse()

    if not speech:
        g = Gather(input='speech', action=f'/gather?call_sid={call_sid}&name={name}',
                   method='POST', language='hi-IN', speech_timeout='auto')
        g.say("Maafi, suna nahi. Dobara bolein?", language='hi-IN', voice='Polly.Aditi')
        response.append(g)
        return Response(str(response), mimetype='text/xml')

    # Transfer triggers
    triggers = ['prashant', 'sir se', 'manager', 'transfer', 'solve nahi',
                'samajh nahi', 'escalate', 'complaint', 'baat karni']
    if any(t in speech.lower() for t in triggers):
        return do_transfer(name)

    if call_sid not in conversations:
        conversations[call_sid] = []
    conversations[call_sid].append({"role": "user", "content": speech})

    ai_text = get_ai_response(call_sid, name, speech)

    if "TRANSFER_TO_MANAGER" in ai_text:
        clean = ai_text.replace("TRANSFER_TO_MANAGER", "").strip()
        response.say(clean, language='hi-IN', voice='Polly.Aditi')
        response.say("Ruko Ji — Prashant Ji se connect karta hoon!", language='hi-IN', voice='Polly.Aditi')
        dial = Dial(); dial.number(MANAGER_NUMBER)
        response.append(dial)
        return Response(str(response), mimetype='text/xml')

    conversations[call_sid].append({"role": "assistant", "content": ai_text})

    g = Gather(input='speech', action=f'/gather?call_sid={call_sid}&name={name}',
               method='POST', language='hi-IN', speech_timeout='auto', speech_model='phone_call')
    g.say(ai_text, language='hi-IN', voice='Polly.Aditi')
    response.append(g)
    response.say("Koi aur sawaal? Prashant Ji se baat karni ho toh bolein.", language='hi-IN', voice='Polly.Aditi')
    return Response(str(response), mimetype='text/xml')

def get_ai_response(call_sid, name, msg):
    try:
        history = conversations.get(call_sid, [])
        system  = f"{SYSTEM_KNOWLEDGE}\n\nAgent: {name}\nTime: {datetime.now().strftime('%H:%M')}"
        messages = [{"role": "system", "content": system}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": msg})

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        res    = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, max_tokens=150, temperature=0.8)
        return res.choices[0].message.content.strip()
    except:
        return "Ji ek second — main Prashant Ji se connect karta hoon. TRANSFER_TO_MANAGER"

def do_transfer(name):
    response = VoiceResponse()
    response.say(
        f"Bilkul {name} Ji! Prashant Ji se abhi connect karta hoon — ek second!",
        language='hi-IN', voice='Polly.Aditi')
    dial = Dial(caller_id=TWILIO_FROM_NUMBER, action='/call-done', method='POST')
    dial.number(MANAGER_NUMBER)
    response.append(dial)
    return Response(str(response), mimetype='text/xml')

@app.route('/call-done', methods=['POST'])
def call_done():
    call_sid = request.form.get('CallSid', '')
    conversations.pop(call_sid, None)
    r = VoiceResponse()
    r.say("Dhanyawad! PB Partners ke saath grow karte rahein!", language='hi-IN', voice='Polly.Aditi')
    return Response(str(r), mimetype='text/xml')

# ══ REST APIs ════════════════════════════════════════════

@app.route('/make-call', methods=['POST'])
def make_call():
    d    = request.json or {}
    to   = d.get('to')
    name = d.get('name', 'Agent Ji')
    ctype = d.get('type', 'morning')
    if not to: return jsonify({'error': 'number required'}), 400
    try:
        call = twilio_client.calls.create(
            to=to, from_=TWILIO_FROM_NUMBER,
            url=f"{request.host_url}voice?name={name}&type={ctype}", method='POST')
        return jsonify({'success': True, 'sid': call.sid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/bulk-calls', methods=['POST'])
def bulk_calls():
    d       = request.json or {}
    agents  = d.get('agents', [])
    ctype   = d.get('type', 'morning')
    results = []
    for a in agents:
        try:
            call = twilio_client.calls.create(
                to=a['phone'], from_=TWILIO_FROM_NUMBER,
                url=f"{request.host_url}voice?name={a.get('name','Agent')}&type={ctype}",
                method='POST')
            results.append({'name': a.get('name'), 'status': 'calling', 'sid': call.sid})
        except Exception as e:
            results.append({'name': a.get('name'), 'status': 'failed', 'error': str(e)})
    return jsonify({'total': len(agents), 'initiated': len([r for r in results if r['status']=='calling']), 'results': results})

@app.route('/business-idea', methods=['GET'])
def business_idea():
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Aap insurance business expert hain. Hindi mein practical ideas do."},
                {"role": "user", "content": f"Aaj {datetime.now().strftime('%A')} hai. PB Partners agent ke liye ek practical business idea do jo aaj implement ho sake. 3-4 sentences."}
            ], max_tokens=200)
        return jsonify({'date': datetime.now().strftime('%d/%m/%Y'), 'idea': res.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daily-motivation', methods=['GET'])
def daily_motivation():
    msgs = [
        "Aaj ka din aapka hai! Sirf 3 calls karo — kuch zaroor niklega!",
        "Ek policy = ek family secure. Aap sirf business nahi — zindagiyaan badal rahe hain!",
        "Top agent woh hai jo sabse zyada karta hai — aaj shuru karo!",
        "Kal ka customer aaj ka follow up hai. Aaj hi contact karo!",
        "Har NO aapko YES ke paas le jaata hai — aur calls karo!",
        "Motor renewal — 15 minute, 2000-5000 commission. 5 renewals = 25,000 aaj!"
    ]
    return jsonify({'motivation': random.choice(msgs), 'date': datetime.now().strftime('%d/%m/%Y')})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'system': 'PRIYA v2.0 — Partners HUB AI',
        'status': 'Active ✅',
        'active_calls': len(conversations),
        'call_types': ['morning', 'recruit', 'training', 'idea'],
        'features': ['PB Partners Knowledge', 'Business Motivation', '360 Recruitment', 'Training', 'Manager Transfer']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
