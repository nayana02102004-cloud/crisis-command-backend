import uuid
from models import ResponsePlan
from priority import rank_incidents
from allocator import allocate_resources
from data import RESOURCES, HOSPITALS

def choose_hospital(incident):
    specialty = "cardiac" if "cardiac" in incident.incident_type else "trauma" if "accident" in incident.incident_type else "general"
    candidates = [h for h in HOSPITALS if specialty in h.specialties and h.available_beds > 0]
    if not candidates:
        candidates = [h for h in HOSPITALS if h.available_beds > 0]
    if not candidates:
        return None
    return max(candidates, key=lambda h: h.available_beds)

def build_plan(incidents, resources, version=1, previous_plan=None):
    ranked = rank_incidents(incidents)
    assignments, shortages = allocate_resources(ranked, resources)

    hospital_assignments = {}
    for inc in ranked:
        if "ambulance" in inc.required_resources:
            hospital = choose_hospital(inc)
            if hospital:
                hospital_assignments[inc.id] = {
                    "hospital_id": hospital.id,
                    "hospital_name": hospital.name,
                    "available_beds": hospital.available_beds
                }

    explanation = (
        "Incidents were ranked using severity, time criticality, people at risk, "
        "vulnerability and escalation risk. Resources were matched deterministically "
        "to required capabilities and route ETAs were estimated."
    )

    approval_required = False
    if previous_plan:
        old = {(a.resource_id, a.incident_id) for a in previous_plan.assignments}
        new = {(a.resource_id, a.incident_id) for a in assignments}
        if old != new:
            approval_required = True

    return ResponsePlan(
        plan_id="PLAN-" + uuid.uuid4().hex[:6].upper(),
        version=version,
        assignments=assignments,
        hospital_assignments=hospital_assignments,
        shortages=shortages,
        contingency_options=[
            "Keep one ambulance reserved when possible.",
            "If a matched resource becomes unavailable, rerun allocation.",
            "If new high-severity incident arrives, trigger immediate replan."
        ],
        explanation=explanation,
        approval_required=approval_required,
    )
