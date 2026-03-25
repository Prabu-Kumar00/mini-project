import json
import re
import base64
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT_TEMPLATE = """
You are a Senior Academic Coordinator at Sri Ramakrishna Engineering College (SREC).

Analyze this student grievance and determine the correct department to route it to.

Student Department: {dept}
Complaint: {input_desc}

ROUTING RULES (strictly follow this priority order):

0. SERIOUS INCIDENT — check this BEFORE anything else, overrides ALL location rules:
   - FIGHTING / PHYSICAL ALTERCATION / ASSAULT / BEATING / ATTACK → "Discipline & Welfare Committee"
   - RAGGING / BULLYING / THREAT / INTIMIDATION / HARASSMENT by students → "Anti Ragging Committee"
   - SEXUAL HARASSMENT / GENDER ABUSE / MISCONDUCT → "Internal Complaints Committee"
   - DRUGS / ALCOHOL / SMOKING / SUBSTANCE ABUSE → "Anti Drug Committee"
   ⚠️ These ALWAYS override location. "near library", "near hostel", "near canteen" = irrelevant. Route to the committee.

1. ESCALATION / FOLLOW-UP — check this before location:
   - NO RESPONSE TO PREVIOUS GRIEVANCE / GRIEVANCE IGNORED / NOT RESOLVED → "Grievance Redressal Committee"
   - WANT TO ESCALATE / NO ACTION TAKEN / COMPLAINT IGNORED → "Grievance Redressal Committee"
   - PREVIOUSLY SUBMITTED BUT NO REPLY → "Grievance Redressal Committee"

2. LOCATION FIRST — location overrides problem type (only for infrastructure/facility issues):
   - Problem IN LIBRARY / library wifi / library computer / library seating → "Librarian"
   - Problem IN HOSTEL / hostel room / mess / dormitory / hostel bathroom → "Hostel Warden"
   - Problem IN CLASSROOM / lecture hall / department building / class bench / class fan → "{dept} HOD"
   - Problem IN COMPUTER LAB / system lab / programming lab → "Computer Maintenance Cell"
   - Problem IN EXAM HALL / exam centre / COE office → "Controller of Examinations"
   - Problem IN BOOK DEPOT / book store / stationery shop → "Book Depot"
   - Problem IN CANTEEN / campus canteen / food court → "Admin Office"
   - Problem IN SPORTS GROUND / playground / gym / sports room → "Student Affairs Cell"
   - Problem IN RESEARCH LAB / research centre → "Research Committee"
   - Problem AT CAMPUS GATE / security / parking → "Admin Office"
   - Problem IN ADMIN BLOCK / admin office → "Admin Office"

3. PROBLEM TYPE — only if no specific location mentioned:
   - FACULTY / TEACHING / ATTENDANCE / SYLLABUS / MENTOR / ACADEMIC → "{dept} HOD"
   - BROKEN FURNITURE (bench/chair/desk/table) in dept or classroom → "{dept} HOD"
   - PROJECTOR / COMPUTER / SYSTEM not working IN CLASSROOM → "{dept} HOD"
   - PROJECTOR / COMPUTER / SYSTEM not working IN LAB → "Computer Maintenance Cell"
   - EXAM / RESULT / HALL TICKET / MARKS / REVALUATION / GRADE → "Controller of Examinations"
   - FEES / PAYMENT / SCHOLARSHIP / FINE / ACCOUNTS / CHALLAN → "Admin Office"
   - DISCIPLINE / CONDUCT / MISBEHAVIOUR / WELFARE → "Discipline & Welfare Committee"
   - RESEARCH / PROJECT FUNDING / PAPER / PATENT → "Research Committee"
   - EVENTS / SPORTS / CULTURAL / FEST / NSS → "Student Affairs Cell"
   - CAMPUS WIFI / WATER / ELECTRICITY / GENERAL CAMPUS MAINTENANCE → "Admin Office"

4. DEFAULT → "{dept} HOD"

CRITICAL RULES (never break these):
   - FIGHTING / VIOLENCE / ASSAULT anywhere on campus → ALWAYS "Discipline & Welfare Committee"
   - RAGGING / BULLYING anywhere on campus → ALWAYS "Anti Ragging Committee"
   - Location words like "near library block", "near hostel", "near canteen" only tell you WHERE it happened — they do NOT change the routing if the problem is violence/discipline
   - Grievance ignored / no response / want to escalate → ALWAYS "Grievance Redressal Committee"
   - ANY infrastructure problem inside CLASSROOM or DEPARTMENT BUILDING → ALWAYS "{dept} HOD"
   - Computer/projector NOT WORKING IN CLASSROOM → "{dept} HOD", never CMC
   - Computer/system broken IN COMPUTER LAB → "Computer Maintenance Cell"
   - Fan/AC/light IN CLASSROOM → "{dept} HOD"
   - Fan/AC/light IN HOSTEL → "Hostel Warden"
   - Do NOT route classroom issues to Admin Office or CMC
   - Do NOT route hostel issues to Admin Office
   - When location is unclear → default to "{dept} HOD"
   - Replace {{dept}} with actual department: {dept}

EXAMPLES (learn from these):
   - "students fighting near library block" (CSE) → "Discipline & Welfare Committee"
   - "physical altercation near hostel gate" (ECE) → "Discipline & Welfare Committee"
   - "ragging happening near canteen" (IT) → "Anti Ragging Committee"
   - "student assaulted near sports ground" (CSE) → "Discipline & Welfare Committee"
   - "student smoking near library" (CSE) → "Anti Drug Committee"
   - "wifi not working in library" (CSE) → "Librarian"
   - "my previously submitted grievances have not received a response" (CSE) → "Grievance Redressal Committee"
   - "grievance not resolved, want to escalate" (ECE) → "Grievance Redressal Committee"
   - "projector not working in my class" (CSE) → "CSE HOD"
   - "computer lab systems are down" (ECE) → "Computer Maintenance Cell"
   - "broken bench in classroom" (MECH) → "MECH HOD"
   - "hostel room fan broken" (CSE) → "Hostel Warden"
   - "faculty not teaching properly" (EEE) → "EEE HOD"
   - "fees not updated in portal" (AERO) → "Admin Office"
   - "food quality bad in canteen" (CSE) → "Admin Office"
   - "exam hall AC not working" (IT) → "Controller of Examinations"
   - "hostel mess food quality poor" (AERO) → "Hostel Warden"
   - "attendance not updated by faculty" (BME) → "BME HOD"
   - "cultural fest budget not approved" (ECE) → "Student Affairs Cell"

Return ONLY valid JSON (no markdown, no explanation, no extra text):

{{
  "category": "Academic | Finance | Infrastructure | Discipline | Hostel | Library | Other",
  "priority": "High | Medium | Low",
  "route_to": "Exact name — e.g: CSE HOD / Librarian / Hostel Warden",
  "summary": "One line summary of the complaint",
  "is_emergency": true or false,
  "is_abusive": true or false,
  "description": "2-3 sentence professional description"
}}
"""

FALLBACK = {
    "category": "Other",
    "priority": "Medium",
    "route_to": "Admin Office",
    "summary": "Grievance submitted — under review",
    "is_emergency": False,
    "is_abusive": False,
    "description": "System fallback routing. Please review manually."
}


# ─── TEXT ANALYSIS ────────────────────────────────────────
def analyze_text(text, dept):
    try:
        prompt = PROMPT_TEMPLATE.format(
            dept=dept,
            input_desc=f'"{text}"'
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        result = parse_response(response.choices[0].message.content)

        if "{dept}" in result.get("route_to", ""):
            result["route_to"] = result["route_to"].replace("{dept}", dept)

        return result

    except Exception as e:
        print("Groq Text Error:", e)
        return FALLBACK


# ─── IMAGE ANALYSIS ───────────────────────────────────────
def analyze_image(image_path, dept, extra_text=""):
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.lower().split(".")[-1]
        mime = "image/png" if ext == "png" else "image/jpeg"

        prompt = PROMPT_TEMPLATE.format(
            dept=dept,
            input_desc=f'Image uploaded by a {dept} student. {extra_text} Analyze the image carefully, describe what problem you see, identify the location, then route accordingly.'
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mime};base64,{image_data}"
                    }}
                ]
            }],
            temperature=0.2
        )
        result = parse_response(response.choices[0].message.content)

        if "{dept}" in result.get("route_to", ""):
            result["route_to"] = result["route_to"].replace("{dept}", dept)

        return result

    except Exception as e:
        print("Groq Image Error:", e)
        return FALLBACK


# ─── PARSE JSON RESPONSE ─────────────────────────────────
def parse_response(raw):
    try:
        clean = re.sub(r'```json|```|json', '', raw).strip()
        result = json.loads(clean)

        required = ["category", "priority", "route_to",
                    "summary", "is_emergency", "is_abusive", "description"]
        for field in required:
            if field not in result:
                result[field] = FALLBACK[field]

        result["is_abusive"] = False  # ✅ disabled — faculty can see all details
        result["route_to"] = result["route_to"].strip()
        return result

    except Exception as e:
        print("Parse Error:", e)
        return FALLBACK


# ── TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        ("students fighting near library block", "CSE"),
        ("ragging happening near canteen", "IT"),
        ("student smoking near library", "CSE"),
        ("wifi not working in library", "CSE"),
        ("projector broken in classroom", "CSE"),
        ("hostel bathroom has no water", "ECE"),
        ("grievance not resolved, want to escalate", "ECE"),
        ("computer lab systems not working", "ECE"),
    ]

    for text, dept in test_cases:
        result = analyze_text(text, dept)
        print(f"Input : {text}")
        print(f"Routes: {result['route_to']}")
        print(f"Categ : {result['category']}")
        print("─" * 50)
