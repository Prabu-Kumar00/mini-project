import json, re
import PIL.Image
from google import genai
from config import GEMINI_API_KEY
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=GEMINI_API_KEY)


PROMPT_TEMPLATE = """
You are a Senior Academic Coordinator with 10+ years experience.
Your job is to route grievances even if the problem is unusual, vague, or new.

Student Dept: {dept}
Grievance: {input_desc}

Return ONLY valid JSON, no extra text:
{{
  "category": "Academic | Finance | Infrastructure | Discipline | Staff | Other",
  "priority": "High | Medium",
  "route_to": "hod | coe | accounts | admin | security | maintenance | hostel_warden | discipline",
  "is_emergency": true/false,
  "is_abusive": true/false,
  "description": "Brief 1-sentence summary of the grievance and routing reason"
}}

CRITICAL ROUTING RULES (Always follow):
1. Danger to life/safety/violence/animals → High + security + is_emergency: true
2. Exam delays/results/marks/academic → High + coe
3. Fees/documents/finance/scholarship → High + accounts
4. Inter-dept fights/serious misconduct → High + discipline
5. Lab/electricity/water/infrastructure → Medium + maintenance
6. Faculty issues/teaching quality → Medium + hod
7. Hostel/accommodation issues → Medium + hostel_warden
8. Vague or general complaints → Medium + hod
9. Abusive/offensive language → is_abusive: true

NEVER leave fields blank - always make a decision.
"""

FALLBACK = {
    "category": "Other",
    "priority": "Medium",
    "route_to": "admin",
    "is_emergency": False,
    "is_abusive": False,
    "description": "System temporarily unavailable - manual review required"
}


def analyze_text(text, dept):
    try:
        prompt = PROMPT_TEMPLATE.format(dept=dept, input_desc=f'"{text}"')
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        return FALLBACK


def analyze_image(image_path, dept):
    try:
        image = PIL.Image.open(image_path)
        prompt = PROMPT_TEMPLATE.format(
            dept=dept,
            input_desc="Image evidence attached - analyze for violence, infrastructure damage, or cleanliness issues."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image]
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini Image Error: {e}")
        return FALLBACK


def parse_response(raw):
    try:
        clean = re.sub(r'```json|```|json', '', raw).strip()
        result = json.loads(clean)

        required = ["category", "priority", "route_to", "is_emergency", "is_abusive", "description"]
        for field in required:
            if field not in result:
                result[field] = FALLBACK[field]

        # ✅ Normalize route_to to lowercase
        result["route_to"] = result["route_to"].lower().strip()

        return result
    except Exception as e:
        print(f"Parse Error: {e}")
        return FALLBACK


if __name__ == "__main__":
    print("🧪 Testing...")
    test_cases = [
        ("A stray dog entered the CSE classroom and bit a student.", "CSE"),
        ("There is a weird smell like burning plastic from the elevator.", "CSE"),
        ("CSE exam results are delayed by 2 weeks.", "CSE"),
        ("This college is absolute garbage and the staff are idiots.", "CSE"),
        ("My hostel room has no water since 3 days.", "ECE"),
        ("Faculty is not teaching properly in our department.", "MECH"),
    ]
    for text, dept in test_cases:
        print(f"\nInput: {text}")
        result = analyze_text(text, dept)
        print(f"✅ Result: {json.dumps(result, indent=2)}")
