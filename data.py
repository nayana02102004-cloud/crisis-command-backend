from models import Resource, Hospital

RESOURCES = [
    Resource(id="AMB-01", type="ambulance", location="Koramangala", capabilities=["basic_life_support", "medical"]),
    Resource(id="AMB-02", type="ambulance", location="BTM", capabilities=["advanced_life_support", "medical"]),
    Resource(id="AMB-03", type="ambulance", location="HSR Layout", capabilities=["basic_life_support", "medical"]),
    Resource(id="RES-01", type="rescue_team", location="HSR Layout", capabilities=["rescue", "fire"]),
    Resource(id="RES-02", type="rescue_team", location="Electronic City", capabilities=["rescue", "fire"]),
]

HOSPITALS = [
    Hospital(id="H-01", name="Apollo Demo Hospital", location="Koramangala", specialties=["cardiac", "trauma", "general"], available_beds=12),
    Hospital(id="H-02", name="City Emergency Hospital", location="BTM", specialties=["trauma", "general"], available_beds=8),
    Hospital(id="H-03", name="Metro Medical Center", location="HSR Layout", specialties=["cardiac", "general"], available_beds=5),
]
