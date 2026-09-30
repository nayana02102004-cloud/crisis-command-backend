import os, uuid, json, re
from dotenv import load_dotenv
from models import Incident

load_dotenv()

SYSTEM_PROMPT = """
You are the Incident Assessment Agent for Crisis Command, an emergency
decision-support prototype. Convert an emergency report into structured data.
Do not allocate resources. Do not give medical treatment instructions.
Estimate fields conservatively and clearly mark missing information.
Return ONLY JSON matching the requested schema.

Priority concepts:
- severity: seriousness of the incident, 1-10
- time_criticality: how quickly harm may occur, 1-10
- vulnerability: vulnerability of affected people, 1-10
- escalation_risk: chance the incident worsens, 1-10
"""

def _fallback(text: str) -> Incident:
    t = text.lower()
    incident_type = "general_emergency"
    if any(x in t for x in ["cardiac", "heart attack", "chest pain", "cardiac arrest"]):
        incident_type = "cardiac_emergency"
    elif any(x in t for x in ["fire", "building burning", "flames"]):
        incident_type = "building_fire"
    elif any(x in t for x in ["accident", "crash", "collision"]):
        incident_type = "road_accident"
    elif any(x in t for x in ["flood", "water rising"]):
        incident_type = "flood"
    elif any(x in t for x in ["chemical", "gas leak", "toxic"]):
        incident_type = "hazmat"

    nums = [int(x) for x in re.findall(r"\b(\d+)\s*(?:people|persons|patients|injured|victims)\b", t)]
    people = nums[0] if nums else 1

    severity = 8
    time_criticality = 8
    vulnerability = 6
    escalation = 6
    resources = ["ambulance"]

    if incident_type == "cardiac_emergency":
        severity, time_criticality, vulnerability = 10, 10, 8
        resources = ["ambulance"]
    elif incident_type == "building_fire":
        severity, time_criticality, escalation = 9, 9, 10
        resources = ["rescue_team"]
    elif incident_type == "road_accident":
        severity, time_criticality = 8, 8
        resources = ["ambulance", "rescue_team"]
    elif incident_type == "hazmat":
        severity, time_criticality, escalation = 9, 8, 10
        resources = ["rescue_team"]

    location = "Unknown"
    known_locations = ["Silk Board", "Koramangala", "BTM", "HSR Layout", "Electronic City", "Indiranagar", "Whitefield", "MG Road"]
    for loc in known_locations:
        if loc.lower() in t:
            location = loc
            break

    missing = []
    if location == "Unknown":
        missing.append("exact location")
    return Incident(
        id="INC-" + uuid.uuid4().hex[:6].upper(),
        incident_type=incident_type,
        location=location,
        people_at_risk=people,
        severity=severity,
        time_criticality=time_criticality,
        vulnerability=vulnerability,
        escalation_risk=escalation,
        hazards=[],
        required_resources=resources,
        confidence=0.55,
        missing_information=missing,
    )

def assess_incident(text: str) -> Incident:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback(text)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        schema = Incident.model_json_schema()
        prompt = SYSTEM_PROMPT + "\nEmergency report:\n" + text

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.1,
            ),
        )
        data = json.loads(response.text)
        data["id"] = "INC-" + uuid.uuid4().hex[:6].upper()
        return Incident.model_validate(data)
    except Exception:
        # Keep the demo operational if the API is unavailable.
        return _fallback(text)
