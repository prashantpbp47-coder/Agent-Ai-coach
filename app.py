#!/usr/bin/env python3
"""
PRIYA AI v3.0 FINAL — Prashant Chandratre ji ki AI Assistant
Crash-proof | Hindi+Marathi | Sales | Quotation | WhatsApp | Leaderboard
"""

# ── Safe imports ──────────────────────────────────────────────
from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
import openai, os, json, random, io, requests
from datetime import datetime, date, timedelta

try:
    import pandas as pd
    EXCEL_OK = True
except:
    EXCEL_OK = False

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID','')
TWILIO_API_KEY     = os.environ.get('TWILIO_API_KEY','')
TWILIO_API_SECRET  = os.environ.get('TWILIO_API_SECRET','')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER','+917709446589')
OPENAI_API_KEY     = os.environ.get('OPENAI_API_KEY','')
PRASHANT_NUMBER    = os.environ.get('PRASHANT_NUMBER','+917709446589')
PRASHANT_WA        = os.environ.get('PRASHANT_WHATSAPP','+917709446589')
UPLOAD_PASSWORD    = os.environ.get('UPLOAD_PASSWORD','agentguru2024')
DAILY_TARGET       = int(os.environ.get('DAILY_TARGET','300000'))
INTERAKT_KEY       = os.environ.get('INTERAKT_API_KEY','')

openai.api_key = OPENAI_API_KEY
try:
    twilio_client = Client(TWILIO_API_KEY, TWILIO_API_SECRET, TWILIO_ACCOUNT_SID)
except:
    twilio_client = None

# ── CONSTANTS ─────────────────────────────────────────────────
PRASHANT = {
    "name":"Prashant Chandratre","role":"Relationship Manager",
    "company":"PB Partners — Policybazaar","tagline":"Ek Rishta Bharose Ka",
    "phone":"7709446589","wa":"wa.me/7709446589",
    "email":"prashantchandratre@pbpartners.com","web":"pbpartners.com",
    "note":"PBPartners is a brand under Policybazaar Insurance Broker Pvt. Ltd."
}

DOCS_REQUIRED = [
    {"id":1,"name":"PAN Card","emoji":"🪪","detail":"Clear photo"},
    {"id":2,"name":"Aadhaar Card","emoji":"🪪","detail":"Front + Back"},
    {"id":3,"name":"Bank Account","emoji":"🏦","detail":"Cancelled cheque"},
    {"id":4,"name":"10th Certificate","emoji":"📄","detail":"Education proof"},
    {"id":5,"name":"Mobile Number","emoji":"📱","detail":"Aadhaar linked"},
    {"id":6,"name":"Email ID","emoji":"📧","detail":"Active email"},
    {"id":7,"name":"Selfie","emoji":"🤳","detail":"Live photo"},
]

# ── DATA STORES ───────────────────────────────────────────────
conversations  = {}
agent_profiles = {}
daily_knowledge= []
pending_cases  = {}
active_leads   = {}
agent_scores   = {}
new_prospects  = {}
collected_docs = {}

today_biz = {
    'date':str(date.today()),'total_premium':0,'total_policies':0,
    'target':DAILY_TARGET,'agents_called':[],'agents_reported':[],
    'agent_data':{},'urgent_agents':[],'projected':0
}

# ── 217 AGENTS LOADED FROM EXCEL ─────────────────────────────
cached_contacts = [
    {'name':'NIKITA NAMDEV WATPADE','phone':'+919823709779','agent_id':'IP218178','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SUNILBHAI VANJARI','phone':'+919922053230','agent_id':'IP263054','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BHAVSAR DHIRAJ ANIL','phone':'+918830819624','agent_id':'IP175831','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MILIND AVCHITE BAISANE','phone':'+919823128100','agent_id':'IP175913','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NANDAKISHOR JADE','phone':'+919403096269','agent_id':'IP176022','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'POOJA SUNIL VANJARI','phone':'+919730019786','agent_id':'IP196966','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ATHARVA MAHENDRA KOTME','phone':'+919226479928','agent_id':'IP197050','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'AHER RATNAKAR SACHIN','phone':'+919372938587','agent_id':'IP242440','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ATHARVA BHAUSAHEB BODKE','phone':'+918421701515','agent_id':'IP264207','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANDEEP ASHOK GAIKWAD','phone':'+918855858540','agent_id':'IP226792','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Viraj Vaibhav Bhanage','phone':'+919823280440','agent_id':'IP249200','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANKUSH PANDHARINATH JAGTAP','phone':'+918575757875','agent_id':'IP249232','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NITIN RAMDAS MURTADAK','phone':'+918007857492','agent_id':'IP271207','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'AMITA SINGH','phone':'+916392528473','agent_id':'IP189023','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MORE SUDHAKAR BHASKAR','phone':'+919423178469','agent_id':'IP234416','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHARAD MURLIDHAR AHER','phone':'+919923356981','agent_id':'IP278848','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DATTATRAY MADHAVRAO RAUT','phone':'+919823369776','agent_id':'IP279116','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRASAD BHAGWAN BHADANGE','phone':'+918805267355','agent_id':'IP300604','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JYOTI NANDKISHOR KOTHAWADE','phone':'+919371525685','agent_id':'IP209632','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'YOGESH VISHANU CHAVAN','phone':'+919307290307','agent_id':'IP232087','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SONALI SUBHASH MORE','phone':'+918888076776','agent_id':'IP232472','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BHUSHAN BANSILAL CHAUDHARI','phone':'+918411966176','agent_id':'IP232576','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'UMAKANT DATTATRAY BAGUL','phone':'+919766850202','agent_id':'IP232618','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHRIKANT ASHOK DESHPANDE','phone':'+917721990070','agent_id':'IP299083','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'WAGHCHAURE RAVINDRA MARUTI','phone':'+917837222111','agent_id':'IP299622','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'GOKUL DAULAT SINGH BAYAS','phone':'+919673567137','agent_id':'IP169958','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHAIKH SALIM SHAIKH HUSEN','phone':'+919921146815','agent_id':'IP169962','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VAIBHAV BHASKAR KAUTKAR','phone':'+918390822211','agent_id':'IP169966','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MAHADEVI GOKUL BAYAS','phone':'+917030961219','agent_id':'IP170196','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Vaibhav Bhausaheb Gaikwad','phone':'+919763654214','agent_id':'IP191969','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Sandip Dattatraya Lokhande','phone':'+919527922951','agent_id':'IP214002','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Uttam Bajirao Dawkhara','phone':'+918010718442','agent_id':'IP236337','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJESH BHIMRAO AHER','phone':'+919834116505','agent_id':'IP259089','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BHAGYASHRI VINAY HIRE','phone':'+919657742043','agent_id':'IP281162','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PATIL JIJABRAO BHIKAN','phone':'+919881521148','agent_id':'IP171907','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SATISH DIGAMBARRAO SHELKE','phone':'+919834322175','agent_id':'IP303600','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANISHA GOKUL WANKHEDE','phone':'+919762206575','agent_id':'IP272307','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RATNA AMOL RAUT','phone':'+919011917669','agent_id':'IP293595','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JAGDISH DADAJI PAGARE','phone':'+919370035512','agent_id':'IP294024','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAGAR KESHAV HIWALE','phone':'+917030676301','agent_id':'IP315835','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAHUL MURLIDHAR PATIL','phone':'+917620856333','agent_id':'IP182242','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SARTHAK MUKUND MALI','phone':'+919970022089','agent_id':'IP182277','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RUSHIKESH S AHIRRAO','phone':'+917020375303','agent_id':'IP182887','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Shivani Sanjay Sonawane','phone':'+917263909091','agent_id':'IP228012','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Rajendra Dwarkanath Deshpande','phone':'+917719016611','agent_id':'IP250227','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KRISHNA PRAKASH GURUKULE','phone':'+917666553561','agent_id':'IP272463','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RUGVED MOHAN KHADILKAR','phone':'+917276715028','agent_id':'IP273040','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJENDRA VIKAS SOBHAGE','phone':'+919960385198','agent_id':'IP294636','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANOHAR M WANKHEDE','phone':'+919860690100','agent_id':'IP205889','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NIKITA AMEET MULEY','phone':'+918055181585','agent_id':'IP251027','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DATTATRYA G WAGH','phone':'+919561061421','agent_id':'IP251315','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DATTATRYA G WAGH','phone':'+919373978579','agent_id':'IP251326','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KHADKE SANTOSH MAHADEV','phone':'+919403519944','agent_id':'IP295344','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RUPALI SATISHRAO SHELAKE','phone':'+919273984200','agent_id':'IP295345','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MULAY VIKAS PRAKASH','phone':'+919371988988','agent_id':'IP185604','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PALLAVI RAJKIRAN JAGTAP','phone':'+919309986891','agent_id':'IP208625','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DEORE ROHINI BABANRAO','phone':'+919011079348','agent_id':'IP297346','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'OMKAR SHIRISH KSHIRSAGAR','phone':'+919822257644','agent_id':'IP297416','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHUBHAM VIJAY RAUT','phone':'+918600726290','agent_id':'IP184876','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MOIN RIYAJ PATEL','phone':'+919657571367','agent_id':'IP207921','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VIJAY MOGAL PAGARE','phone':'+918180831802','agent_id':'IP274771','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NAUSHABA ALZAR SHAIKH','phone':'+919028016443','agent_id':'IP274785','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KIRTI KRISHNA PATANKAR','phone':'+919552902506','agent_id':'IP187912','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VILAS CHANDRAKANT KAMBLE','phone':'+919822263722','agent_id':'IP210693','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SNEHAL PRAVIN BHOSALE','phone':'+918983551978','agent_id':'IP277606','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PANKAJ ANANDA GAWALI','phone':'+919921384873','agent_id':'IP298761','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DHIRAJ MAHIPALSING BAIS','phone':'+917028187346','agent_id':'IP172255','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRANAV RAVINDRA LAHAMGE','phone':'+917798798795','agent_id':'IP192834','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VISHWAJEET K CHHAJED','phone':'+918605725909','agent_id':'IP215487','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRIYANKA ANIL NIRBHAVANE','phone':'+919850646560','agent_id':'IP282300','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANGESH S CHANDRATRE','phone':'+919822247258','agent_id':'IP215990','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRAVIN MADHUKAR BHOSALE','phone':'+919511829113','agent_id':'IP260799','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANANT C CHOUDHARI','phone':'+918850237271','agent_id':'IP304963','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHIVAJI NIVRUTTI CHAVANKE','phone':'+917720031311','agent_id':'IP326198','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KANIFNATH GOPINATH BAGUL','phone':'+918669657799','agent_id':'IP326302','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BHARATI BHAGAT','phone':'+919822391131','agent_id':'IP326569','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'POONAM HARSHWARDHAN NARKE','phone':'+919834391762','agent_id':'IP155549','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KAVITA NARAYAN MONDHE','phone':'+919022487313','agent_id':'IP217670','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Anita Hiralal Mahajan','phone':'+919422094897','agent_id':'IP262530','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Nikita pavan more','phone':'+918626089183','agent_id':'IP262561','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'INDIRA SHANKAR SHINDE','phone':'+919823098181','agent_id':'IP283388','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJENDRA SHRIDHAR RASAL','phone':'+918379920396','agent_id':'IP173879','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DIVYA SAMADHAN GHAYAL','phone':'+919561426327','agent_id':'IP193856','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAHUL JAYPRAKASH NIKAM','phone':'+919850202951','agent_id':'IP284195','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJKUMAR RAGHUNATH PAGARE','phone':'+919890632159','agent_id':'IP328203','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANDIP M PATIL','phone':'+918830018514','agent_id':'IP180924','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'CHETAN MACHHINDRA GANGURDE','phone':'+919112099203','agent_id':'IP180975','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DARSHAN MAHENDRA KOTME','phone':'+919822017928','agent_id':'IP203882','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'HARSH PRASANNA MAHAJANI','phone':'+919225722777','agent_id':'IP203904','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DESALE VRISHABH PRAKASH','phone':'+919096708090','agent_id':'IP248341','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VAISHALI SACHIN KHAIRNAR','phone':'+919764600068','agent_id':'IP313672','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'GAHIWAD SACHIN PANDURANG','phone':'+919372913777','agent_id':'IP314246','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Kalpesh Kumar Sutrave','phone':'+917276016993','agent_id':'IP186129','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KALYANI VISHAL MARATHE','phone':'+919763017637','agent_id':'IP186496','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VARIS FIROZ KHAN','phone':'+918668211091','agent_id':'IP186511','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SUGANDH RAMESH DEORE','phone':'+919322457077','agent_id':'IP186525','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJESH Namdev Jadhav','phone':'+919763641005','agent_id':'IP209176','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHUBHANGI YOGESH KATARE','phone':'+918308368809','agent_id':'IP209303','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHAILENDRA JAIN','phone':'+919358825909','agent_id':'IP231675','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAHUL PADMAKAR CHAVAN','phone':'+919890098006','agent_id':'IP298094','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JYOTI ROHIT NIRBHAVANE','phone':'+917020001759','agent_id':'IP170917','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANWAR RASHID PINJARI','phone':'+919823853289','agent_id':'IP190114','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Rohit Rajendra Patil','phone':'+919881959199','agent_id':'IP235723','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHITAL SURAJ JADHAV','phone':'+917058157777','agent_id':'IP235847','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DHANASHRI SANDESH BHANDARKAR','phone':'+919423900764','agent_id':'IP280637','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANITA AVISHKAR PATALPURE','phone':'+919860177841','agent_id':'IP302053','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MAKARAND RAMDAS GHEGADMAL','phone':'+917058743721','agent_id':'IP346201','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SONAM NITIN CHAVHAN','phone':'+918010552489','agent_id':'IP221859','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ARJUN BAJIRAO MANTE','phone':'+919822544892','agent_id':'IP221884','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHIRISH VIJAY KARNIK','phone':'+919372601879','agent_id':'IP243978','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'HEMLATA SURYAKANT MALI','phone':'+919527487010','agent_id':'IP266566','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SWANAND RAVIKIRAN JOSHI','phone':'+919767903046','agent_id':'IP266689','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'OM KIRAN SANGLE','phone':'+918087192351','agent_id':'IP288458','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'YOGESH VINAYAK MAHAJAN','phone':'+918975877168','agent_id':'IP310047','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHAIKH FARHIN VASIM','phone':'+918484888030','agent_id':'IP188626','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VINITA SHRINIWAS JOSHI','phone':'+919850260680','agent_id':'IP211414','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRATHAMESH SANJAY KHARADE','phone':'+919322548945','agent_id':'IP211444','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DASHPUTE DHANANJAY RAMESH','phone':'+918380094062','agent_id':'IP255906','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DEORE BHARAT GANGADHAR','phone':'+918180802050','agent_id':'IP255953','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Aryan Tushar Bhusare','phone':'+919420485096','agent_id':'IP366663','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MAHESH KRUSHNA MOTHE','phone':'+919825328050','agent_id':'IP287684','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VICKY SHYAMRAO KALE','phone':'+919595097096','agent_id':'IP309391','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANDIP LAXIMAN DALVI','phone':'+919402183051','agent_id':'IP176691','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANJEEV JAGANNATH KHORE','phone':'+917774012242','agent_id':'IP177095','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Nilesh  Zade','phone':'+919420593999','agent_id':'IP243147','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANISHA RAMNATH SABALE','phone':'+919527855824','agent_id':'IP264846','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SUNITA PRAKASH KSHIRSAGAR','phone':'+919823739855','agent_id':'IP265096','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KOKATE MAYUR ASHOK','phone':'+919922303403','agent_id':'IP309012','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'OMKAR UMAKANT BAGUL','phone':'+919209928377','agent_id':'IP330991','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAHANE MANOJ BAJUNATH','phone':'+917264856051','agent_id':'IP206940','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SUYOG NAMDEV DIGHOLE','phone':'+919881012839','agent_id':'IP207113','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DATTATRAY G LASURE','phone':'+919923092637','agent_id':'IP229273','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'GHANSHYAM RAMESH DASHPUTE','phone':'+919822723857','agent_id':'IP251721','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRERANA SHUBHAM ASWARE','phone':'+917058753120','agent_id':'IP317896','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DALICHAND PARAKH','phone':'+919545804312','agent_id':'IP317964','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DHOTRE GIRISH KANTIRAJ','phone':'+917972391607','agent_id':'IP340338','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANGITA BHARAT MULANE','phone':'+919764358811','agent_id':'IP201878','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JAYASHRI BHIVAJI AHIRE','phone':'+918975396483','agent_id':'IP269238','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRAVIN EKNATH PAGARE','phone':'+917843054143','agent_id':'IP313128','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BAPUSAHEB HIRAMAN GAVLI','phone':'+919822490777','agent_id':'IP313338','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAVINDRA R KALKATTE','phone':'+919921286234','agent_id':'IP380263','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHAIKH MOIN AYUB','phone':'+918796738030','agent_id':'IP401732','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VINIT CHANDRASHEKHAR WAGHMARE','phone':'+919822669462','agent_id':'IP203106','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'CHAVAN JYOTI YOGESH','phone':'+917218876054','agent_id':'IP203620','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PUSHPA SANJAY SONAWANE','phone':'+919922231222','agent_id':'IP225227','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NILESH BHIKHA MUSALE','phone':'+918275138111','agent_id':'IP247972','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAHIL AMAN SINGH','phone':'+919766946512','agent_id':'IP247999','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'GAHIWAD YOGESH PANDURANG','phone':'+919850067228','agent_id':'IP269650','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHIVANI SWAPNIL JOSHI','phone':'+919689724799','agent_id':'IP336935','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANIL LAXMAN JADHAV','phone':'+918080232850','agent_id':'IP196513','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRADIP JANARDHAN KHAIRNAR','phone':'+919730369443','agent_id':'IP218965','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KAVITA RANJAN BIRARI','phone':'+919822820035','agent_id':'IP241277','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KOTHAWADE KISHOR VASANTRAO','phone':'+918551009333','agent_id':'IP395029','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Jayshri Vijay Pagare','phone':'+919921727007','agent_id':'IP201054','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Pritika Sachin Aher','phone':'+919404738587','agent_id':'IP246020','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JADHAV DEEPALI MUKTARAM','phone':'+919130021564','agent_id':'IP290461','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MODHE SACHIN DILIP','phone':'+919921232349','agent_id':'IP422858','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BEDARKAR DILIP CHANDRKANT','phone':'+919922322033','agent_id':'IP325272','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NIVRUTTI ANURUDDHA GHUGE','phone':'+919049596115','agent_id':'IP369458','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAMADHAN DATTATRAY AHER','phone':'+917020663301','agent_id':'IP279470','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRASHANT BABANRAO LONARI','phone':'+917720002093','agent_id':'IP279589','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'WAKALE SAVITA DEVIDAS','phone':'+918600059817','agent_id':'IP346112','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SURAJ BABURAO THOMBARE','phone':'+918788679876','agent_id':'IP348361','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHRIGOPALRAO VISHNUPANT','phone':'+918999148017','agent_id':'IP348609','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VAISHNAVI DHONDIRAM KHATALE','phone':'+917588172601','agent_id':'IP370726','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VARSHA SANJAY SHINDE','phone':'+918087330545','agent_id':'IP326894','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JANHAVI TUSHAR TAWARE','phone':'+919637475315','agent_id':'IP371568','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRITI KRUSHNANATH BELEKAR','phone':'+919309115821','agent_id':'IP350200','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ASHWINI KIRAN SHINDE','phone':'+919403926500','agent_id':'IP372023','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANISHA SUNIL SURYAWANSHI','phone':'+919763606193','agent_id':'IP350673','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'GAURAV SHIVAJI GHADWAJE','phone':'+917030465706','agent_id':'IP394203','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RADHAKISAN KARBHARI CHAUDHARI','phone':'+919422942902','agent_id':'IP374141','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'YASMIN ANWAR PINJARI','phone':'+918625853289','agent_id':'IP396070','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANJAY CHINTAMAN SAINDANE','phone':'+917249119995','agent_id':'IP375468','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'QAZI MANZOOR IMAMODDIN','phone':'+919689597847','agent_id':'IP375612','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NIKHIL MOHAN GAWALI','phone':'+919403117617','agent_id':'IP397447','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAKSHI SUNIL BHORASKAR','phone':'+919075878858','agent_id':'IP419520','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAKSHI PRAVIN CHAUDHARI','phone':'+919860319056','agent_id':'IP419795','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JANARDAN LOKADI RANKHAMB','phone':'+919527577156','agent_id':'IP376903','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'JEEVAN SAMADHAN AHIRE','phone':'+918675751999','agent_id':'IP267402','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANAV DIGAMBAR SONAKAMBALE','phone':'+919067167425','agent_id':'IP311143','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'AZAR SHAHABUDDIN SHAIKH','phone':'+919823677833','agent_id':'IP355277','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VAIBHAV DADA BORSE','phone':'+919270351601','agent_id':'IP399044','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DNYANESHWAR UDDHAVRAO GHATUL','phone':'+917030234240','agent_id':'IP399481','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANITA PANDURANG DANGRE','phone':'+919850172998','agent_id':'IP421502','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VITTHAL ANNA MALI','phone':'+919921987985','agent_id':'IP267809','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'BHANUPRIYA JADHAV','phone':'+919373339343','agent_id':'IP289757','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'OM SARASWATICHANDRA BORSE','phone':'+918830131990','agent_id':'IP378299','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PRACHI SHIVAJI JADHAV','phone':'+919529540481','agent_id':'IP335959','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RUPALI RAJENDRA DESHPANDE','phone':'+917304352555','agent_id':'IP400993','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MADHURI BALASAHEB FASATE','phone':'+918421919370','agent_id':'IP293347','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'DIPALI RAHUL SUMANT','phone':'+919225656001','agent_id':'IP337791','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANOHAR BHAGAWAN PATIL','phone':'+919890997204','agent_id':'IP359802','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KIRAN BALANATH AHIRE','phone':'+918805711703','agent_id':'IP403330','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Disha Shashikant pawar','phone':'+917020261629','agent_id':'IP316282','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VISHWAJIT RAMDAS SANGALE','phone':'+919767926831','agent_id':'IP339093','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MONAL YASHPAL RAJPUT','phone':'+919822813225','agent_id':'IP360358','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Shahrukh Shaizad Sajid Kaleem Ansari','phone':'+918888333564','agent_id':'IP360513','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'Abdul ahaad iftekhar shaikh','phone':'+917038204286','agent_id':'IP383709','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PATHAN SHAHEZAD KHAN AFSAR KHAN','phone':'+919307032121','agent_id':'IP319512','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SANDHYA RAHUL KOLI','phone':'+919370454233','agent_id':'IP319551','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ASHWINI KIRAN SHINDE','phone':'+919209769005','agent_id':'IP406844','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'MANOJ ARJUNDAS MANGARMALANI','phone':'+919225119578','agent_id':'IP407767','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'VAISHNAVI JANARDAN RANKHAMB','phone':'+917822069006','agent_id':'IP386706','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'NARENDRA S NIKUMBHE','phone':'+919823620334','agent_id':'IP408105','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANIKET BALU NIRBHAVANE','phone':'+918010342676','agent_id':'IP408412','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ASHOK PRALHAD BHISE','phone':'+919175937946','agent_id':'IP386356','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'KRUSHNA VASANT JADHAV','phone':'+917588103593','agent_id':'IP322818','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'PAWAN SURESH PATIL','phone':'+917420994235','agent_id':'IP322984','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SAYYED MUDASSARALI MAHEFUJALI','phone':'+918805636443','agent_id':'IP323029','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHRUNJAL BHAGWAN DEOGHARE','phone':'+919175500764','agent_id':'IP411700','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'RAJ ASHOK AHIRE','phone':'+918421023517','agent_id':'IP343939','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SHRADDHA ALANKAR WAGHMARE','phone':'+919422694669','agent_id':'IP365849','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'ANKUSH SHANTARAM DHAGE','phone':'+917588625986','agent_id':'IP366042','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'SADANAND MOTIRAM PANDAV','phone':'+917448285872','agent_id':'IP388171','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'CHAITALI MANOJ THORAT','phone':'+919823560031','agent_id':'IP388501','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
    {'name':'THORAT GANESH MANOJ','phone':'+919665181576','agent_id':'IP388504','city':'Nashik','language':'marathi','type':'MAIN_AGENT','parent_code':'','onboarding':'pending','remarks':''},
]
# 217 agents loaded from Excel — Nashik


# ── PRIYA SYSTEM ──────────────────────────────────────────────
PRIYA_SYSTEM = f"""Tu "Priya" aahes — Prashant Chandratre ji chi Personal AI Insurance Sales Assistant.

IDENTITY: Naam Priya | 4 saal insurance experience | Hindi+Marathi fluent
Prashant Chandratre ji chi AI — unchi taraf ne baat karti hai

SALES FLOW (ek ek step):
1. "Aaj koi business hai? Customer ready hai?"
2. "Car hai ki Bike?" 
3. "Policy: Comprehensive / Third Party / Zero Dep?"
4. "RC photo WhatsApp karo {PRASHANT['phone']} pe. Ya reg number batao."
5. "Purani policy? Claim tha pichle saal?" (NCB ke liye)
6. "Customer ka naam aur mobile?"
7. "Main quotation nikal kar WhatsApp karti hoon — 2 minute!"

ONBOARDING CHECK: Agar agent ka onboarding pending hai to poochho:
"Documents submit ho gaye? Google form fill kiya? Koi help chahiye onboarding mein?"

PERSONALITY: Warm, persistent, professional. 2-3 sentences max.
LANGUAGE: Agent ki language detect karke jawab do.
TRANSFER: "Prashant ji se baat" sune to call transfer karo.

PB KNOWLEDGE: Motor/Bike/Health/Life process, NCB, Zero Dep, IDV,
Commission 15-25%, KYC process, Payment link, Renewal tracking."""

# ── HELPERS ───────────────────────────────────────────────────
def detect_lang(text):
    if not text: return 'hindi'
    m_words = ['आहे','नाही','करा','मला','तुम्ही','aahe','nahi','kara','mala','tumhi',
               'cha','chi','la','tar','pan','kay','kase','zala','nako','kiti','aaj']
    return 'marathi' if sum(1 for w in m_words if w in text.lower())>=1 else 'hindi'

def greet(name, lang):
    h=datetime.now().hour; fn=name.split()[0].title()
    if lang=='marathi':
        t='सुप्रभात' if h<12 else ('नमस्ते' if h<17 else 'शुभ संध्या')
        return f"{t} {fn} जी! मी प्रिया, Prashant जींची AI assistant."
    t='Good morning' if h<12 else ('Namaste' if h<17 else 'Good evening')
    return f"{t} {fn} ji! Main Priya, Prashant Chandratre ji ki AI assistant."

def find_agent(phone):
    clean=phone.replace('+91','').replace('+','').strip()[-10:]
    return next((a for a in cached_contacts if a['phone'].replace('+91','').strip()[-10:]==clean),None)

def get_parent(agent):
    if agent and agent.get('parent_code'):
        return next((a for a in cached_contacts if a['agent_id']==agent['parent_code']),None)
    return None

def is_calling_hours():
    h=datetime.now().hour
    return 10<=h<18

def calling_blocked(lang='hindi'):
    now=datetime.now()
    if lang=='marathi':
        return jsonify({"error":"Priya fakt 10 AM - 6 PM mein outgoing calls karte.",
                       "current":now.strftime("%I:%M %p"),"allowed":"10:00 AM — 6:00 PM"}),403
    return jsonify({"error":"Priya only calls 10 AM - 6 PM. Incoming 24/7 active.",
                   "current":now.strftime("%I:%M %p"),"allowed":"10:00 AM — 6:00 PM"}),403

def reset_daily():
    global today_biz
    if today_biz['date']!=str(date.today()):
        today_biz={'date':str(date.today()),'total_premium':0,'total_policies':0,
                  'target':DAILY_TARGET,'agents_called':[],'agents_reported':[],
                  'agent_data':{},'urgent_agents':[],'projected':0}

def update_biz(aid,aname,premium,policies,ptypes,pending,notes):
    reset_daily()
    today_biz['agent_data'][aid]={'name':aname,'premium':premium,'policies':policies,
        'policy_types':ptypes,'pending':pending,'notes':notes,'time':datetime.now().strftime("%H:%M")}
    if aid not in today_biz['agents_reported']: today_biz['agents_reported'].append(aid)
    today_biz['total_premium']=sum(v['premium'] for v in today_biz['agent_data'].values())
    today_biz['total_policies']=sum(v['policies'] for v in today_biz['agent_data'].values())
    r=len(today_biz['agents_reported'])
    if r>0: today_biz['projected']=int((today_biz['total_premium']/r)*len(cached_contacts))

def do_transfer(lang):
    msg="थांबा, Prashant जींशी connect करते..." if lang=='marathi' else "Ek second, Prashant ji se connect karti hoon..."
    resp=VoiceResponse()
    resp.say(msg,voice='Polly.Aditi',language='hi-IN')
    d=Dial(caller_id=TWILIO_FROM_NUMBER,timeout=30); d.number(PRASHANT_NUMBER); resp.append(d)
    no="उपलब्ध नाहीत. Message पाठवते." if lang=='marathi' else "Available nahi. Message karungi."
    resp.say(no,voice='Polly.Aditi',language='hi-IN')
    return Response(str(resp),mimetype='text/xml')

# ── WHATSAPP ──────────────────────────────────────────────────
def send_wa(phone, msg):
    if not phone: return False
    if not phone.startswith('+'): phone='+91'+phone.replace('+91','')
    if INTERAKT_KEY:
        try:
            r=requests.post("https://api.interakt.ai/v1/public/message/",
                json={"fullPhoneNumber":phone,"callbackData":"priya","type":"Text","data":{"message":msg}},
                headers={"Authorization":f"Basic {INTERAKT_KEY}","Content-Type":"application/json"},timeout=10)
            if r.status_code in [200,201]: return True
        except: pass
    try:
        if twilio_client:
            twilio_client.messages.create(body=msg[:1600],from_=TWILIO_FROM_NUMBER,to=phone)
            return True
    except Exception as e:
        print(f"WA/SMS err: {e}")
    return False

def wa_p(msg): return send_wa(PRASHANT_WA,msg)

# ── QUOTATION ─────────────────────────────────────────────────
def calc_quote(vtype,ptype,year,idv=None,ncb_years=0,has_claim=False):
    age=datetime.now().year-int(year) if year else 3
    is_car=vtype.lower() in ['car','motor']
    if not idv: idv=max(100000,500000-(age*50000)) if is_car else max(30000,100000-(age*10000))
    idv=int(idv)
    od=int(idv*(0.035 if is_car else 0.03))
    tp=(3416 if idv>300000 else 2094) if is_car else (1854 if idv>75000 else 1366)
    ncb_d={0:0,1:20,2:25,3:35,4:45,5:50}.get(min(ncb_years,5),0)
    nd=int(od*ncb_d/100) if not has_claim else 0
    pt=ptype.lower()
    if 'third' in pt or pt=='tp':
        g=int(tp*0.18); return {'policy_type':'Third Party Only','tp_premium':tp,'gst_18pct':g,'total_premium':tp+g,'idv':idv}
    elif 'zero' in pt:
        zd=int(idv*0.015); net=od-nd+tp+zd; g=int(net*0.18)
        return {'policy_type':'Zero Depreciation','idv':idv,'od_premium':od,'tp_premium':tp,'ncb_discount':nd,'zd_premium':zd,'net_premium':net,'gst_18pct':g,'total_premium':net+g}
    else:
        net=od-nd+tp; g=int(net*0.18); zd=int(idv*0.015)
        return {'policy_type':'Comprehensive','idv':idv,'od_premium':od,'tp_premium':tp,'ncb_discount':nd,'net_premium':net,'gst_18pct':g,'total_premium':net+g,'with_zero_dep':net+zd+int((net+zd)*0.18)}

def quote_msg(aname,cname,reg,vtype,q,lang='marathi'):
    fn=aname.split()[0].title() if aname else 'Agent'; total=q.get('total_premium',0)
    hdr=f"🚗 *INSURANCE QUOTATION*\n━━━━━━━━━━━━━━━━━━━━\n👤 *{'Agent' if lang!='marathi' else 'Agent'}:* {fn} {'जी' if lang=='marathi' else 'ji'}\n👤 *Customer:* {cname or 'N/A'}\n🚗 *Vehicle:* {vtype or ''} {reg or ''}\n📋 *Policy:* {q.get('policy_type','')}\n━━━━━━━━━━━━━━━━━━━━\n"
    if q.get('idv'):          hdr+=f"💰 IDV: ₹{q['idv']:,}\n"
    if q.get('od_premium'):   hdr+=f"📊 OD: ₹{q['od_premium']:,}\n"
    if q.get('tp_premium'):   hdr+=f"⚖️ TP: ₹{q['tp_premium']:,}\n"
    if q.get('ncb_discount'): hdr+=f"✅ NCB: -₹{q['ncb_discount']:,}\n"
    if q.get('zd_premium'):   hdr+=f"🛡️ Zero Dep: ₹{q['zd_premium']:,}\n"
    hdr+=f"━━━━━━━━━━━━━━━━━━━━\n💳 GST 18%: ₹{q.get('gst_18pct',0):,}\n💰 *TOTAL: ₹{total:,}*\n━━━━━━━━━━━━━━━━━━━━\n🤖 Priya AI | Prashant Chandratre\n✅ PB Partners pe generate karo"
    if q.get('with_zero_dep'): hdr+=f"\n💡 Zero Dep ke saath: ₹{q['with_zero_dep']:,}"
    return hdr

# ── AI RESPONSE ───────────────────────────────────────────────
def priya_reply(user_msg, agent, call_sid, lang, ctype='sales'):
    try:
        if call_sid not in conversations: conversations[call_sid]=[]
        conversations[call_sid].append({"role":"user","content":user_msg})
        aname=agent['name'] if agent else 'Agent'
        aid=agent['agent_id'] if agent else ''
        onb=agent.get('onboarding','') if agent else ''
        rem=agent.get('remarks','') if agent else ''
        li=lang=='marathi'
        
        # Onboarding context
        onb_ctx=""
        if onb in ['pending','']:
            onb_ctx="\nIMPORTANT: Is agent ka onboarding PENDING hai. Zaroor poochho:\n- Documents submit ho gaye?\n- Google form fill kiya?\n- Koi help chahiye?" if not li else "\nIMPORTANT: Ya agent cha onboarding PENDING aahe. Zaroor vicharaa:\n- Documents submit zale?\n- Google form fill kela?\n- Kahi madad havi?"
        
        pending=pending_cases.get(aid,{})
        p_info=f"\nCase pending: {json.dumps(pending,ensure_ascii=False)}" if pending else ""
        
        if ctype=='sales':
            goal=f"SALES: Step by step collect karo — vehicle>policy>RC>old policy+claim>customer name+mobile{p_info}{onb_ctx}\nSab ho to: 'Quotation nikal kar WhatsApp karti hoon!'"
        else:
            goal="BUSINESS: Aaj ki policies, premium, koi problem?"
        
        system=f"{PRIYA_SYSTEM}\nCURRENT: {aname} ({aid})\nRemarks: {rem or 'None'}\n{goal}\n{'MARATHI madhe jawab de.' if li else 'HINDI mein jawab de.'}\n2-3 sentences max."
        
        resp=openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},*conversations[call_sid][-8:]],
            max_tokens=150,temperature=0.75)
        reply=resp.choices[0].message.content.strip()
        conversations[call_sid].append({"role":"assistant","content":reply})
        
        # Extract + auto-process
        _extract(aid,aname,conversations[call_sid],ctype,agent)
        
        # Profile update
        if aid:
            if aid not in agent_profiles: agent_profiles[aid]={'name':aname,'interactions':0,'last_call':'','lang':lang}
            agent_profiles[aid]['interactions']+=1
            agent_profiles[aid]['last_call']=datetime.now().strftime("%d/%m %H:%M")
        
        if len(user_msg)>10:
            daily_knowledge.append(f"{aname}: {user_msg[:80]}")
            if len(daily_knowledge)>200: daily_knowledge.pop(0)
        
        transfer=any(w in user_msg.lower() for w in ['prashant','transfer','manager','प्रशांत'])
        return reply, transfer
    except Exception as e:
        print(f"AI err: {e}")
        fb="माफ करा, technical अडचण." if lang=='marathi' else "Maafi, technical issue."
        return fb, False

def _extract(aid,aname,conv,ctype,agent_obj):
    try:
        if len(conv)<2: return
        ct="\n".join([f"{m['role']}: {m['content']}" for m in conv[-6:]])
        if ctype=='sales':
            pr=f"""Extract insurance details. ONLY JSON:
{{"vehicle_type":"Car/Bike/empty","reg_number":"or empty","policy_type":"Comprehensive/ThirdParty/ZeroDep/empty","customer_name":"or empty","customer_mobile":"10digit or empty","vehicle_year":"or empty","has_claim":false,"ncb_years":0,"idv":0,"ready_for_quote":false}}
Conversation:\n{ct}"""
        else:
            pr=f"""Extract business data. ONLY JSON:
{{"policies":0,"premium":0,"policy_types":"","pending":"","needs_help":false,"urgent":false}}
Conversation:\n{ct}"""
        r=openai.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role":"user","content":pr}],max_tokens=180,temperature=0)
        raw=r.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        data=json.loads(raw)
        if ctype=='sales':
            if aid not in pending_cases: pending_cases[aid]={}
            for k,v in data.items():
                if v and v!=0 and v!='empty' and v!='': pending_cases[aid][k]=v
            if data.get('ready_for_quote') and data.get('vehicle_type') and data.get('policy_type'):
                c=pending_cases[aid]
                q=calc_quote(c.get('vehicle_type','car'),c.get('policy_type','comprehensive'),
                    c.get('vehicle_year',datetime.now().year-3),c.get('idv'),c.get('ncb_years',0),c.get('has_claim',False))
                if agent_obj:
                    lang=agent_obj.get('language','marathi')
                    m=quote_msg(agent_obj['name'],c.get('customer_name',''),c.get('reg_number',''),c.get('vehicle_type',''),q,lang)
                    send_wa(agent_obj['phone'],m)
                    wa_p(f"📋 NEW LEAD\n{agent_obj['name']}\n{c.get('customer_name','N/A')} | {c.get('customer_mobile','N/A')}\n{c.get('vehicle_type','')} {c.get('reg_number','')}\n₹{q.get('total_premium',0):,}")
                    active_leads[f"{aid}_{datetime.now().strftime('%H%M')}"]={'agent_id':aid,'agent_name':agent_obj['name'],'case':c,'quotation':q,'time':datetime.now().strftime("%H:%M"),'date':str(date.today())}
                    pending_cases[aid]={}
        else:
            if data.get('policies',0)>0 or data.get('premium',0)>0:
                update_biz(aid,aname,data.get('premium',0),data.get('policies',0),data.get('policy_types',''),data.get('pending',''),'')
            if data.get('urgent') or data.get('needs_help'):
                if aid not in today_biz['urgent_agents']:
                    today_biz['urgent_agents'].append(aid)
                    wa_p(f"🚨 URGENT\n{aname} ko help chahiye!\nAbhi call karo!")
    except Exception as e:
        print(f"Extract err: {e}")

# ── CALL ROUTES ───────────────────────────────────────────────
@app.route('/incoming-call',methods=['POST'])
def incoming_call():
    caller=request.form.get('From',''); call_sid=request.form.get('CallSid','')
    agent=find_agent(caller)
    if agent:
        lang=agent.get('language','hindi'); name=agent['name']; aid=agent['agent_id']
        parent=get_parent(agent); pm=''
        if parent:
            pn=parent['name'].split()[0].title()
            pm=f" तुम्ही {pn} जींच्या team मध्ये." if lang=='marathi' else f" Aap {pn} ji ki team mein."
        onb=agent.get('onboarding','pending')
        if onb in ['pending','']:
            onb_hint=" Onboarding baaki hai — documents baare mein bhi baat karein." if lang=='hindi' else " Onboarding baaki aahe — documents baaddal bhi bolaa."
        else:
            onb_hint=""
    else:
        lang='hindi'; name='Agent'; aid=''; pm=''; onb_hint=''
    
    g=greet(name,lang)
    if lang=='marathi':
        intro=f"{g}{pm} Prashant जींनी पाठवले.{onb_hint} आज कोणता business आहे? Customer ready असेल तर details द्या — quotation काढते!"
    else:
        intro=f"{g}{pm} Prashant ji ne bheja hai.{onb_hint} Aaj koi business hai? Customer ready ho toh details do — quotation nikalungi!"
    
    print(f"📞 Incoming: {caller} — {name} — {lang}")
    resp=VoiceResponse()
    g2=Gather(input='speech',language='hi-IN',speech_timeout='auto',
              action=f'/handle-speech?aid={aid}&caller={caller}&lang={lang}&type=sales',method='POST')
    g2.say(intro,voice='Polly.Aditi',language='hi-IN'); resp.append(g2)
    resp.say("Response nahi mila." if lang=='hindi' else "Response mila nahi.",voice='Polly.Aditi',language='hi-IN')
    return Response(str(resp),mimetype='text/xml')

@app.route('/handle-speech',methods=['POST'])
def handle_speech():
    speech=request.form.get('SpeechResult','')
    aid=request.args.get('aid',''); caller=request.args.get('caller','')
    lang=request.args.get('lang','hindi'); ctype=request.args.get('type','sales')
    call_sid=request.form.get('CallSid','')
    if not speech:
        resp=VoiceResponse()
        g2=Gather(input='speech',language='hi-IN',speech_timeout='auto',
                 action=f'/handle-speech?aid={aid}&caller={caller}&lang={lang}&type={ctype}',method='POST')
        g2.say("Samajh nahi aaya, phir bolein." if lang=='hindi' else "Samajhle nahi, parat sanga.",voice='Polly.Aditi',language='hi-IN')
        resp.append(g2); return Response(str(resp),mimetype='text/xml')
    detected=detect_lang(speech)
    if detected!=lang: lang=detected
    agent=next((a for a in cached_contacts if a['agent_id']==aid),None)
    if any(w in speech.lower() for w in ['prashant','transfer','manager','प्रशांत']):
        return do_transfer(lang)
    ai_reply,need_tr=priya_reply(speech,agent,call_sid,lang,ctype)
    if need_tr: return do_transfer(lang)
    resp=VoiceResponse()
    g2=Gather(input='speech',language='hi-IN',speech_timeout='auto',
             action=f'/handle-speech?aid={aid}&caller={caller}&lang={lang}&type={ctype}',method='POST')
    g2.say(ai_reply,voice='Polly.Aditi',language='hi-IN'); resp.append(g2)
    return Response(str(resp),mimetype='text/xml')

@app.route('/call-status',methods=['POST'])
def call_status():
    print(f"📊 {request.form.get('To')}: {request.form.get('CallStatus')}"); return '',200

# ── OUTGOING CALLS (10AM-6PM ONLY) ───────────────────────────
def make_outgoing(phone,msg):
    if not twilio_client: return None
    try:
        return twilio_client.calls.create(to=phone,from_=TWILIO_FROM_NUMBER,
            twiml=f'<Response><Say voice="Polly.Aditi" language="hi-IN">{msg}</Say></Response>')
    except Exception as e:
        print(f"Call err: {e}"); return None

@app.route('/make-call',methods=['POST'])
def make_call():
    data=request.json or {}; phone=str(data.get('phone','')); name=data.get('name','Agent'); lang=data.get('language','hindi')
    if not is_calling_hours(): return calling_blocked(lang)
    if len(phone)==10: phone='+91'+phone
    fn=name.split()[0].title()
    msg=data.get('message',f"{'नमस्ते '+fn+' जी! मी प्रिया.' if lang=='marathi' else 'Namaste '+fn+' ji! Main Priya.'}")
    c=make_outgoing(phone,msg)
    return jsonify({'success':bool(c),'call_sid':c.sid if c else None})

@app.route('/daily-collection',methods=['POST'])
def daily_collection():
    data=request.json or {}
    if not is_calling_hours(): return calling_blocked()
    limit=int(data.get('limit',len(cached_contacts))); reset_daily(); results=[]
    for agent in cached_contacts[:limit]:
        lang=agent.get('language','marathi'); fn=agent['name'].split()[0].title()
        onb=agent.get('onboarding','pending')
        if lang=='marathi':
            if onb in ['pending','']:
                msg=f"नमस्ते {fn} जी! मी प्रिया. Prashant जींनी पाठवले. आज business आहे का? आणि onboarding documents submit झाले का?"
            else:
                msg=f"नमस्ते {fn} जी! मी प्रिया. आज कोणता business आहे? Customer ready असेल तर details द्या!"
        else:
            if onb in ['pending','']:
                msg=f"Namaste {fn} ji! Main Priya. Prashant ji ne bheja. Aaj business hai? Aur onboarding documents submit ho gaye?"
            else:
                msg=f"Namaste {fn} ji! Main Priya. Aaj koi business hai? Customer ready ho toh details do!"
        try:
            c=twilio_client.calls.create(to=agent['phone'],from_=TWILIO_FROM_NUMBER,
                url=f"https://{request.host}/biz-handler?aid={agent['agent_id']}&lang={lang}&name={fn}",method='POST')
            today_biz['agents_called'].append(agent['agent_id'])
            results.append({'agent':agent['name'],'status':'calling','sid':c.sid})
        except Exception as e:
            results.append({'agent':agent['name'],'status':'failed','error':str(e)})
    return jsonify({'success':True,'called':len([r for r in results if r['status']=='calling']),'results':results})

@app.route('/biz-handler',methods=['POST'])
def biz_handler():
    aid=request.args.get('aid',''); lang=request.args.get('lang','marathi'); name=request.args.get('name','Agent')
    agent=next((a for a in cached_contacts if a['agent_id']==aid),None)
    onb=agent.get('onboarding','pending') if agent else 'pending'
    if lang=='marathi':
        if onb in ['pending','']:
            intro=f"नमस्ते {name} जी! मी प्रिया. आज business काय आहे? आणि तुमचे onboarding documents — Aadhaar, PAN, bank details — submit झाले का?"
        else:
            intro=f"नमस्ते {name} जी! मी प्रिया. आज कोणता business आहे? Car, bike, health — customer असेल तर RC details द्या!"
    else:
        if onb in ['pending','']:
            intro=f"Namaste {name} ji! Main Priya. Aaj ka business kya hai? Aur aapke onboarding documents — Aadhaar, PAN, bank — submit ho gaye?"
        else:
            intro=f"Namaste {name} ji! Main Priya. Aaj koi business hai? Car, bike, health — customer ho toh RC details do!"
    resp=VoiceResponse()
    g2=Gather(input='speech',language='hi-IN',speech_timeout='auto',
             action=f'/handle-speech?aid={aid}&caller=&lang={lang}&type=sales',method='POST')
    g2.say(intro,voice='Polly.Aditi',language='hi-IN'); resp.append(g2)
    resp.say("Update nahi mila.",voice='Polly.Aditi',language='hi-IN')
    return Response(str(resp),mimetype='text/xml')

@app.route('/welcome-call',methods=['POST'])
def welcome_call():
    data=request.json or {}; phone=str(data.get('phone','')); name=data.get('name','Agent')
    lang=data.get('language','marathi'); aid=data.get('agent_id','')
    if not is_calling_hours(): return calling_blocked(lang)
    if len(phone)==10: phone='+91'+phone
    fn=name.split()[0].title()
    if lang=='marathi':
        msg=f"नमस्ते {fn} जी! PB Partners मध्ये स्वागत! मी प्रिया. Code: {aid}. App download करा. Documents — Aadhaar, PAN, bank details, selfie — WhatsApp करा {PRASHANT['phone']} वर. मदत लागली तर call करा!"
    else:
        msg=f"Namaste {fn} ji! PB Partners mein swagat! Main Priya. Code: {aid}. App download karein. Documents — Aadhaar, PAN, bank, selfie — WhatsApp karein {PRASHANT['phone']} pe. Help chahiye toh call karein!"
    c=make_outgoing(phone,msg)
    wa_msg=f"🎉 *PB Partners Welcome!*\nCode: *{aid}*\n\n📋 Documents bhejein:\n🪪 PAN Card\n🪪 Aadhaar (Front+Back)\n🏦 Bank (Cheque/Passbook)\n📄 10th Certificate\n📱 Mobile (Aadhaar linked)\n📧 Email\n🤳 Selfie\n\nWhatsApp: {PRASHANT['wa']}\n— Prashant ji"
    send_wa(phone,wa_msg)
    # Update onboarding status
    for a in cached_contacts:
        if a['phone'].replace('+91','')[-10:]==phone.replace('+91','')[-10:]:
            a['onboarding']='welcome_done'; break
    return jsonify({'success':True,'call':c.sid if c else None,'wa_sent':True})

@app.route('/recruitment-call',methods=['POST'])
def recruitment_call():
    data=request.json or {}; phone=str(data.get('phone','')); name=data.get('name','ji')
    lang=data.get('language','hindi')
    if not is_calling_hours(): return calling_blocked(lang)
    if len(phone)==10: phone='+91'+phone
    fn=name.split()[0].title() if name!='ji' else 'ji'
    if lang=='marathi':
        msg=f"नमस्ते {fn} जी! मी प्रिया, Prashant Chandratre जींच्या वतीने. PB Partners सोबत insurance agent व्हा. 100% free. Free training. चांगले commission. Interest आहे का?"
    else:
        msg=f"Namaste {fn} ji! Main Priya, Prashant Chandratre ji ki taraf se. PB Partners ke saath agent banein. 100% free. Free training. Achha commission. Interested hain?"
    c=make_outgoing(phone,msg)
    # WhatsApp with full details
    if lang=='marathi':
        wa=f"🙏 नमस्ते {fn} जी!\n\nमी प्रिया, {PRASHANT['name']} जींची AI.\n\n🚀 *PB Partners मध्ये join करा!*\n✅ 100% FREE\n✅ Free Training\n✅ Motor 15-20% commission\n✅ Health 20-25% commission\n\n📋 *Documents:*\n🪪 PAN, 🪪 Aadhaar, 🏦 Bank, 📄 10th, 📱 Mobile, 📧 Email, 🤳 Selfie\n\n📞 {PRASHANT['phone']}\n💬 {PRASHANT['wa']}\n\n_{PRASHANT['note']}_"
    else:
        wa=f"🙏 Namaste {fn} ji!\n\nMain Priya, {PRASHANT['name']} ji ki AI.\n\n🚀 *PB Partners mein join karein!*\n✅ 100% FREE\n✅ Free Training\n✅ Motor 15-20% commission\n✅ Health 20-25% commission\n\n📋 *Documents:*\n🪪 PAN, 🪪 Aadhaar, 🏦 Bank, 📄 10th, 📱 Mobile, 📧 Email, 🤳 Selfie\n\n📞 {PRASHANT['phone']}\n💬 {PRASHANT['wa']}\n\n_{PRASHANT['note']}_"
    send_wa(phone,wa)
    new_prospects[phone]={'name':name,'phone':phone,'lang':lang,'status':'contacted','docs':[],'date':str(date.today())}
    wa_p(f"🎯 NEW PROSPECT\n{name} | {phone}\nWA sent ✅")
    return jsonify({'success':True,'call':c.sid if c else None,'wa_sent':True})

@app.route('/reminder-call',methods=['POST'])
def reminder_call():
    data=request.json or {}; phone=str(data.get('phone','')); name=data.get('name','Agent'); lang=data.get('language','marathi')
    if not is_calling_hours(): return calling_blocked(lang)
    if len(phone)==10: phone='+91'+phone
    fn=name.split()[0].title(); h=datetime.now().hour
    # Dark psychology — FOMO + loss aversion
    pressure=random.choice(["Aaj kai agents ne target hit kiya!","Customer wait kar raha hai!","Month end aa raha hai!"])
    if lang=='marathi':
        t='सुप्रभात' if h<12 else ('नमस्ते' if h<17 else 'शुभ संध्या')
        msg=f"{t} {fn} जी! मी प्रिया. {pressure} आज business आहे का? Customer असेल तर details द्या — quotation काढते!"
    else:
        t='Good morning' if h<12 else ('Namaste' if h<17 else 'Good evening')
        msg=f"{t} {fn} ji! Main Priya. {pressure} Aaj business hai? Customer ho toh details do — quotation nikalungi!"
    c=make_outgoing(phone,msg)
    return jsonify({'success':True,'call':c.sid if c else None})

@app.route('/call-all',methods=['POST'])
def call_all():
    data=request.json or {}; limit=int(data.get('limit',5))
    if not is_calling_hours(): return calling_blocked()
    results=[]
    for agent in cached_contacts[:limit]:
        lang=agent.get('language','marathi'); fn=agent['name'].split()[0].title()
        pressure=random.choice(["Aaj kai agents ne business dila!","Month end hai!","Target miss mat karo!"])
        if lang=='marathi':
            msg=data.get('message',f"नमस्ते {fn} जी! मी प्रिया. {pressure} आज business द्या — quotation काढते!")
        else:
            msg=data.get('message',f"Namaste {fn} ji! Main Priya. {pressure} Aaj business do — quotation nikalungi!")
        c=make_outgoing(agent['phone'],msg)
        results.append({'agent':agent['name'],'status':'called' if c else 'failed'})
    return jsonify({'success':True,'called':len([r for r in results if r['status']=='called']),'results':results})

@app.route('/alert-prashant',methods=['POST'])
def alert_prashant():
    data=request.json or {}; msg=data.get('message','🚨 URGENT from Priya AI')
    aid=data.get('agent_id','')
    agent=next((a for a in cached_contacts if a['agent_id']==aid),None)
    if agent and not data.get('message'): msg=f"🚨 URGENT\n{agent['name']} ko help chahiye!\n{agent['phone']}\nAbhi call karo!"
    sent=wa_p(msg)
    c=make_outgoing(PRASHANT_NUMBER,"Namaste Prashant ji! Priya bol rahi hoon. Urgent matter hai. WhatsApp check karein please.")
    return jsonify({'success':True,'wa_sent':sent,'call':c.sid if c else None})

# ── QUOTE ROUTES ──────────────────────────────────────────────
@app.route('/quote-request',methods=['POST'])
def quote_request():
    data=request.json or {}; aid=data.get('agent_id','')
    agent=next((a for a in cached_contacts if a['agent_id']==aid),None)
    q=calc_quote(data.get('vehicle_type','car'),data.get('policy_type','comprehensive'),
        data.get('year',datetime.now().year-3),data.get('idv'),data.get('ncb_years',0),data.get('has_claim',False))
    wa_sent=False
    if agent:
        lang=agent.get('language','marathi')
        m=quote_msg(agent['name'],data.get('customer_name',''),data.get('reg_number',''),data.get('vehicle_type',''),q,lang)
        wa_sent=send_wa(agent['phone'],m)
        wa_p(f"📋 QUOTE\n{agent['name']}\n{data.get('customer_name','N/A')} | {data.get('customer_mobile','N/A')}\n{data.get('vehicle_type','')} {data.get('reg_number','')}\n₹{q.get('total_premium',0):,}")
        active_leads[f"{aid}_{datetime.now().strftime('%H%M')}"]={'agent_id':aid,'agent_name':agent['name'],'case':data,'quotation':q,'time':datetime.now().strftime("%H:%M"),'date':str(date.today())}
    return jsonify({'success':True,'quotation':q,'wa_sent':wa_sent,'agent':agent['name'] if agent else 'Unknown'})

@app.route('/quote-form',methods=['GET'])
def quote_form():
    opts=''.join([f'<option value="{a["agent_id"]}">{a["name"].split()[0].title()} ({a["agent_id"]})</option>' for a in cached_contacts])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Priya — Quote</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:Arial;background:#0d0d0d;color:#F0F0F0;padding:20px;}}
h1{{color:#E8521A;margin-bottom:4px;font-size:20px;}}.sub{{color:#909090;font-size:13px;margin-bottom:18px;}}
.card{{background:#1c1c1c;border:1px solid rgba(232,82,26,.2);border-radius:14px;padding:16px;margin-bottom:12px;}}
.ct{{font-size:10px;font-weight:700;color:#E8521A;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;}}
.f2{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}.fr{{margin-bottom:10px;}}
label{{display:block;font-size:11px;color:#909090;margin-bottom:4px;}}
input,select{{width:100%;background:#252525;border:1px solid rgba(255,255,255,.1);border-radius:9px;padding:10px 12px;color:#F0F0F0;font-size:14px;outline:none;}}
input:focus,select:focus{{border-color:#E8521A;}}.btn{{width:100%;background:#E8521A;border:none;border-radius:12px;padding:14px;color:#fff;font-size:15px;font-weight:800;cursor:pointer;margin-bottom:12px;}}
.result{{background:rgba(0,200,83,.08);border:1px solid rgba(0,200,83,.3);border-radius:12px;padding:16px;display:none;}}
.rt{{color:#00C853;font-weight:800;margin-bottom:10px;}}.rr{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px;}}
.rr:last-child{{border:none;}}.rv{{font-weight:700;color:#00C853;}}.big{{font-size:32px;font-weight:900;color:#00C853;text-align:center;margin:10px 0;}}
</style></head><body>
<h1>🤖 Priya — Quote Generator</h1><p class="sub">Prashant Chandratre ji | Insurance Quotation</p>
<div class="card"><div class="ct">👤 Agent & Customer</div>
<div class="fr"><label>Agent</label><select id="ai">{opts}</select></div>
<div class="f2"><div class="fr"><label>Customer Name</label><input id="cn" placeholder="Rahul Kumar"></div>
<div class="fr"><label>Mobile</label><input id="cm" type="tel" placeholder="9876543210"></div></div></div>
<div class="card"><div class="ct">🚗 Vehicle</div>
<div class="f2"><div class="fr"><label>Type</label><select id="vt"><option value="Car">🚗 Car</option><option value="Bike">🏍️ Bike</option></select></div>
<div class="fr"><label>Year</label><input id="vy" type="number" placeholder="2020"></div></div>
<div class="fr"><label>Registration No</label><input id="rn" placeholder="MH01AB1234" oninput="this.value=this.value.toUpperCase()"></div>
<div class="fr"><label>IDV (optional)</label><input id="idv" type="number" placeholder="Auto calculate"></div></div>
<div class="card"><div class="ct">📋 Policy</div>
<div class="fr"><label>Policy Type</label><select id="pt"><option value="Comprehensive">Comprehensive (First Party)</option><option value="ZeroDep">Zero Depreciation (Best)</option><option value="ThirdParty">Third Party Only</option></select></div>
<div class="f2"><div class="fr"><label>NCB Years</label><select id="nc"><option value="0">0 (New/Claim)</option><option value="1">1yr 20% off</option><option value="2">2yr 25% off</option><option value="3">3yr 35% off</option><option value="4">4yr 45% off</option><option value="5">5yr 50% off</option></select></div>
<div class="fr"><label>Claim Last Year?</label><select id="cl"><option value="false">❌ No (NCB milega)</option><option value="true">✅ Yes</option></select></div></div></div>
<button class="btn" onclick="gen()">🚀 Generate + WhatsApp</button>
<div class="result" id="res"><div class="rt" id="rt">💰 Quotation</div><div id="rows"></div><div class="big" id="total">₹0</div><div style="text-align:center;font-size:12px;color:#909090;" id="st">Processing...</div></div>
<script>async function gen(){{const b=document.querySelector('.btn');b.textContent='⏳...';b.disabled=true;
try{{const r=await fetch('/quote-request',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:document.getElementById('ai').value,vehicle_type:document.getElementById('vt').value,policy_type:document.getElementById('pt').value,year:parseInt(document.getElementById('vy').value)||2020,reg_number:document.getElementById('rn').value,customer_name:document.getElementById('cn').value,customer_mobile:document.getElementById('cm').value,ncb_years:parseInt(document.getElementById('nc').value),has_claim:document.getElementById('cl').value==='true',idv:parseInt(document.getElementById('idv').value)||0}})}});
const d=await r.json();const q=d.quotation;document.getElementById('rt').textContent='💰 '+q.policy_type;
let rows='';if(q.idv)rows+=`<div class="rr"><span>IDV</span><span class="rv">₹${{q.idv.toLocaleString('en-IN')}}</span></div>`;
if(q.od_premium)rows+=`<div class="rr"><span>OD</span><span>₹${{q.od_premium.toLocaleString('en-IN')}}</span></div>`;
if(q.tp_premium)rows+=`<div class="rr"><span>TP</span><span>₹${{q.tp_premium.toLocaleString('en-IN')}}</span></div>`;
if(q.ncb_discount)rows+=`<div class="rr"><span>NCB Discount</span><span style="color:#00C853;">-₹${{q.ncb_discount.toLocaleString('en-IN')}}</span></div>`;
if(q.gst_18pct)rows+=`<div class="rr"><span>GST 18%</span><span>₹${{q.gst_18pct.toLocaleString('en-IN')}}</span></div>`;
if(q.with_zero_dep)rows+=`<div class="rr"><span>💡 With Zero Dep</span><span>₹${{q.with_zero_dep.toLocaleString('en-IN')}}</span></div>`;
document.getElementById('rows').innerHTML=rows;document.getElementById('total').textContent='₹'+q.total_premium.toLocaleString('en-IN');
document.getElementById('st').textContent=d.wa_sent?'✅ WhatsApp sent!':'⚠️ Quote ready (send manually)';document.getElementById('res').style.display='block';
}}catch(e){{alert('Error: '+e.message);}}finally{{b.textContent='🚀 Generate + WhatsApp';b.disabled=false;}}}}</script></body></html>'''

# ── REPORTS ───────────────────────────────────────────────────
@app.route('/daily-report',methods=['GET','POST'])
def daily_report():
    reset_daily()
    tp=today_biz['total_premium']; tpl=today_biz['total_policies']
    tgt=today_biz['target']; prj=today_biz['projected']
    rep=len(today_biz['agents_reported']); tot=len(cached_contacts)
    gap=tgt-tp; pct=round((tp/tgt*100),1) if tgt>0 else 0
    rpt=f"📊 PRIYA AI REPORT\n{today_biz['date']} | {datetime.now().strftime('%H:%M')}\n━━━━━━━━━━━━━━━━━━\n🎯 TARGET: ₹{tgt:,}\n💰 ACHIEVED: ₹{tp:,} ({pct}%)\n📈 PROJECTED: ₹{prj:,}\n📋 POLICIES: {tpl}\n📱 LEADS: {len(active_leads)}\n⚠️ GAP: ₹{gap:,}\n👥 AGENTS: {rep}/{tot}"
    if today_biz['urgent_agents']: rpt+=f"\n🚨 URGENT: {len(today_biz['urgent_agents'])} agents"
    if request.method=='POST' or request.args.get('send')=='true': wa_p(rpt)
    if request.args.get('view')=='html':
        color='#00C853' if pct>=100 else ('#FFB300' if pct>=60 else '#FF3B3B')
        ar=''.join([f'<tr><td>{d["name"].split()[0]}</td><td>{d["policies"]}</td><td>₹{d["premium"]:,}</td><td>{d.get("policy_types","—")}</td><td>{"⚠️ "+d["pending"] if d.get("pending") else "✅"}</td><td>{d["time"]}</td></tr>' for d in today_biz['agent_data'].values()])
        lr=''.join([f'<tr><td>{v["agent_name"].split()[0]}</td><td>{v["case"].get("customer_name","N/A")}</td><td>{v["case"].get("vehicle_type","")}</td><td>{v["quotation"]["policy_type"]}</td><td>₹{v["quotation"].get("total_premium",0):,}</td><td>{v["case"].get("customer_mobile","N/A")}</td><td>{v["time"]}</td></tr>' for v in list(active_leads.values())[-10:]])
        # Onboarding status
        ob_p=[a for a in cached_contacts if a.get('onboarding') in ['pending','']]
        ob_d=[a for a in cached_contacts if a.get('onboarding') not in ['pending','',None]]
        ob_rows=''.join([f'<tr><td>{a["name"].split()[0]}</td><td style="color:#FF3B3B;">⏳ Pending</td><td style="color:#909090;">{a.get("remarks","—")}</td></tr>' for a in ob_p[:10]])
        return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Priya Report</title>
<style>body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;padding:20px;}}h1{{color:#E8521A;margin-bottom:4px;}}
.card{{background:#1c1c1c;border-radius:14px;padding:18px;margin-bottom:12px;border:1px solid rgba(255,255,255,.07);}}
.big{{font-size:38px;font-weight:900;color:{color};}}.row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #252525;font-size:13px;}}
.prog{{height:16px;background:#252525;border-radius:99px;overflow:hidden;margin:10px 0;}}.pf{{height:100%;background:{color};border-radius:99px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}th{{background:#1c1c1c;padding:9px 10px;text-align:left;color:#909090;font-size:11px;text-transform:uppercase;}}
td{{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.05);}}.btn{{background:#E8521A;color:#fff;border:none;border-radius:10px;padding:10px 16px;font-size:13px;font-weight:700;cursor:pointer;margin:4px;text-decoration:none;display:inline-block;}}
.btn2{{background:#252525;border:1px solid rgba(255,255,255,.1);}}.ct{{font-size:10px;font-weight:700;color:#E8521A;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;}}</style></head>
<body><h1>📊 Priya AI — Daily Report</h1><p style="color:#909090;margin-bottom:14px;">{today_biz["date"]} | {datetime.now().strftime("%H:%M")} | Prashant Chandratre</p>
<div class="card"><div class="ct">Today Business</div><div class="big">₹{tp:,}</div>
<div style="color:#909090;margin-bottom:8px;">of ₹{tgt:,} ({pct}%)</div>
<div class="prog"><div class="pf" style="width:{min(pct,100)}%;"></div></div>
<div class="row"><span>🎯 Target</span><span>₹{tgt:,}</span></div>
<div class="row"><span>💰 Achieved</span><span style="color:{color};">₹{tp:,}</span></div>
<div class="row"><span>📈 Projected</span><span>₹{prj:,}</span></div>
<div class="row"><span>📋 Policies</span><span>{tpl}</span></div>
<div class="row"><span>📱 Active Leads</span><span style="color:#E8521A;">{len(active_leads)}</span></div>
<div class="row"><span>⚠️ Gap</span><span style="color:#FF3B3B;">₹{gap:,}</span></div>
<div class="row"><span>👥 Reported</span><span>{rep}/{tot}</span></div></div>
<div class="card"><div class="ct">📋 Onboarding Status</div>
<div style="display:flex;gap:10px;margin-bottom:12px;">
<div style="flex:1;background:#252525;border-radius:10px;padding:11px;text-align:center;"><div style="font-size:22px;font-weight:900;color:#FF3B3B;">{len(ob_p)}</div><div style="font-size:11px;color:#909090;">Pending</div></div>
<div style="flex:1;background:#252525;border-radius:10px;padding:11px;text-align:center;"><div style="font-size:22px;font-weight:900;color:#00C853;">{len(ob_d)}</div><div style="font-size:11px;color:#909090;">Done</div></div>
<div style="flex:1;background:#252525;border-radius:10px;padding:11px;text-align:center;"><div style="font-size:22px;font-weight:900;color:#E8521A;">{len(cached_contacts)}</div><div style="font-size:11px;color:#909090;">Total</div></div>
</div>
<table><thead><tr><th>Agent</th><th>Status</th><th>Remarks</th></tr></thead>
<tbody>{ob_rows}</tbody></table></div>
<div class="card"><div class="ct">📱 Today Leads</div>
{"<table><thead><tr><th>Agent</th><th>Customer</th><th>Vehicle</th><th>Policy</th><th>Premium</th><th>Mobile</th><th>Time</th></tr></thead><tbody>"+lr+"</tbody></table>" if lr else "<div style='color:#909090;text-align:center;padding:16px;'>No leads yet</div>"}</div>
<div class="card"><div class="ct">👥 Agent Business</div>
{"<table><thead><tr><th>Agent</th><th>Policies</th><th>Premium</th><th>Type</th><th>Status</th><th>Time</th></tr></thead><tbody>"+ar+"</tbody></table>" if ar else "<div style='color:#909090;text-align:center;padding:16px;'>No reports yet</div>"}</div>
<div style="display:flex;flex-wrap:wrap;gap:8px;">
<button class="btn" onclick="fetch('/daily-report',{{method:'POST'}}).then(()=>alert('✅ Sent to Prashant ji!'))">📱 Send Prashant ji</button>
<button class="btn btn2" onclick="fetch('/daily-collection',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{limit:5}})}}).then(r=>r.json()).then(d=>alert('📞 Calling '+d.called))">📞 Collect Updates</button>
<a href="/quote-form" class="btn">💰 Quote</a><a href="/agents" class="btn btn2">👥 Agents</a></div></body></html>'''
    return jsonify({'date':today_biz['date'],'target':tgt,'achieved':tp,'policies':tpl,'projected':prj,'gap':gap,'percentage':pct,'leads':len(active_leads),'report':rpt})

# ── AGENT MANAGEMENT ──────────────────────────────────────────
@app.route('/agents',methods=['GET'])
def list_agents():
    search=request.args.get('search','').lower()
    filt=[a for a in cached_contacts if not search or search in a['name'].lower() or search in a['phone']] if search else cached_contacts
    onb_colors={'pending':'rgba(255,59,59,.15)','welcome_done':'rgba(255,179,0,.15)','done':'rgba(0,200,83,.15)','active':'rgba(0,200,83,.15)'}
    onb_text={'pending':'⏳ Pending','welcome_done':'👋 Welcome Done','done':'✅ Done','active':'✅ Active'}
    rows=''.join([f'<tr><td>{i}</td><td><b>{"&nbsp;&nbsp;└ " if a.get("type")=="SUB_AGENT" else ""}{a["name"].split()[0].title()}</b><br><small style="color:#909090">{a["name"]}</small></td><td style="color:#E8521A;font-family:monospace;">{a["phone"]}</td><td style="color:#909090;">{a["agent_id"]}</td><td><span style="background:{onb_colors.get(a.get("onboarding","pending"),"rgba(255,59,59,.15)")};color:#F0F0F0;padding:2px 8px;border-radius:99px;font-size:10px;">{onb_text.get(a.get("onboarding","pending"),"⏳ Pending")}</span></td><td style="color:#909090;font-size:11px;">{a.get("remarks","—") or "—"}</td><td style="color:#00C853;">₹{today_biz["agent_data"].get(a["agent_id"],{{}}).get("premium",0):,}</td><td><a href="#" onclick="ca(\'{a["agent_id"]}\',\'{a["phone"]}\',\'{a["name"].split()[0].title()}\',\'{a.get("language","marathi")}\')" style="color:#E8521A;text-decoration:none;">📞</a></td></tr>' for i,a in enumerate(filt,1)])
    pend=len([a for a in cached_contacts if a.get('onboarding') in ['pending','']])
    done=len([a for a in cached_contacts if a.get('onboarding') not in ['pending','',None]])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Priya — Agents</title>
<style>body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;padding:20px;}}h1{{color:#E8521A;margin-bottom:12px;}}
.top{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;align-items:center;}}input{{background:#1c1c1c;border:1px solid rgba(232,82,26,.3);border-radius:10px;padding:10px 14px;color:#F0F0F0;font-size:14px;outline:none;flex:1;min-width:200px;}}
.btn{{background:#E8521A;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700;font-size:13px;cursor:pointer;border:none;white-space:nowrap;}}
.btn2{{background:#252525;border:1px solid rgba(255,255,255,.1);color:#F0F0F0;}}
table{{width:100%;border-collapse:collapse;font-size:12px;}}th{{background:#1c1c1c;padding:9px 10px;text-align:left;font-size:10px;text-transform:uppercase;color:#909090;}}
td{{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.05);}}tr:hover td{{background:rgba(232,82,26,.03);}}
.stats{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}}.stat{{background:#1c1c1c;border-radius:10px;padding:11px 16px;}}.sn{{font-size:20px;font-weight:900;color:#E8521A;}}.sl{{font-size:11px;color:#909090;}}
small{{color:#909090;font-size:10px;}}</style></head>
<body><h1>🤖 Priya AI — Agent Management</h1>
<div class="stats">
<div class="stat"><div class="sn">{len(cached_contacts)}</div><div class="sl">Total Agents</div></div>
<div class="stat"><div class="sn" style="color:#FF3B3B;">{pend}</div><div class="sl">Onboarding Pending</div></div>
<div class="stat"><div class="sn" style="color:#00C853;">{done}</div><div class="sl">Onboarded</div></div>
<div class="stat"><div class="sn">₹{today_biz["total_premium"]:,}</div><div class="sl">Today Business</div></div>
<div class="stat"><div class="sn">{len(active_leads)}</div><div class="sl">Active Leads</div></div>
</div>
<div class="top"><input type="text" placeholder="🔍 Search..." value="{search}" oninput="window.location='/agents?search='+this.value">
<a href="/daily-report?view=html" class="btn">📊 Report</a>
<a href="/quote-form" class="btn" style="text-decoration:none;">💰 Quote</a>
<a href="/upload-excel" class="btn btn2" style="text-decoration:none;">📤 Upload</a></div>
<table><thead><tr><th>#</th><th>Name</th><th>Phone</th><th>Code</th><th>Onboarding</th><th>Remarks</th><th>Today ₹</th><th>Call</th></tr></thead>
<tbody>{rows}</tbody></table>
<script>function ca(id,phone,name,lang){{if(confirm('Priya will call '+name+'?')){{fetch('/make-call',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{phone:phone,name:name,language:lang}})}}).then(r=>r.json()).then(d=>alert(d.success?'✅ Priya calling!':'❌ '+(d.error||'Check calling hours')));}}}}</script>
</body></html>'''

# ── EXCEL UPLOAD ──────────────────────────────────────────────
@app.route('/upload-excel',methods=['GET','POST'])
def upload_excel():
    if request.method=='GET':
        pend=len([a for a in cached_contacts if a.get('onboarding') in ['pending','']])
        return f'''<!DOCTYPE html><html lang="hi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Priya Upload</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:Arial;background:#0d0d0d;color:#F0F0F0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}}
.card{{background:#1c1c1c;border:1px solid rgba(232,82,26,.3);border-radius:20px;padding:28px;width:100%;max-width:480px;}}h1{{color:#E8521A;text-align:center;font-size:20px;margin-bottom:14px;}}
.sr{{display:flex;gap:10px;margin-bottom:16px;}}.s{{flex:1;background:#252525;border-radius:10px;padding:10px;text-align:center;}}.sn{{font-size:20px;font-weight:900;color:#E8521A;}}.sl{{font-size:11px;color:#909090;}}
label.lbl{{display:block;font-size:11px;font-weight:700;color:#909090;margin-bottom:5px;text-transform:uppercase;}}
.fa{{width:100%;background:#252525;border:2px dashed rgba(232,82,26,.4);border-radius:12px;padding:18px;text-align:center;cursor:pointer;margin-bottom:12px;display:block;}}
input[type=file]{{display:none;}}input[type=password]{{width:100%;background:#252525;border:1px solid rgba(255,255,255,.1);border-radius:9px;padding:11px 13px;color:#F0F0F0;font-size:14px;margin-bottom:16px;outline:none;}}
button{{width:100%;background:#E8521A;border:none;border-radius:12px;padding:14px;color:#fff;font-size:15px;font-weight:800;cursor:pointer;}}
.links{{display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap;}}.link{{color:#E8521A;text-decoration:none;font-size:12px;padding:6px 12px;background:#252525;border-radius:8px;}}
.info{{background:rgba(255,179,0,.08);border:1px solid rgba(255,179,0,.2);border-radius:10px;padding:12px;margin-bottom:14px;font-size:12px;color:#FFB300;}}</style></head>
<body><div class="card">
<div style="font-size:44px;text-align:center;margin-bottom:8px;">🤖</div>
<h1>Priya AI — Agent Upload</h1>
<div class="sr">
<div class="s"><div class="sn">{len(cached_contacts)}</div><div class="sl">Total</div></div>
<div class="s"><div class="sn" style="color:#FF3B3B;">{pend}</div><div class="sl">Onb. Pending</div></div>
<div class="s"><div class="sn">₹{today_biz["total_premium"]:,}</div><div class="sl">Today</div></div>
</div>
<div class="info">⚠️ Excel mein naye columns add karein:<br><b>Meeting Status | Remarks | Onboarding</b></div>
<form method="POST" enctype="multipart/form-data">
<label class="lbl">📎 Excel File</label>
<label class="fa" for="fi"><div style="font-size:28px;margin-bottom:5px;">📁</div><div style="font-weight:700;font-size:14px;">Click to Select (.xlsx .csv)</div>
<input type="file" id="fi" name="excel_file" accept=".xlsx,.xls,.csv" required></label>
<label class="lbl">🔐 Password</label>
<input type="password" name="password" placeholder="Enter password" required>
<button type="submit">🚀 Upload & Update</button></form>
<div class="links"><a href="/daily-report?view=html" class="link">📊 Report</a><a href="/agents" class="link">👥 Agents</a><a href="/quote-form" class="link">💰 Quote</a><a href="/marketing-page" class="link">🎯 Marketing</a></div>
</div></body></html>'''

    if not EXCEL_OK: return 'pandas not installed — add to requirements.txt',500
    if request.form.get('password','')!=UPLOAD_PASSWORD: return '<h2 style="color:red;text-align:center;padding:50px;">Wrong Password!</h2>',403
    if 'excel_file' not in request.files: return jsonify({'error':'No file'}),400
    file=request.files['excel_file']
    try:
        fb=file.read()
        df=pd.read_csv(io.BytesIO(fb)) if file.filename.lower().endswith('.csv') else pd.read_excel(io.BytesIO(fb))
        new_contacts=[]; skipped=0
        for _,row in df.iterrows():
            name=str(row.get('PartnerName') or row.get('Name') or '').strip()
            phone=str(row.get('PartnerPhoneNumber') or row.get('Phone') or row.get('Mobile') or '').strip()
            code=str(row.get('PartnerCode') or row.get('Code') or '').strip()
            rm=str(row.get('RMName') or row.get('RM') or '').strip()
            city=str(row.get('RMCity') or row.get('City') or 'Nashik').strip()
            atype=str(row.get('Type') or 'MAIN_AGENT').strip().upper()
            pcode=str(row.get('ParentAgentCode') or row.get('ParentCode') or '').strip()
            # NEW: Onboarding + Remarks columns
            onb_status=str(row.get('Onboarding') or row.get('Meeting Status') or row.get('OnboardingStatus') or 'pending').strip().lower()
            remarks=str(row.get('Remarks') or row.get('Notes') or '').strip()
            if onb_status in ['nan','none','']: onb_status='pending'
            try: pc=str(int(float(phone)))
            except: pc=phone.replace(' ','').replace('-','')
            if not pc or len(pc)<10: skipped+=1; continue
            if not pc.startswith('+'): pc='+91'+pc[-10:]
            new_contacts.append({'name':name,'phone':pc,'agent_id':code,'rm':rm,'city':city,'language':'marathi','type':atype,'parent_code':pcode,'parent_name':'','onboarding':onb_status,'remarks':remarks})
        if not new_contacts: return '<h2 style="color:red;text-align:center;padding:50px;">No valid contacts!</h2>'
        old=len(cached_contacts); cached_contacts.clear(); cached_contacts.extend(new_contacts)
        pend=len([a for a in new_contacts if a.get('onboarding') in ['pending','']])
        return f'<html><head><meta charset="UTF-8"><style>body{{background:#0d0d0d;color:#F0F0F0;font-family:Arial;text-align:center;padding:40px;}}.card{{background:#1c1c1c;border:1px solid rgba(0,200,83,.3);border-radius:20px;padding:32px;max-width:400px;margin:0 auto;}}.num{{font-size:60px;font-weight:900;color:#00C853;margin:10px 0;}}h2{{color:#00C853;}}.row{{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #252525;font-size:14px;}}.btn{{display:inline-block;background:#E8521A;color:#fff;padding:11px 22px;border-radius:10px;text-decoration:none;font-weight:800;margin:7px 4px;}}</style></head><body><div class="card"><div style="font-size:44px;">✅</div><h2>Upload Successful!</h2><div class="num">{len(new_contacts)}</div><div style="color:#909090;margin-bottom:16px;">Agents Loaded — Priya Ready!</div><div class="row"><span>Previous</span><span>{old}</span></div><div class="row"><span>New Total</span><span>{len(new_contacts)}</span></div><div class="row"><span>Skipped</span><span>{skipped}</span></div><div class="row"><span>⏳ Onboarding Pending</span><span style="color:#FF3B3B;">{pend}</span></div><a href="/agents" class="btn">👥 View Agents</a><a href="/daily-report?view=html" class="btn" style="background:#252525;border:1px solid rgba(255,255,255,.1);">📊 Report</a></div></body></html>'
    except Exception as e:
        return f'<h2 style="color:red;text-align:center;padding:50px;">Error: {str(e)}</h2>'

# ── ADD / REMOVE AGENT ────────────────────────────────────────
@app.route('/add-agent',methods=['POST'])
def add_agent():
    data=request.json or {}
    if data.get('password')!=UPLOAD_PASSWORD: return jsonify({'error':'Wrong password'}),403
    phone=str(data.get('phone','')).strip()
    if len(phone)==10: phone='+91'+phone
    if any(a['phone']==phone for a in cached_contacts): return jsonify({'error':'Already exists'}),409
    new={'name':data.get('name',''),'phone':phone,'agent_id':data.get('agent_id','IP'+str(random.randint(100000,999999))),'rm':data.get('rm',''),'city':data.get('city','Nashik'),'language':data.get('language','marathi'),'type':data.get('type','MAIN_AGENT'),'parent_code':data.get('parent_code',''),'parent_name':'','onboarding':data.get('onboarding','pending'),'remarks':data.get('remarks','')}
    cached_contacts.append(new)
    return jsonify({'success':True,'agent':new,'total':len(cached_contacts)})

@app.route('/remove-agent',methods=['POST'])
def remove_agent():
    data=request.json or {}
    if data.get('password')!=UPLOAD_PASSWORD: return jsonify({'error':'Wrong password'}),403
    phone=str(data.get('phone','')).replace('+91','')
    before=len(cached_contacts)
    idx=[i for i,a in enumerate(cached_contacts) if a['phone'].replace('+91','')==phone]
    for i in reversed(idx): cached_contacts.pop(i)
    if len(cached_contacts)==before: return jsonify({'error':'Not found'}),404
    return jsonify({'success':True,'total':len(cached_contacts)})

@app.route('/update-agent',methods=['POST'])
def update_agent():
    """Update agent onboarding status + remarks"""
    data=request.json or {}
    if data.get('password')!=UPLOAD_PASSWORD: return jsonify({'error':'Wrong password'}),403
    aid=data.get('agent_id','')
    for a in cached_contacts:
        if a['agent_id']==aid:
            if 'onboarding' in data: a['onboarding']=data['onboarding']
            if 'remarks' in data: a['remarks']=data['remarks']
            if 'language' in data: a['language']=data['language']
            return jsonify({'success':True,'agent':a})
    return jsonify({'error':'Not found'}),404

# ── MARKETING ─────────────────────────────────────────────────
@app.route('/marketing-page',methods=['GET'])
def marketing_page():
    docs_html=''.join([f'<div class="di"><span>{d["emoji"]}</span><div><div class="dn">{d["name"]}</div><div class="dd">{d["detail"]}</div></div></div>' for d in DOCS_REQUIRED])
    return f'''<!DOCTYPE html><html lang="hi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>PB Partners — Join FREE</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:Arial;background:#0a1628;color:#F0F0F0;min-height:100vh;}}
.hero{{background:linear-gradient(135deg,#003087,#0066CC);padding:28px 20px 36px;text-align:center;}}
.badge{{background:#FFD700;color:#003087;font-weight:900;font-size:15px;border-radius:99px;padding:9px 24px;display:inline-block;margin-bottom:12px;}}
.ht{{font-size:24px;font-weight:900;color:#fff;margin-bottom:6px;line-height:1.3;}}.hs{{font-size:13px;color:rgba(255,255,255,.85);}}
.profile{{background:rgba(255,255,255,.95);color:#1a1a1a;margin:16px;border-radius:14px;padding:18px;}}
.ph{{display:flex;align-items:center;gap:12px;margin-bottom:12px;}}.pav{{width:52px;height:52px;border-radius:50%;background:#003087;display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:900;flex-shrink:0;}}
.pname{{font-size:16px;font-weight:900;color:#003087;}}.prole{{font-size:11px;color:#666;}}
.cr{{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #eee;font-size:13px;}}.cr:last-child{{border:none;}}
.cico{{width:26px;height:26px;border-radius:7px;background:#003087;display:flex;align-items:center;justify-content:center;font-size:12px;}}
.content{{padding:18px;}}.st{{font-size:16px;font-weight:900;color:#FFD700;margin-bottom:12px;text-align:center;}}
.benefits{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:20px;}}
.benefit{{background:rgba(255,255,255,.07);border-radius:11px;padding:12px;text-align:center;}}
.bico{{font-size:22px;margin-bottom:5px;}}.btxt{{font-size:11px;font-weight:700;}}
.docs-box{{background:rgba(255,255,255,.05);border:1px solid rgba(255,215,0,.2);border-radius:12px;padding:16px;margin-bottom:18px;}}
.dt{{font-size:13px;font-weight:800;color:#FFD700;margin-bottom:10px;text-align:center;}}
.di{{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06);}}.di:last-child{{border:none;}}
.di span{{font-size:20px;flex-shrink:0;width:28px;text-align:center;}}.dn{{font-size:13px;font-weight:700;}}.dd{{font-size:11px;color:#A0A0A0;margin-top:1px;}}
.free{{background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.3);border-radius:10px;padding:11px;margin-bottom:16px;text-align:center;font-size:13px;font-weight:700;color:#FFD700;}}
.cta{{display:block;width:100%;border-radius:13px;padding:15px;font-size:15px;font-weight:900;text-decoration:none;text-align:center;margin-bottom:10px;}}
.cta-c{{background:linear-gradient(135deg,#003087,#0066CC);color:#fff;}}
.cta-w{{background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;}}
.note{{font-size:10px;color:#606060;text-align:center;margin-top:8px;line-height:1.6;}}
.tl{{background:linear-gradient(135deg,#FFD700,#FFA500);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900;font-size:15px;text-align:center;margin:14px 0 6px;}}</style></head>
<body>
<div class="hero"><div class="badge">🎉 100% FREE Registration | No Charges</div>
<div class="ht">Insurance Agent बनो<br>घर से कमाओ!</div>
<div class="hs">Free Training • अच्छा Commission • Policybazaar का भरोसा</div></div>
<div class="profile">
<div class="ph"><div class="pav">PC</div><div><div class="pname">{PRASHANT["name"]}</div><div class="prole">{PRASHANT["role"]} — PB Partners</div></div></div>
<div class="cr"><div class="cico">📞</div><b>{PRASHANT["phone"]}</b></div>
<div class="cr"><div class="cico">💬</div>{PRASHANT["wa"]}</div>
<div class="cr"><div class="cico">📧</div>{PRASHANT["email"]}</div>
<div class="cr"><div class="cico">🌐</div>{PRASHANT["web"]}</div>
</div>
<div class="content">
<div class="tl">#{PRASHANT["tagline"]}</div>
<div class="st">क्यों Join करें?</div>
<div class="benefits">
<div class="benefit"><div class="bico">🆓</div><div class="btxt">100% FREE</div></div>
<div class="benefit"><div class="bico">🏠</div><div class="btxt">घर से काम</div></div>
<div class="benefit"><div class="bico">💰</div><div class="btxt">अच्छा Commission</div></div>
<div class="benefit"><div class="bico">📚</div><div class="btxt">Free Training</div></div>
<div class="benefit"><div class="bico">⏰</div><div class="btxt">Flexible Time</div></div>
<div class="benefit"><div class="bico">🏆</div><div class="btxt">India #1 Platform</div></div>
</div>
<div class="docs-box"><div class="dt">📋 Required Documents</div>{docs_html}</div>
<div class="free">✅ Registration बिल्कुल FREE — No hidden charges!</div>
<a href="tel:+91{PRASHANT['phone']}" class="cta cta-c">📞 Call — {PRASHANT['phone']}</a>
<a href="{PRASHANT['wa']}" class="cta cta-w">💬 WhatsApp — Join Now!</a>
<div class="note">{PRASHANT["note"]}<br>Priya AI — Prashant Chandratre ji ki Personal AI</div>
</div></body></html>'''

# ── HOME ──────────────────────────────────────────────────────
@app.route('/',methods=['GET'])
def home():
    reset_daily()
    pct=round(today_biz['total_premium']/today_biz['target']*100,1) if today_biz['target']>0 else 0
    pend=len([a for a in cached_contacts if a.get('onboarding') in ['pending','']])
    return jsonify({
        'status':'Priya AI Active ✅','version':'3.0 FINAL',
        'assistant':'Priya — Prashant Chandratre ji ki AI',
        'total_agents':len(cached_contacts),
        'calling_hours':'10:00 AM — 6:00 PM (Incoming 24/7)',
        'today':{
            'target':f"₹{today_biz['target']:,}",'achieved':f"₹{today_biz['total_premium']:,}",
            'percentage':f"{pct}%",'policies':today_biz['total_policies'],'leads':len(active_leads)
        },
        'onboarding':{'pending':pend,'done':len(cached_contacts)-pend},
        'pages':{
            '/quote-form':'💰 Quote Generator','/daily-report?view=html':'📊 Daily Report',
            '/agents':'👥 Agents + Onboarding','/upload-excel':'📤 Excel Upload',
            '/marketing-page':'🎯 360° Marketing Page'
        }
    })

@app.route('/get-contacts',methods=['GET'])
def get_contacts(): return jsonify({'contacts':cached_contacts,'total':len(cached_contacts),'onboarding_pending':len([a for a in cached_contacts if a.get('onboarding') in ['pending','']])})

@app.route('/active-leads',methods=['GET'])
def get_leads(): return jsonify({'leads':list(active_leads.values()),'total':len(active_leads)})

@app.route('/collect-documents',methods=['POST'])
def collect_docs():
    data=request.json or {}; phone=str(data.get('phone','')).replace('+91',''); name=data.get('name','Agent'); docs=data.get('documents_received',[]); lang=data.get('language','marathi')
    if not phone: return jsonify({'error':'phone required'}),400
    if phone not in collected_docs: collected_docs[phone]={'name':name,'phone':phone,'docs':[],'date':str(date.today())}
    for d in docs:
        if d not in collected_docs[phone]['docs']: collected_docs[phone]['docs'].append(d)
    current=collected_docs[phone]['docs']; all_names=[d['name'] for d in DOCS_REQUIRED]; pending=[d for d in all_names if d not in current]
    fp='+91'+phone
    if lang=='marathi':
        msg=f"📋 *{name} जी — Documents*\n✅ मिळाले: {', '.join(current)}\n{'⏳ बाकी: '+', '.join(pending) if pending else '🎉 सर्व complete!'}\n\nWhatsApp: {PRASHANT['wa']}"
    else:
        msg=f"📋 *{name} ji — Documents*\n✅ Received: {', '.join(current)}\n{'⏳ Pending: '+', '.join(pending) if pending else '🎉 All complete!'}\n\nWhatsApp: {PRASHANT['wa']}"
    send_wa(fp,msg); wa_p(f"📋 DOCS\n{name}|{phone}\n{len(current)}/7\n{'✅ COMPLETE' if not pending else f'{len(pending)} pending'}")
    return jsonify({'success':True,'received':current,'pending':pending,'complete':len(pending)==0})

if __name__=='__main__':
    port=int(os.environ.get('PORT',8000))
    print(f"🤖 Priya AI v3.0 FINAL — Port {port} — {len(cached_contacts)} agents")
    app.run(host='0.0.0.0',port=port,debug=False)
