from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class RoomStatus(str, Enum):
    available = "Disponível"
    occupied = "Ocupada"
    reserved = "Reservada"
    blocked = "Bloqueada"


class Period(str, Enum):
    morning = "Manhã"
    afternoon = "Tarde"
    evening = "Noite"


class DayOfWeek(str, Enum):
    monday = "Segunda"
    tuesday = "Terça"
    wednesday = "Quarta"
    thursday = "Quinta"
    friday = "Sexta"
    saturday = "Sábado"
    sunday = "Domingo"


class Room(BaseModel):
    id: str
    name: str
    room_type: str
    capacity: int
    status: RoomStatus = Field(default=RoomStatus.available)
    blocked_dates: List[date] = Field(default_factory=list)


class RoomCreate(BaseModel):
    name: str
    room_type: str
    capacity: int


class RoomUpdate(BaseModel):
    name: Optional[str]
    room_type: Optional[str]
    capacity: Optional[int]
    status: Optional[RoomStatus]
    blocked_dates: Optional[List[date]]


class ClassSchedule(BaseModel):
    start_date: date
    end_date: date
    days_of_week: List[DayOfWeek]
    period: Period

    @validator("end_date")
    def validate_dates(cls, v: date, values: dict) -> date:
        start = values.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class ClassroomRelease(BaseModel):
    date: date
    period: Period
    reason: Optional[str]


class Classroom(BaseModel):
    id: str
    name: str
    schedule: ClassSchedule
    student_count: int
    room_id: str
    released_slots: List[ClassroomRelease] = Field(default_factory=list)


class ClassCreate(BaseModel):
    name: str
    schedule: ClassSchedule
    student_count: int
    room_id: Optional[str]


class ClassUpdate(BaseModel):
    schedule: Optional[ClassSchedule]
    student_count: Optional[int]
    room_id: Optional[str]


class ReservationRequest(BaseModel):
    requesting_class_id: str
    desired_room_id: str
    reason: Optional[str]


class ReservationResponse(BaseModel):
    requesting_class_id: str
    displaced_class_id: Optional[str]
    new_room_for_requesting: str
    new_room_for_displaced: Optional[str]
    status: RoomStatus
    message: str


class ReleaseRequest(BaseModel):
    date: date
    period: Period
    reason: Optional[str]

