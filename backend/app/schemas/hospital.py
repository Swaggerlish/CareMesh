from pydantic import BaseModel, computed_field


class HospitalBase(BaseModel):
    name: str
    country: str = 'Nigeria'
    state: str
    lga: str
    address: str
    specialties: str
    services: str
    capabilities: str
    registry_id: str | None = None
    phone: str | None = None
    email: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class HospitalOut(HospitalBase):
    id: int

    @computed_field
    @property
    def facilities(self) -> list[str]:
        services_list = [s.strip() for s in self.services.split(',') if s.strip()]
        capabilities_list = [c.strip() for c in self.capabilities.split(',') if c.strip()]
        return services_list + capabilities_list

    class Config:
        from_attributes = True
