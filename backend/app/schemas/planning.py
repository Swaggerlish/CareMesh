from pydantic import BaseModel


class MedicalDesertItem(BaseModel):
    state: str
    lga: str
    severity: str
    score: int
    population: int | None = None
    population_source: str
    nearest_care_km: int
    estimated_travel_time_minutes: int
    facilities_in_lga: int
    mapped_hospitals: int
    bed_capacity: int
    doctor_capacity: int
    nurse_capacity: int
    missing_services: list[str]
    recommendation: str


class InventorySignalItem(BaseModel):
    service: str
    desert_count: int
    affected_population: int


class FacilitySummaryItem(BaseModel):
    state: str
    count: int
    mapped: int
    total_beds: int
    total_doctors: int
    specialties: list[str]


class PlanningResponse(BaseModel):
    medical_deserts: list[MedicalDesertItem]
    inventory_signals: list[InventorySignalItem]
    facilities_summary: list[FacilitySummaryItem]
    note: str
