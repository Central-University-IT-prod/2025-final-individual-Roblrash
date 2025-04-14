from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class ClientUpsert(BaseModel):
    client_id: UUID
    login: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    location: str = Field(..., min_length=1)
    gender: GenderEnum


class ClientOut(BaseModel):
    client_id: UUID
    login: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    location: str = Field(..., min_length=1)
    gender: GenderEnum

    model_config = ConfigDict(from_attributes=True)

