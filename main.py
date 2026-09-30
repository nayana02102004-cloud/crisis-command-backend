from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import EmergencyReport, ApprovalRequest
from ai_agent import assess_incident
from data import RESOURCES
from planner import build_plan
from priority import rank_incidents

app = FastAPI(title="Crisis Command", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INCIDENTS = []
CURRENT_PLAN = None
PREVIOUS_PLAN = None
AUDIT_LOG = []

def calculate_plan_diff(old_plan, new_plan):
    """
    Compare the previous response plan with the new response plan.
    """

    if old_plan is None:
        return {
            "has_changes": False,
            "changes": [],
            "reason": "Initial response plan"
        }

    old_assignments = {
        a.incident_id: a.resource_id
        for a in old_plan.assignments
    }

    new_assignments = {
        a.incident_id: a.resource_id
        for a in new_plan.assignments
    }

    changes = []

    # Detect new or changed assignments
    for incident_id, new_resource in new_assignments.items():

        old_resource = old_assignments.get(incident_id)

        if old_resource is None:
            changes.append({
                "type": "new_assignment",
                "incident_id": incident_id,
                "from_resource": None,
                "to_resource": new_resource,
                "message": f"{new_resource} assigned to {incident_id}"
            })

        elif old_resource != new_resource:
            changes.append({
                "type": "resource_reassigned",
                "incident_id": incident_id,
                "from_resource": old_resource,
                "to_resource": new_resource,
                "message": f"{incident_id}: {old_resource} → {new_resource}"
            })

    # Detect removed assignments
    for incident_id, old_resource in old_assignments.items():

        if incident_id not in new_assignments:
            changes.append({
                "type": "assignment_removed",
                "incident_id": incident_id,
                "from_resource": old_resource,
                "to_resource": None,
                "message": f"{old_resource} removed from {incident_id}"
            })

    return {
        "has_changes": len(changes) > 0,
        "changes": changes,
        "reason": (
            "Response plan changed because incident priorities "
            "or resource availability changed."
            if changes
            else "No assignment changes"
        )
    }

@app.get("/")
def home():
    return {
        "system": "Crisis Command",
        "status": "online",
        "message": "Emergency response decision-support API"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/resources")
def resources():
    return [r.model_dump() for r in RESOURCES]

@app.get("/incidents")
def incidents():
    return [i.model_dump() for i in rank_incidents(INCIDENTS)]

@app.get("/plan")
def get_plan():
    if CURRENT_PLAN is None:
        return {"message": "No response plan yet"}
    return CURRENT_PLAN.model_dump()


@app.get("/plan-diff")
def get_plan_diff():
    if CURRENT_PLAN is None:
        return {
            "has_changes": False,
            "changes": [],
            "reason": "No response plan available"
        }

    diff = calculate_plan_diff(PREVIOUS_PLAN, CURRENT_PLAN)

    return {
        "previous_plan_version": (
            PREVIOUS_PLAN.version
            if PREVIOUS_PLAN
            else None
        ),
        "current_plan_version": CURRENT_PLAN.version,
        "diff": diff
    }



@app.get("/audit")
def audit():
    return AUDIT_LOG

@app.post("/incident")
def create_incident(report: EmergencyReport):
    global CURRENT_PLAN, PREVIOUS_PLAN

    incident = assess_incident(report.message)
    INCIDENTS.append(incident)

    old_plan = CURRENT_PLAN

    new_plan = build_plan(
        INCIDENTS,
        RESOURCES,
        version=(old_plan.version + 1 if old_plan else 1),
        previous_plan=old_plan
    )

    PREVIOUS_PLAN = old_plan
    CURRENT_PLAN = new_plan

    AUDIT_LOG.append({
        "event": "incident_created",
        "incident_id": incident.id,
        "message": report.message,
        "new_plan_version": new_plan.version
    })

    return {
        "incident": incident.model_dump(),
        "plan": new_plan.model_dump(),
        "replanned": old_plan is not None,
        "approval_required": new_plan.approval_required
    }

@app.post("/inject-event") 
def inject_event(report: EmergencyReport): 
    global CURRENT_PLAN, PREVIOUS_PLAN

    message = report.message.lower()

    # Detect ambulance/resource breakdown events
    for resource in RESOURCES:
        resource_id = resource.id.lower()

        if resource_id in message and (
            "broken down" in message
            or "breakdown" in message
            or "unavailable" in message
            or "not available" in message
        ):
            # Mark the resource as unavailable
            resource.available = False

            old_plan = CURRENT_PLAN

            # Rebuild the response plan using only available resources
            new_plan = build_plan(
                INCIDENTS,
                RESOURCES,
                version=(old_plan.version + 1 if old_plan else 1),
                previous_plan=old_plan
            )

            PREVIOUS_PLAN = old_plan
            CURRENT_PLAN = new_plan

            AUDIT_LOG.append({
                "event": "resource_unavailable",
                "resource_id": resource.id,
                "message": report.message,
                "new_plan_version": new_plan.version
            })

            return {
                "event_type": "resource_failure",
                "resource": resource.model_dump(),
                "plan": new_plan.model_dump(),
                "replanned": old_plan is not None,
                "approval_required": new_plan.approval_required
            }

    # If it is not a resource failure, treat it as a normal incident
    return create_incident(report)

@app.post("/approve")
def approve(request: ApprovalRequest):
    if CURRENT_PLAN is None:
        raise HTTPException(status_code=404, detail="No plan to approve")

    status = "approved" if request.approved else "rejected"
    AUDIT_LOG.append({
        "event": "human_decision",
        "plan_id": request.plan_id,
        "decision": status,
        "commander": request.commander
    })

    return {
        "status": status,
        "plan_id": request.plan_id,
        "commander": request.commander,
        "message": "Decision recorded in audit log."
    }

@app.post("/reset")
def reset():
    global INCIDENTS, CURRENT_PLAN, PREVIOUS_PLAN, AUDIT_LOG

    INCIDENTS = []
    CURRENT_PLAN = None
    PREVIOUS_PLAN = None
    AUDIT_LOG = []

    # Restore resources after reset
    for resource in RESOURCES:
        resource.available = True

    return {"status": "reset"}
