"""
============================================================
DAILY ENGAGEMENT MODULE
============================================================
Prashant Sir ki taraf se daily morning messages
- Marathi version (Pune, Nashik, Maharashtra agents)
- Hindi version (Mumbai, other agents)
- Day-specific themes (Monday-Sunday)
============================================================
"""

from datetime import datetime
import os

# ============================================================
# CONFIG
# ============================================================
RM_NAME = os.getenv("RM_NAME", "Prashant Chandratre")
RM_PHONE = os.getenv("RM_PHONE", "+91 7709446589")

# ============================================================
# MARATHI MORNING MESSAGES (Day-wise)
# ============================================================
MORNING_MESSAGES_MARATHI = {
    "Monday": """🌅 शुभ सकाळ {name} जी!

नवीन आठवडा, नवीन goals! 💪

आजचे challenge:
✅ कमीत कमी ३ quotes generate करा
✅ १ pending renewal ला call करा
✅ एक नवीन customer पर्यंत पोहोचा

लक्षात ठेवा — PBPartners मध्ये Partner Contest मधून up to 3.50% extra reward मिळतो. तुमचा effort = तुमचा reward.

मदत हवी असेल तर मला message करा.

- {rm_name}
📞 {rm_phone}""",

    "Tuesday": """🌞 शुभ सकाळ {name} जी!

आज Renewal Tuesday! 🔄

तुमच्या pending renewals पैकी ३ ला आज call करा. Renewal Contest मधून up to 2% extra commission मिळतो.

💡 Prashant tip:
"Renewal call मध्ये आधी 'गाडी कशी चालू आहे?' विचारा — मग insurance बद्दल बोला. Trust आधी, business नंतर."

आजचा goal — 3 renewals!

- {rm_name}
📞 {rm_phone}""",

    "Wednesday": """🌅 शुभ सकाळ {name} जी!

आज Cross-Sell Wednesday! 💼

तुमच्या motor customers पैकी 70% कडे family health insurance नाही. ही तुमची biggest opportunity आहे!

📱 Script:
"Sir, गाडीचा insurance झाला — फार छान. कुटुंबाचा health insurance आहे का? Hospital bills खूप वाढले आहेत. १ लाखाचा cover फक्त ₹500/month पासून."

आज २ cross-sell try करा!

- {rm_name}
📞 {rm_phone}""",

    "Thursday": """🌅 शुभ सकाळ {name} जी!

आज Customer Care Thursday! ❤️

५ जुन्या customers ना एक voice note पाठवा:
🎙️ "नमस्कार sir/madam, प्रशांत सरांच्या team कडून. सर्व ठीक आहे ना? काही help हवी आहे का?"

हे FREE आहे, पण effect खूप मोठा:
✅ Customer retention 2x
✅ Referrals आपोआप
✅ Renewal पक्के

तुमचे loyal customers हीच तुमची कमाई!

- {rm_name}
📞 {rm_phone}""",

    "Friday": """🌅 शुभ सकाळ {name} जी!

Friday morning! 🚀 Weekend ला लोक गाडी shopping करतात. आज ३ नवीन leads generate करा!

💡 Prashant's Friday Formula:
1. Local garage owner शी बोला
2. Petrol pump जवळ २ cars चे owners
3. WhatsApp status वर quote sticker

Loyalty Yearly Club मध्ये top performers ला Trip Reward up to 1.73% मिळतो. तुम्ही त्या position जवळ आहात!

- {rm_name}
📞 {rm_phone}""",

    "Saturday": """🌅 Saturday energy {name} जी! ⚡

Weekend = High-conversion time! लोक free असतात, बोलण्याचा mood असतो.

आजचा focus:
🎯 २ face-to-face meetings
🎯 ५ pending follow-ups close करा
🎯 १ family insurance bundle pitch

Quarterly Club चे milestones जवळ येत आहेत — up to 0.50% extra. Push करा!

कोणी customer stuck असेल तर मला call करा, मी directly बोलून घेईन.

- {rm_name}
📞 {rm_phone}""",

    "Sunday": """🌸 शुभ सकाळ {name} जी!

आज Sunday — rest day, पण smart planning चा दिवस!

💡 आज हे करा:
1. Top 5 leads ची list बनवा
2. ३ renewals चे script ready करा
3. १ cross-sell opportunity identify करा

कुटुंबासोबत वेळ घालवा — Monday पासून पुन्हा तयारी. 💪

PBPartners ecosystem मध्ये तुम्ही सर्व मिळून एक team आहोत. Grow Together, Succeed Together.

- {rm_name}
📞 {rm_phone}"""
}

# ============================================================
# HINDI MORNING MESSAGES (Day-wise)
# ============================================================
MORNING_MESSAGES_HINDI = {
    "Monday": """🌅 Suprabhat {name} ji!

Naya hafta, naye goals! 💪

Aaj ka challenge:
✅ Kam se kam 3 quotes generate karo
✅ 1 pending renewal ko call karo
✅ Ek naya customer reach karo

Yaad rakho — PBPartners mein Partner Contest se up to 3.50% extra reward milta hai. Aapka effort = aapka reward.

Help chahiye to message karo.

- {rm_name}
📞 {rm_phone}""",

    "Tuesday": """🌞 Suprabhat {name} ji!

Aaj Renewal Tuesday! 🔄

Aapke pending renewals mein se 3 ko aaj call karo. Renewal Contest se up to 2% extra commission milta hai.

💡 Prashant tip:
"Renewal call mein pehle 'Sir, gaadi kaisi chal rahi hai?' puchho — phir insurance baat karo. Trust pehle, business baad mein."

Aaj ka goal — 3 renewals!

- {rm_name}
📞 {rm_phone}""",

    "Wednesday": """🌅 Suprabhat {name} ji!

Aaj Cross-Sell Wednesday! 💼

Aapke motor customers mein se 70% ke paas family health insurance NAHI hai. Yeh aapka biggest opportunity hai!

📱 Script:
"Sir, gaadi ka insurance ho gaya — bahut accha. Family ka health insurance hai? Hospital bills bahut badh gaye hain. 1 lakh ka cover sirf ₹500/month se."

Aaj 2 cross-sell try karo!

- {rm_name}
📞 {rm_phone}""",

    "Thursday": """🌅 Suprabhat {name} ji!

Aaj Customer Care Thursday! ❤️

5 purane customers ko ek voice note bhejo:
🎙️ "Namaste sir/madam, Prashant Sir ki team se. Sab theek hai? Koi help chahiye?"

Yeh FREE hai, par effect bahut bada:
✅ Customer retention 2x
✅ Referrals automatic
✅ Renewal pakka

Aapke loyal customers hi aapki kamai hain!

- {rm_name}
📞 {rm_phone}""",

    "Friday": """🌅 Suprabhat {name} ji!

Friday morning! 🚀 Weekend pe log gaadi shopping karte hain. Aaj 3 naye leads generate karo!

💡 Prashant's Friday Formula:
1. Local garage owner se baat
2. Petrol pump ke pass 2 cars ke owners
3. WhatsApp status pe quote sticker

Loyalty Yearly Club mein top performers ko Trip Reward up to 1.73% milta hai. Aap us position ke kareeb ho!

- {rm_name}
📞 {rm_phone}""",

    "Saturday": """🌅 Saturday energy {name} ji! ⚡

Weekend = High-conversion time! Log free hote hain, baat karne ka mood hota hai.

Aaj ka focus:
🎯 2 face-to-face meetings
🎯 5 pending follow-ups close karo
🎯 1 family insurance bundle pitch

Quarterly Club ke milestones near aa rahe hain — up to 0.50% extra. Push karo!

Koi customer stuck? Mujhe call karo, main directly baat kar lunga.

- {rm_name}
📞 {rm_phone}""",

    "Sunday": """🌸 Suprabhat {name} ji!

Aaj Sunday — rest day, par smart planning ka din!

💡 Aaj yeh karo:
1. Top 5 leads ki list banao
2. 3 renewals ka script ready karo
3. 1 cross-sell opportunity identify karo

Family ke saath time spend karo — Monday se phir taiyari. 💪

PBPartners ecosystem mein aap sab mil ke ek team ho. Grow Together, Succeed Together.

- {rm_name}
📞 {rm_phone}"""
}


# ============================================================
# MAIN FUNCTION
# ============================================================
def get_morning_message(agent_name, language="marathi"):
    """
    Get personalized morning message based on:
    - Day of week
    - Agent's preferred language
    - Agent's first name
    """
    # Get today's day
    today = datetime.now().strftime("%A")
    
    # Extract first name only
    first_name = agent_name.split()[0] if agent_name else "Sir"
    
    # Select language template
    if language.lower() == "hindi":
        templates = MORNING_MESSAGES_HINDI
    else:
        templates = MORNING_MESSAGES_MARATHI
    
    # Get day's template (fallback to Monday)
    template = templates.get(today, templates["Monday"])
    
    # Fill placeholders
    message = template.format(
        name=first_name,
        rm_name=RM_NAME,
        rm_phone=RM_PHONE
    )
    
    return message


# ============================================================
# TEST FUNCTION (for local debugging)
# ============================================================
if __name__ == "__main__":
    # Test Marathi
    print("=" * 60)
    print("MARATHI VERSION:")
    print("=" * 60)
    print(get_morning_message("Prashant Chandratre", "marathi"))
    
    print("\n" + "=" * 60)
    print("HINDI VERSION:")
    print("=" * 60)
    print(get_morning_message("Shaikh Farhin", "hindi"))
