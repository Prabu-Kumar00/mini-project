import json, re
import PIL.Image
from google import genai
from config import GEMINI_API_KEY
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=GEMINI_API_KEY)

# Your improved uncertainty-aware prompt - handles weird/edge cases perfectly
PROMPT_TEMPLATE = """
You are a Senior Academic Coordinator with 10+ years experience. 
Your job is to route grievances even if the problem is unusual, vague, or new.

Student Dept: {dept}
Grievance: {input_desc}

Return ONLY valid JSON, no extra text:
{{
  "category": "Academic | Finance | Infrastructure | Discipline | Staff | Other",
  "priority": "High | Medium", 
  "route_to": "HOD | COE | Accounts | Admin | Security | Maintenance",
  "is_emergency": true/false,
  "logic": "Briefly explain your reasoning in 1 sentence"
}}

CRITICAL ROUTING RULES (Always follow):
1. Danger to life/safety/violence/animals → High + Security + is_emergency: true
2. Exam delays/results/marks → High + COE  
3. Fees/documents/finance → High + Accounts
4. Inter-dept fights → High + Admin
5. Lab/electricity/water → Medium + Maintenance/HOD
6. Faculty issues → Medium + HOD
7. Vague "come see" complaints → Medium + HOD

NEVER use "Other" category or leave fields blank - always make a decision.
"""

FALLBACK = {
    "category": "Other",
    "priority": "Medium",
    "route_to": "Admin", 
    "is_emergency": False,
    "logic": "System temporarily unavailable - manual review required"
}

def analyze_text(text, dept):
    """Analyze text grievance with uncertainty handling"""
    try:
        prompt = PROMPT_TEMPLATE.format(dept=dept, input_desc=f'"{text}"')
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        return FALLBACK

def analyze_image(image_path, dept):
    """Analyze image grievance (violence/infrastructure/cleanliness)"""
    try:
        image = PIL.Image.open(image_path)
        prompt = PROMPT_TEMPLATE.format(dept=dept, input_desc="Image evidence attached - analyze for violence, infrastructure damage, or cleanliness issues.")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image]
        )
        return parse_response(response.text)
    except Exception as e:
        print(f"Gemini Image Error: {e}")
        return FALLBACK

def parse_response(raw):
    """Extract JSON from Gemini response, fallback if parsing fails"""
    try:
        # Remove markdown code blocks and parse
        clean = re.sub(r'```json|```|```|json', '', raw).strip()
        result = json.loads(clean)
        
        # Validate required fields exist
        required = ["category", "priority", "route_to", "is_emergency", "logic"]
        for field in required:
            if field not in result:
                result[field] = FALLBACK[field]
                
        return result
    except Exception as e:
        print(f"Parse Error: {e}")
        return FALLBACK

# Test function - run `python gemini_helper.py` to test
if __name__ == "__main__":
    print("🧪 Testing uncertainty cases...")
    test_cases = [
        ("A stray dog entered the CSE classroom and bit a student.", "CSE"),
        ("There is a weird smell like burning plastic from the elevator.", "CSE"),
        ("Problem in ECE dept, please come and see immediately.", "ECE"),
        ("CSE exam results are delayed by 2 weeks.", "CSE")
    ]
    
    for text, dept in test_cases:
        print(f"\nInput: {text}")
        result = analyze_text(text, dept)
        print(f"✅ Result: {json.dumps(result, indent=2)}")
