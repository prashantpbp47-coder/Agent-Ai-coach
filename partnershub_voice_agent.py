from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Dial
from twilio.rest import Client
import openai, os, json, random, requests, base64
from datetime import datetime

app = Flask(__name__)

# ══ CONFIG ═══════════════════════════════════════════════
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_API_KEY     = os.environ.get('TWILIO_API_KEY', '')
TWILIO_API_SECRET  = os.environ.get('TWILIO_API_SECRET', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '+917709446589')
OPENAI_API_KEY     = os.environ.get('OPENAI_API_KEY', '')
MANAGER_NUMBER     = os.environ.get('MANAGER_NUMBER', '+917709446589')
INTERAKT_KEY       = os.environ.get('INTERAKT_KEY', '')

openai.api_key = OPENAI_API_KEY
twilio_client  = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
conversations  = {}
agent_profiles = {}
cached_contacts = []  # Interakt se fetched contacts

# ══ INTERAKT CONTACTS FETCH ══════════════════════════════

def fetch_interakt_contacts():
    """Interakt se sabhi 221 agents fetch karo"""
    global cached_contacts
    try:
        # Interakt API - contacts list
        url = "https://api.interakt.ai/v1/public/track/users/"
        headers = {
            "Authorization": f"Basic {INTERAKT_KEY}",
            "Content-Type": "application/json"
        }
        
        all_contacts = []
        offset = 0
        limit = 100
        
        while True:
            params = {"limit": limit, "offset": offset}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                contacts = data.get("data", {}).get("contacts", [])
                if not contacts:
                    break
                    
                for c in contacts:
                    phone = c.get("phoneNumber", "")
                    name = c.get("name", "Agent Ji")
                    if phone and phone != "":
                        # Format phone number
                        if not phone.startswith("+"):
                            phone = f"+91{phone}" if len(phone) == 10 else f"+{phone}"
                        all_contacts.append({
                            "name": name or "Agent Ji",
                            "phone": phone,
                            "id": c.get("userId", "")
                        })
                
                if len(contacts) < limit:
                    break
                offset += limit
            else:
                break
        
        if all_contacts:
            cached_contacts = all_contacts
            return all_contacts
        else:
            # Fallback: try different Interakt endpoint
            url2 = "https://api.interakt.ai/v1/public/track/users/list"
            res2 = requests.get(url2, headers=headers, timeout=10)
            if res2.status_code == 200:
                data2 = res2.json()
                users = data2.get("result", [])
                for u in users:
                    phone = u.get("phone_number", u.get("phoneNumber", ""))
                    name = u.get("name", "Agent Ji")
                    if phone:
                        if not phone.startswith("+"):
                            phone = f"+91{phone}" if len(phone) == 10 else f"+{phone}"
                        cached_contacts.append({
                            "name": name,
                            "phone": phone
                        })
            return cached_contacts
            
    except Exception as e:
        print(f"Interakt fetch error: {e}")
        return cached_contacts

# ══ KNOWLEDGE BASE ════════════════════════════════════════
SYSTEM_KNOWLEDGE = """
Aap "PRIYA" hain — Partners HUB Intelligent Assistant.
Prashant Ji ki team ke AI voice assistant.

PB PARTNERS:
- India ka fastest growing insurance platform
- 18+ insurance companies
- Motor, Life, Health, Travel, Home insurance
- Helpline: 1800 120 800

POSP REGISTRATION (FREE):
1. pbpartners.com par register
2. 15 ghante online training
3. IRDAI exam
4. License → bechna shuru!

MOTOR POLICY:
1. Vehicle number lo
2. App → Motor → New Policy
3. 18+ quotes compare
4. Payment → PDF!

HEALTH POLICY:
1. Age, family details
2. Sum insured: 3L/5L/10L/25L
3. Payment → Policy!

LIFE INSURANCE:
1. Income × 10 = cover
2. Term plan best
3. Policy 24-48 ghante

COMMISSION:
Motor: 15-20% | Health: 20-30%
Life: 25-40% | Travel: 15-25%

MOTIVATION:
- "Kal se zyada aaj karo!"
- "Sirf 3 calls — kuch zaroor niklega!"
- "Har NO aapko YES ke paas le jaata hai!"

INCOME IDEAS:
- WhatsApp Status mein daily tip
- Har customer se 2 referral maango
- Colony bulk health campaign
- Car dealer tie-up
- Office HR se group health

RECRUITMENT SCRIPT:
"Namaskar Ji! Main Partners HUB se hoon.
AI assistant milega, Zero investment, Unlimited earning.
Interested?"

RULES:
1. Hindi/Hinglish/Marathi mein
2. Max 2-3 sentences (phone call)
3. Energetic aur warm
4. Business ideas proactively do
5. TRANSFER_TO_MANAGER jab frustrated ho
"""

# ══ VOICE ROUTES ═════════════════════════════════════════

@app.route('/')
def home():
    return jsonify({
        'system': 'PRIYA v2.0 — Partners HUB AI',
        'status': 'Active ✅',
        'total_agents': len(cached_contacts)
    })

@app.route('/voice', methods=['POST'])
def voice():
    response  = VoiceResponse()
    call_sid  = request.form.get('CallSid', '')
    name      = request.args.get('name', 'Agent Ji')
    ctype     = request.args.get('type', 'morning')

    conversations[call_sid] = []

    greetings = {
        'morning': f"Namaskar {name} Ji! Main PRIYA hoon — Prashant Ji ki team se. PB Partner mein policy banane ke liye virtually koi bhi madad kar sakte hain. Kal se zyada aaj karo! Koi sawaal ya business idea chahiye?",
        'recruit': f"Namaskar {name} Ji! Main Partners HUB se bol rahi hoon. AI-powered insurance platform — zero investment, unlimited earning. Ek minute baat kar sakte hain?",
        'training': f"Namaskar {name} Ji! Main PRIYA hoon — aapki AI training assistant. Aaj PB Partners ka poora process seekhenge. Kahan se shuru karein?",
        'idea': f"Namaskar {name} Ji! Main PRIYA hoon. Aaj ke liye ek special business idea leke aayi hoon. Sunna chahenge?"
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

    triggers = ['prashant', 'sir se', 'manager', 'transfer', 'solve nahi',
                'samajh nahi', 'escalate', 'complaint']
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
        history  = conversations.get(call_sid, [])
        system   = f"{SYSTEM_KNOWLEDGE}\nAgent: {name}\nTime: {datetime.now().strftime('%H:%M')}"
        messages = [{"role": "system", "content": system}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": msg})
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        res    = client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=150, temperature=0.8)
        return res.choices[0].message.content.strip()
    except:
        return "Ji ek second — main Prashant Ji se connect karta hoon. TRANSFER_TO_MANAGER"

def do_transfer(name):
    response = VoiceResponse()
    response.say(f"Bilkul {name} Ji! Prashant Ji se abhi connect karta hoon!", language='hi-IN', voice='Polly.Aditi')
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

# ══ CONTACTS API ════════════════════════════════════════

@app.route('/get-contacts', methods=['GET'])
def get_contacts():
    """Interakt se contacts fetch karo"""
    contacts = fetch_interakt_contacts()
    return jsonify({
        'total': len(contacts),
        'contacts': contacts[:5],  # Preview - first 5
        'message': f'{len(contacts)} agents ready for calling!'
    })

@app.route('/make-call', methods=['POST'])
def make_call():
    d     = request.json or {}
    to    = d.get('to')
    name  = d.get('name', 'Agent Ji')
    ctype = d.get('type', 'morning')
    if not to: return jsonify({'error': 'number required'}), 400
    try:
        call = twilio_client.calls.create(
            to=to, from_=TWILIO_FROM_NUMBER,
            url=f"{request.host_url}voice?name={name}&type={ctype}", method='POST')
        return jsonify({'success': True, 'sid': call.sid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/morning-calls-all', methods=['POST'])
def morning_calls_all():
    """Interakt se sabhi agents fetch karke morning call karo"""
    contacts = fetch_interakt_contacts()
    if not contacts:
        return jsonify({'error': 'No contacts found in Interakt'}), 400
    
    results = []
    for agent in contacts[:10]:  # Pehle 10 test ke liye
        try:
            call = twilio_client.calls.create(
                to=agent['phone'],
                from_=TWILIO_FROM_NUMBER,
                url=f"{request.host_url}voice?name={agent['name']}&type=morning",
                method='POST'
            )
            results.append({'name': agent['name'], 'phone': agent['phone'], 'status': 'calling', 'sid': call.sid})
        except Exception as e:
            results.append({'name': agent['name'], 'phone': agent['phone'], 'status': 'failed', 'error': str(e)})
    
    return jsonify({
        'total_contacts': len(contacts),
        'called': len(results),
        'results': results
    })

@app.route('/bulk-calls', methods=['POST'])
def bulk_calls():
    d       = request.json or {}
    agents  = d.get('agents', [])
    ctype   = d.get('type', 'morning')
    
    # Agar agents empty hai toh Interakt se fetch karo
    if not agents:
        agents = fetch_interakt_contacts()
    
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
    
    return jsonify({'total': len(agents), 'results': results})

@app.route('/business-idea', methods=['GET'])
def business_idea():
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Insurance business expert. Hindi mein practical ideas."},
                {"role": "user", "content": f"Aaj {datetime.now().strftime('%A')} hai. PB Partners agent ke liye ek practical business idea do. 3-4 sentences."}
            ], max_tokens=200)
        return jsonify({'date': datetime.now().strftime('%d/%m/%Y'), 'idea': res.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daily-motivation', methods=['GET'])
def daily_motivation():
    msgs = [
        "Aaj ka din aapka hai! Sirf 3 calls karo — kuch zaroor niklega!",
        "Ek policy = ek family secure. Aap sirf business nahi — zindagiyaan badal rahe hain!",
        "Motor renewal — 15 minute, 2000-5000 commission. 5 renewals = 25,000 aaj!",
        "Har NO aapko YES ke paas le jaata hai — aur calls karo!",
        "Top agent woh hai jo sabse zyada karta hai — aaj shuru karo!",
        "Health policy 10L = 20,000-30,000 commission. Ek policy = ek mahine ki salary!"
    ]
    return jsonify({'motivation': random.choice(msgs), 'date': datetime.now().strftime('%d/%m/%Y')})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'system': 'PRIYA v2.0 — Partners HUB AI',
        'status': 'Active ✅',
        'active_calls': len(conversations),
        'total_agents': len(cached_contacts),
        'call_types': ['morning', 'recruit', 'training', 'idea'],
        'features': ['PB Partners Knowledge', 'Business Motivation', '360 Recruitment', 'Training', 'Manager Transfer', 'Interakt Auto-Fetch']
    })

if __name__ == '__main__':
    # Startup mein contacts fetch karo
    print("Fetching Interakt contacts...")
    fetch_interakt_contacts()
    print(f"Loaded {len(cached_contacts)} contacts")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
