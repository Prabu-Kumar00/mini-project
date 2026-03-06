from google import genai
import json, re
import PIL.Image
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT_TEMPLATE = """
You are a grievance classification AI for a college.
Student department: {dept}
Input: {input_desc}

Return ONLY valid JSON, no extra text:
{{
  "category": "Lab | Infrastructure | Discipline | Inter-Department | Water | Cleanliness | Academic | Other",
  "priority": "High | Medium",
  "route_to": "CSE HOD | ECE HOD | Warden | Maintenance | Disciplinary Committee | Admin",
  "is_abusive": true or false,
  "description": "one clear sentence describing the issue"
}}
Rules:
- Violence / ragging / fighting → Discipline, High priority
- Lab computers/equipment → Lab, route to that dept HOD
- Water / cleanliness → Maintenance, Medium
- Inter-department conflict → Disciplinary Committee
- Abusive/offensive language → is_abusive: true
- Only High or Medium priority, never Low
"""

FALLBACK = {
    "category": "Other",
    "priority": "Medium",
    "route_to": "Admin",
    "is_abusive": False,
    "description": "Grievance received. Manual review required."
}

def analyze_text(text, dept):
    try:
        prompt = PROMPT_TEMPLATE.format(dept=dept, input_desc=f'Text grievance: "{text}"')
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini error: {e}")
        return FALLBACK

def analyze_image(image_path, dept):
    try:
        image = PIL.Image.open(image_path)
        prompt = PROMPT_TEMPLATE.format(dept=dept, input_desc="Image grievance attached.")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image]
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini error: {e}")
        return FALLBACK

def parse_response(raw):
    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        return json.loads(clean)
    except Exception:
        return FALLBACK
