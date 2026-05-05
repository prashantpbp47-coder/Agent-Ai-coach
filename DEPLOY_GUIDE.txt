#!/usr/bin/env python3
# ================================================================
# AGENT GURU v2.0 — partnershub_voice_agent.py
# Excel Auto-Update + Incoming + Outgoing Calls
# ================================================================

from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Dial
from twilio.rest import Client
import openai, os, json, random, io
from datetime import datetime

try:
    import pandas as pd
    EXCEL_OK = True
except:
    EXCEL_OK = False

app = Flask(__name__)

# === CONFIG ===
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_API_KEY     = os.environ.get('TWILIO_API_KEY', '')
TWILIO_API_SECRET  = os.environ.get('TWILIO_API_SECRET', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '+917709446589')
OPENAI_API_KEY     = os.environ.get('OPENAI_API_KEY', '')
MANAGER_NUMBER     = os.environ.get('MANAGER_NUMBER', '+917709446589')
UPLOAD_PASSWORD    = os.environ.get('UPLOAD_PASSWORD', 'agentguru2024')

openai.api_key = OPENAI_API_KEY
twilio_client  = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
conversations  = {}

# ================================================================
# AGENTS — 217 Nashik Agents
# /upload-excel se naya Excel upload karo — auto update!
# ================================================================
cached_contacts = [
    {'name': 'NIKITA NAMDEV WATPADE', 'phone': '+919823709779', 'agent_id': 'IP218178', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'SUNILBHAI VANJARI', 'phone': '+919922053230', 'agent_id': 'IP263054', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'BHAVSAR DHIRAJ ANIL', 'phone': '+918830819624', 'agent_id': 'IP175831', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'MILIND AVCHITE BAISANE', 'phone': '+919823128100', 'agent_id': 'IP175913', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'NANDAKISHOR JADE', 'phone': '+919403096269', 'agent_id': 'IP176022', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'POOJA SUNIL VANJARI', 'phone': '+919730019786', 'agent_id': 'IP196966', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'ATHARVA MAHENDRA KOTME', 'phone': '+919226479928', 'agent_id': 'IP197050', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'AHER RATNAKAR SACHIN', 'phone': '+919372938587', 'agent_id': 'IP242440', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'ATHARVA BHAUSAHEB BODKE', 'phone': '+918421701515', 'agent_id': 'IP264207', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'SANDEEP ASHOK GAIKWAD', 'phone': '+918855858540', 'agent_id': 'IP226792', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'RAHUL RAOSAHEB MHASKE', 'phone': '+918698064781', 'agent_id': 'IP196304', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'AMITA SINGH', 'phone': '+916392528473', 'agent_id': 'IP189023', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'MORE SUDHAKAR BHASKAR', 'phone': '+919423178469', 'agent_id': 'IP234416', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'SHARAD MURLIDHAR AHER', 'phone': '+919923356981', 'agent_id': 'IP278848', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'DATTATRAY MADHAVRAO RAUT', 'phone': '+919823369776', 'agent_id': 'IP279116', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'PRASAD BHAGWAN BHADANGE', 'phone': '+918805267355', 'agent_id': 'IP300604', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'JYOTI NANDKISHOR KOTHAWADE', 'phone': '+919371525685', 'agent_id': 'IP209632', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'ANKUSH PANDHARINATH JAGTAP', 'phone': '+918575757875', 'agent_id': 'IP249232', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'NITIN RAMDAS MURTADAK', 'phone': '+918007857492', 'agent_id': 'IP271207', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
    {'name': 'Viraj Vaibhav Bhanage', 'phone': '+919823280440', 'agent_id': 'IP249200', 'rm': 'Prashant Dinkar Chandratre', 'city': 'Nashik'},
]
# NOTE: Puri 217 agents list ke liye /upload-excel pe Excel upload karein

# ================================================================
# EXCEL UPLOAD PAGE — NEW AGENTS AUTO UPDATE
# ================================================================
@app.route('/upload-excel', methods=['GET', 'POST'])
def upload_excel():
    if request.method == 'GET':
        return f'''<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Agent Guru — Excel Upload</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial,sans-serif;background:#0d0d0d;color:#F0F0F0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}}
.card{{background:#1c1c1c;border:1px solid rgba(232,82,26,.3);border-radius:20px;padding:32px;width:100%;max-width:480px;}}
h1{{color:#E8521A;text-align:center;font-size:22px;margin-bottom:4px;}}
.sub{{text-align:center;color:#909090;font-size:13px;margin-bottom:24px;}}
.stat-row{{display:flex;gap:10px;margin-bottom:24px;}}
.stat{{flex:1;background:#252525;border-radius:12px;padding:14px;text-align:center;}}
.stat-n{{font-size:28px;font-weight:900;color:#E8521A;}}
.stat-l{{font-size:11px;color:#909090;margin-top:3px;}}
label{{display:block;font-size:11px;font-weight:700;color:#909090;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;}}
.file-area{{width:100%;background:#252525;border:2px dashed rgba(232,82,26,.4);border-radius:12px;padding:24px;text-align:center;cursor:pointer;margin-bottom:14px;}}
.file-area:hover{{border-color:#E8521A;}}
input[type=file]{{display:none;}}
input[type=password]{{width:100%;background:#252525;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:12px 14px;color:#F0F0F0;font-size:14px;margin-bottom:20px;outline:none;}}
input[type=password]:focus{{border-color:#E8521A;}}
button{{width:100%;background:#E8521A;border:none;border-radius:12px;padding:15px;color:#fff;font-size:16px;font-weight:800;cursor:pointer;}}
.info{{background:#252525;border-radius:10px;padding:14px;margin-top:20px;font-size:12px;color:#909090;}}
.col{{display:inline-block;background:#1c1c1c;border:1px solid rgba(232,82,26,.2);border-radius:6px;padding:3px 8px;margin:3px;font-size:11px;color:#E8521A;}}
.links{{display:flex;gap:8px;justify-content:center;margin-top:16px;flex-wrap:wrap;}}
.link{{color:#E8521A;text-decoration:none;font-size:12px;padding:6px 12px;background:#252525;border-radius:8px;}}
</style>
</head>
<body>
<div class="card">
<div style="font-size:48px;text-align:center;margin-bottom:8px;">📊</div>
<h1>Agent Guru</h1>
<p class="sub">Excel Upload — Agents Auto Update</p>
<div class="stat-row">
<div class="stat"><div class="stat-n">{len(cached_contacts)}</div><div class="stat-l">Current Agents</div></div>
<div class="stat"><div class="stat-n">✅</div><div class="stat-l">System Active</div></div>
</div>
<form method="POST" enctype="multipart/form-data">
<label>📎 Excel File Choose करें</label>
<label class="file-area" for="file-inp">
<div style="font-size:32px;margin-bottom:8px;">📁</div>
<div style="font-weight:700;">Click to select file</div>
<div style="font-size:12px;color:#909090;margin-top:4px;">.xlsx .xls .csv supported</div>
<input type="file" id="file-inp" name="excel_file" accept=".xlsx,.xls,.csv" required onchange="document.getElementById('fname').textContent=this.files[0].name">
</label>
<div id="fname" style="color:#E8521A;font-size:13px;margin-bottom:14px;text-align:center;"></div>
<label>🔐 Upload Password</label>
<input type="password" name="password" placeholder="Password enter करें" required>
<button type="submit">🚀 Upload & Update Agents</button>
</form>
<div class="info">
<strong style="color:#E8521A;">Required Excel Columns:</strong><br>
<div style="margin-top:6px;">
<span class="col">PartnerCode</span>
<span class="col">PartnerName</span>
<span class="col">PartnerPhoneNumber</span>
<span class="col">RMName</span>
<span class="col">RMCity</span>
</div>
<div style="margin-top:10px;">💡 New agent add karein Excel mein → Upload karein → System update!</div>
</div>
<div class="links">
<a href="/agents" class="link">👥 View Agents</a>
<a href="/get-contacts" class="link">📋 JSON Data</a>
<a href="/" class="link">🏠 Home</a>
</div>
</div>
</body>
</html>'''

    # POST — Process Excel
    if not EXCEL_OK:
        return '<h2>Error: pandas not installed. Add to requirements.txt</h2>', 500

    password = request.form.get('password', '')
    if password != UPLOAD_PASSWORD:
        return '<html><body style="background:#0d0d0d;color:#FF3B3B;font-family:Arial;text-align:center;padding:50px;"><h2>❌ Wrong Password!</h2><a href="/upload-excel" style="color:#E8521A;">← Back</a></body></html>', 403

    if 'excel_file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['excel_file']
    try:
        file_bytes = file.read()
        fname = file.filename.lower()
        df = pd.read_csv(io.BytesIO(file_bytes)) if fname.endswith('.csv') else pd.read_excel(io.BytesIO(file_bytes))

        new_contacts = []
        skipped = 0
        for _, row in df.iterrows():
            name  = str(row.get('PartnerName') or row.get('Name') or '').strip()
            phone = str(row.get('PartnerPhoneNumber') or row.get('Phone') or row.get('Mobile') or '').strip()
            code  = str(row.get('PartnerCode') or row.get('Code') or '').strip()
            rm    = str(row.get('RMName') or row.get('RM') or '').strip()
            city  = str(row.get('RMCity') or row.get('City') or 'Nashik').strip()

            try:
                phone_clean = str(int(float(phone)))
            except:
                phone_clean = phone.replace(' ','').replace('-','')

            if not phone_clean or len(phone_clean) < 10:
                skipped += 1
                continue

            if not phone_clean.startswith('+'):
                phone_clean = '+91' + phone_clean[-10:]

            new_contacts.append({'name': name, 'phone': phone_clean, 'agent_id': code, 'rm': rm, 'city': city})

        if not new_contacts:
            return '<html><body style="background:#0d0d0d;color:#FF3B3B;font-family:Arial;text-align:center;padding:50px;"><h2>No valid contacts found!</h2><a href="/upload-excel" style="color:#E8521A;">← Try again</a></body></html>'

        global cached_contacts
        old = len(cached_contacts)
        cached_contacts = new_contacts

        return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Success!</title>
<style>body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;text-align:center;padding:40px 20px;}}
.card{{background:#1c1c1c;border:1px solid rgba(0,200,83,.3);border-radius:20px;padding:32px;max-width:400px;margin:0 auto;}}
.num{{font-size:64px;font-weight:900;color:#00C853;margin:10px 0;}}
h2{{color:#00C853;}}
.row{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #252525;font-size:14px;text-align:left;}}
.btn{{display:inline-block;background:#E8521A;color:#fff;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:800;margin:8px 4px;}}
.btn2{{background:#252525;border:1px solid rgba(255,255,255,.1);}}</style>
</head>
<body><div class="card">
<div style="font-size:48px;">✅</div>
<h2>Upload Successful!</h2>
<div class="num">{len(new_contacts)}</div>
<div style="color:#909090;margin-bottom:20px;">Agents Updated!</div>
<div class="row"><span>📊 Previous</span><span>{old}</span></div>
<div class="row"><span>✅ New Total</span><span>{len(new_contacts)}</span></div>
<div class="row"><span>⏭️ Skipped</span><span>{skipped}</span></div>
<div class="row"><span>🕐 Updated</span><span>{datetime.now().strftime("%d/%m %H:%M")}</span></div>
<div style="margin-top:20px;">
<a href="/upload-excel" class="btn">📤 Upload Again</a>
<a href="/agents" class="btn btn2">👥 View Agents</a>
</div>
</div></body></html>'''

    except Exception as e:
        return f'<html><body style="background:#0d0d0d;color:#FF3B3B;font-family:Arial;text-align:center;padding:50px;"><h2>❌ Error: {str(e)}</h2><a href="/upload-excel" style="color:#E8521A;">← Try again</a></body></html>'


# ================================================================
# AGENTS LIST PAGE
# ================================================================
@app.route('/agents', methods=['GET'])
def list_agents():
    search = request.args.get('search', '').lower()
    filtered = [a for a in cached_contacts if not search or search in a['name'].lower() or search in a['phone']] if search else cached_contacts

    rows = ''.join([f'<tr><td>{i}</td><td><strong>{a["name"]}</strong></td><td style="color:#E8521A;font-family:monospace;">{a["phone"]}</td><td style="color:#909090;font-size:11px;">{a["agent_id"]}</td><td>{a.get("rm","")}</td><td>{a.get("city","")}</td><td><a href="/call-agent/{a["agent_id"]}" style="color:#E8521A;font-size:12px;">📞</a></td></tr>' for i, a in enumerate(filtered, 1)])

    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Agents</title>
<style>body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;padding:20px;}}
h1{{color:#E8521A;margin-bottom:4px;}}
.top{{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center;}}
input{{background:#1c1c1c;border:1px solid rgba(232,82,26,.3);border-radius:10px;padding:10px 14px;color:#F0F0F0;font-size:14px;outline:none;flex:1;min-width:200px;}}
.btn{{background:#E8521A;color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;white-space:nowrap;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}
th{{background:#1c1c1c;padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:#909090;}}
td{{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.05);}}
tr:hover td{{background:rgba(232,82,26,.04);}}
</style></head>
<body>
<h1>👥 Agent Guru — Agents ({len(filtered)} of {len(cached_contacts)})</h1>
<div class="top">
<input type="text" placeholder="🔍 Search name or phone..." value="{search}" oninput="window.location='/agents?search='+this.value">
<a href="/upload-excel" class="btn">📤 Upload Excel</a>
</div>
<table><thead><tr><th>#</th><th>Name</th><th>Phone</th><th>Code</th><th>RM</th><th>City</th><th>Call</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>'''


# ================================================================
# API ROUTES
# ================================================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'Agent Guru Active ✅',
        'version': '2.0 — Excel Auto-Update',
        'total_agents': len(cached_contacts),
        'routes': {
            'GET  /upload-excel': 'Excel upload page — agents auto update',
            'GET  /agents': 'All agents list (browser)',
            'GET  /get-contacts': 'Contacts JSON',
            'POST /add-agent': 'Single agent add {name,phone,password}',
            'POST /remove-agent': 'Agent remove {phone,password}',
            'POST /make-call': 'Outgoing call {phone,message}',
            'POST /call-agent/<id>': 'Call specific agent',
            'POST /call-all': 'Call all agents {message,limit}',
            'POST /incoming-call': 'Twilio webhook',
        }
    })

@app.route('/get-contacts', methods=['GET'])
def get_contacts():
    return jsonify({'contacts': cached_contacts, 'total': len(cached_contacts), 'message': f'{len(cached_contacts)} agents ready!'})

@app.route('/add-agent', methods=['POST'])
def add_agent():
    data = request.json or {}
    if data.get('password') != UPLOAD_PASSWORD:
        return jsonify({'error': 'Wrong password'}), 403
    phone = str(data.get('phone', '')).strip()
    if len(phone) == 10: phone = '+91' + phone
    for a in cached_contacts:
        if a['phone'] == phone:
            return jsonify({'error': 'Already exists', 'agent': a}), 409
    new = {'name': data.get('name',''), 'phone': phone, 'agent_id': data.get('agent_id', 'IP'+str(random.randint(100000,999999))), 'rm': data.get('rm',''), 'city': data.get('city','Nashik')}
    cached_contacts.append(new)
    return jsonify({'success': True, 'agent': new, 'total': len(cached_contacts)})

@app.route('/remove-agent', methods=['POST'])
def remove_agent():
    global cached_contacts
    data = request.json or {}
    if data.get('password') != UPLOAD_PASSWORD:
        return jsonify({'error': 'Wrong password'}), 403
    phone = str(data.get('phone','')).replace('+91','')
    before = len(cached_contacts)
    cached_contacts = [a for a in cached_contacts if a['phone'].replace('+91','') != phone]
    if len(cached_contacts) == before:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'success': True, 'removed': before - len(cached_contacts), 'total': len(cached_contacts)})

@app.route('/incoming-call', methods=['POST'])
def incoming_call():
    caller = request.form.get('From', '')
    call_sid = request.form.get('CallSid', '')
    agent = find_agent_by_phone(caller)
    name = agent['name'].split()[0].title() if agent else 'Agent'
    print(f"📞 Incoming: {caller} — {name}")
    response = VoiceResponse()
    gather = Gather(input='speech', language='hi-IN', speech_timeout='auto', action=f'/handle-speech?agent={name}&caller={caller}', method='POST')
    gather.say(f"Namaste {name} ji! Main Agent Guru hoon, aapka AI assistant. PB Partners mein aapki kaise madad kar sakta hoon?", voice='Polly.Aditi', language='hi-IN')
    response.append(gather)
    response.say("Koi response nahi aaya. Phir call karein.", voice='Polly.Aditi', language='hi-IN')
    return Response(str(response), mimetype='text/xml')

@app.route('/handle-speech', methods=['POST'])
def handle_speech():
    speech = request.form.get('SpeechResult', '')
    agent = request.args.get('agent', 'Agent')
    caller = request.args.get('caller', '')
    call_sid = request.form.get('CallSid', '')
    print(f"🎤 {agent}: {speech}")
    if not speech:
        response = VoiceResponse()
        response.say("Maafi chahta hoon, samajh nahi aaya. Phir bolein.", voice='Polly.Aditi', language='hi-IN')
        return Response(str(response), mimetype='text/xml')
    ai_reply = get_ai_response(speech, agent, call_sid)
    response = VoiceResponse()
    gather = Gather(input='speech', language='hi-IN', speech_timeout='auto', action=f'/handle-speech?agent={agent}&caller={caller}', method='POST')
    gather.say(ai_reply, voice='Polly.Aditi', language='hi-IN')
    response.append(gather)
    return Response(str(response), mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    print(f"📊 Call {request.form.get('CallSid')}: {request.form.get('CallStatus')}")
    return '', 200

@app.route('/make-call', methods=['POST'])
def make_call():
    data = request.json or {}
    phone = str(data.get('phone', ''))
    message = data.get('message', 'Namaste! Yeh Agent Guru ka call hai. PB Partners app open karein.')
    if len(phone) == 10: phone = '+91' + phone
    if not phone: return jsonify({'error': 'phone required'}), 400
    try:
        call = twilio_client.calls.create(to=phone, from_=TWILIO_FROM_NUMBER, twiml=f'<Response><Say voice="Polly.Aditi" language="hi-IN">{message}</Say></Response>')
        return jsonify({'success': True, 'call_sid': call.sid, 'to': phone})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/call-agent/<agent_id>', methods=['GET', 'POST'])
def call_agent(agent_id):
    agent = next((a for a in cached_contacts if a['agent_id'] == agent_id), None)
    if not agent: return jsonify({'error': 'Not found'}), 404
    msg = (request.json or {}).get('message', f'Namaste {agent["name"].split()[0].title()} ji! Yeh PB Partners ka reminder call hai. Apna target complete karein.')
    try:
        call = twilio_client.calls.create(to=agent['phone'], from_=TWILIO_FROM_NUMBER, twiml=f'<Response><Say voice="Polly.Aditi" language="hi-IN">{msg}</Say></Response>')
        return jsonify({'success': True, 'agent': agent['name'], 'call_sid': call.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/call-all', methods=['POST'])
def call_all():
    data = request.json or {}
    message = data.get('message', 'Namaste! PB Partners ka reminder — apna target complete karein. Dhanyawad!')
    limit = int(data.get('limit', 5))
    results = []
    for agent in cached_contacts[:limit]:
        try:
            call = twilio_client.calls.create(to=agent['phone'], from_=TWILIO_FROM_NUMBER, twiml=f'<Response><Say voice="Polly.Aditi" language="hi-IN">Namaste {agent["name"].split()[0].title()} ji! {message}</Say></Response>')
            results.append({'agent': agent['name'], 'status': 'called', 'sid': call.sid})
        except Exception as e:
            results.append({'agent': agent['name'], 'status': 'failed', 'error': str(e)})
    return jsonify({'success': True, 'results': results, 'called': len(results)})

# ================================================================
# HELPERS
# ================================================================
def find_agent_by_phone(phone):
    clean = phone.replace('+91','').replace('+','').strip()[-10:]
    return next((a for a in cached_contacts if a['phone'].replace('+91','').strip()[-10:] == clean), None)

def get_ai_response(msg, agent_name, call_sid):
    try:
        if call_sid not in conversations: conversations[call_sid] = []
        conversations[call_sid].append({"role": "user", "content": msg})
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"Tu Agent Guru hai — expert insurance AI assistant. {agent_name} ji se Hindi mein baat kar. 2-3 sentences mein helpful insurance guidance de. PB Partners app use karne mein guide kar."}, *conversations[call_sid][-6:]],
            max_tokens=120, temperature=0.7)
        reply = resp.choices[0].message.content
        conversations[call_sid].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return "Maafi chahta hoon, abhi technical dikkat hai. Dobara try karein."

# ================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Agent Guru v2.0 — Port {port} — {len(cached_contacts)} agents")
    app.run(host='0.0.0.0', port=port, debug=False)
