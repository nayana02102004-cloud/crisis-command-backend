# Demo routing layer. Replace with OSRM/OpenRouteService later.
LOCATION_COORDS = {
    "Koramangala": (12.9352, 77.6245),
    "BTM": (12.9166, 77.6101),
    "HSR Layout": (12.9116, 77.6741),
    "Electronic City": (12.8452, 77.6602),
    "Silk Board": (12.9177, 77.6227),
    "Indiranagar": (12.9784, 77.6408),
    "Whitefield": (12.9698, 77.7499),
    "MG Road": (12.9756, 77.6060),
}

def estimate_route(origin, destination):
    # Simple deterministic demo ETA.
    # The UI can later replace this with a real routing API.
    if origin == destination:
        return {"distance_km": 0.8, "eta_minutes": 3}
    a = LOCATION_COORDS.get(origin, (12.9716, 77.5946))
    b = LOCATION_COORDS.get(destination, (12.9716, 77.5946))
    # Manhattan-ish demo distance.
    distance = round((abs(a[0]-b[0]) + abs(a[1]-b[1])) * 85, 1)
    distance = max(1.0, min(distance, 18.0))
    eta = max(4, round(distance * 2.2))
    return {"distance_km": distance, "eta_minutes": eta}
