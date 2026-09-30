def calculate_priority(incident):
    # Deterministic scoring. LLM never decides allocation mathematics.
    # We normalize people-at-risk so a large crowd matters without dominating.
    people_factor = min(10, incident.people_at_risk)
    score = (
        incident.severity * 0.30
        + incident.time_criticality * 0.25
        + people_factor * 0.20
        + incident.vulnerability * 0.15
        + incident.escalation_risk * 0.10
    )
    return round(score, 2)

def rank_incidents(incidents):
    for incident in incidents:
        incident.priority_score = calculate_priority(incident)
    return sorted(incidents, key=lambda x: x.priority_score, reverse=True)
