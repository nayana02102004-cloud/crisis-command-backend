from typing import List, Optional
from pydantic import BaseModel, Field

class EmergencyReport(BaseModel):
    message: str

class Incident(BaseModel):
    id: str
    incident_type: str
    location: str
    people_at_risk: int = Field(ge=0)
    severity: int = Field(ge=1, le=10)
    time_criticality: int = Field(ge=1, le=10)
    vulnerability: int = Field(ge=1, le=10)
    escalation_risk: int = Field(ge=1, le=10)
    hazards: List[str] = []
    required_resources: List[str] = []
    confidence: float = Field(ge=0, le=1)
    missing_information: List[str] = []
    priority_score: float = 0.0
    status: str = "active"

class Resource(BaseModel):
    id: str
    type: str
    location: str
    capabilities: List[str] = []
    available: bool = True

class Hospital(BaseModel):
    id: str
    name: str
    location: str
    specialties: List[str] = []
    available_beds: int = 0

class Assignment(BaseModel):
    resource_id: str
    incident_id: str
    eta_minutes: int
    distance_km: float
    status: str = "proposed"

class ResponsePlan(BaseModel):
    plan_id: str
    version: int
    assignments: List[Assignment]
    hospital_assignments: dict = {}
    shortages: List[str] = []
    contingency_options: List[str] = []
    explanation: str = ""
    approval_required: bool = False

class ApprovalRequest(BaseModel):
    plan_id: str
    approved: bool
    commander: str = "Demo Commander"
