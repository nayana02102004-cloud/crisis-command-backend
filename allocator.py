from models import Assignment
from router import estimate_route

def allocate_resources(incidents, resources):
    assignments = []
    shortages = []
    used = set()

    for incident in incidents:
        needed = set(incident.required_resources)

        # First pass: exact type/capability match.
        for resource in resources:
            if resource.id in used or not resource.available:
                continue
            if resource.type not in needed and not (set(resource.capabilities) & needed):
                continue

            route = estimate_route(resource.location, incident.location)
            assignments.append(
                Assignment(
                    resource_id=resource.id,
                    incident_id=incident.id,
                    eta_minutes=route["eta_minutes"],
                    distance_km=route["distance_km"],
                )
            )
            used.add(resource.id)
            # One ambulance/resource per requested type for MVP.
            break

        # If no resource found, record shortage.
        if not any(a.incident_id == incident.id for a in assignments):
            shortages.append(
                f"No available matching resource for incident {incident.id}"
            )

    return assignments, shortages
