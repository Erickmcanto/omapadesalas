from __future__ import annotations

from datetime import date, timedelta
import uuid
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from .models import (
    Classroom,
    ClassCreate,
    ClassUpdate,
    ClassSchedule,
    DayOfWeek,
    Period,
    ReleaseRequest,
    ReservationRequest,
    ReservationResponse,
    Room,
    RoomCreate,
    RoomStatus,
    RoomUpdate,
)
from .storage import get_store


DAYS_OF_WEEK = [
    DayOfWeek.monday,
    DayOfWeek.tuesday,
    DayOfWeek.wednesday,
    DayOfWeek.thursday,
    DayOfWeek.friday,
    DayOfWeek.saturday,
    DayOfWeek.sunday,
]


def _generate_id() -> str:
    return uuid.uuid4().hex


def load_data() -> Tuple[List[Room], List[Classroom]]:
    store = get_store()
    data = store.load()
    rooms: List[Room] = data["rooms"]
    classes: List[Classroom] = data["classes"]
    if not rooms:
        rooms = seed_rooms()
        store.save(rooms, classes)
    return rooms, classes


def save_data(rooms: List[Room], classes: List[Classroom]) -> None:
    store = get_store()
    store.save(rooms, classes)


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_rooms() -> List[Room]:
    default_rooms = [
        ("Laboratório 1", "Informática", 18),
        ("Laboratório 2", "Informática", 20),
        ("Laboratório 3", "Informática", 40),
        ("Sala 4", "Experimental", 45),
        ("Laboratório 5", "Informática", 35),
        ("Laboratório 6", "Informática", 28),
        ("Laboratório 7", "Saúde", 30),
        ("Laboratório 8", "Bem-estar", 30),
        ("Laboratório 9", "Beleza", 30),
        ("Sala 10", "Convencional", 32),
        ("Sala 11", "Convencional", 32),
        ("Sala 12", "Convencional", 32),
        ("Sala 13", "Convencional", 32),
        ("Sala 14", "Teatro", 35),
        ("Sala 15", "Moda", 35),
        ("Sala 16", "Convencional", 32),
        ("Sala 17", "Convencional", 32),
        ("Sala 18", "Convencional", 32),
        ("Sala 19", "Convencional", 32),
        ("Sala 20", "Convencional", 32),
        ("Biblioteca", "Experimental", 45),
    ]
    rooms = [
        Room(id=_generate_id(), name=name, room_type=room_type, capacity=capacity)
        for name, room_type, capacity in default_rooms
    ]
    return rooms


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _class_conflicts(candidate: Classroom, target: Classroom) -> bool:
    sched_a, sched_b = candidate.schedule, target.schedule
    same_period = sched_a.period == sched_b.period
    days_overlap = bool(set(sched_a.days_of_week) & set(sched_b.days_of_week))
    date_overlap = not (
        sched_a.end_date < sched_b.start_date or sched_b.end_date < sched_a.start_date
    )
    return same_period and days_overlap and date_overlap


def _room_has_conflict(room_id: str, new_schedule: ClassSchedule, classes: List[Classroom]) -> bool:
    for cls in classes:
        if cls.room_id != room_id:
            continue
        if _class_conflicts(
            Classroom(id="temp", name="temp", schedule=new_schedule, student_count=0, room_id=room_id),
            cls,
        ):
            return True
    return False


def _room_blocked(room: Room, schedule: ClassSchedule) -> bool:
    return any(schedule.start_date <= block_date <= schedule.end_date for block_date in room.blocked_dates)


def _eligible_rooms(rooms: List[Room], schedule: ClassSchedule, students: int, classes: List[Classroom]) -> List[Room]:
    eligible = []
    for room in rooms:
        if room.capacity < students:
            continue
        if room.status == RoomStatus.blocked:
            continue
        if _room_blocked(room, schedule):
            continue
        if _room_has_conflict(room.id, schedule, classes):
            continue
        eligible.append(room)
    return eligible


def _suggest_next_gap(rooms: List[Room], schedule: ClassSchedule, students: int, classes: List[Classroom]) -> Optional[date]:
    suggestions: List[date] = []
    for room in rooms:
        if room.capacity < students:
            continue
        if room.status == RoomStatus.blocked:
            continue
        relevant_classes = [cls for cls in classes if cls.room_id == room.id]
        conflicted = [cls for cls in relevant_classes if _class_conflicts(cls, Classroom(id="temp", name="temp", schedule=schedule, student_count=0, room_id=room.id))]
        if not conflicted:
            continue
        latest_end = max(cls.schedule.end_date for cls in conflicted)
        suggestions.append(latest_end + timedelta(days=1))
    if suggestions:
        return min(suggestions)
    return None


def _update_room_status(room: Room, classes: List[Classroom]) -> RoomStatus:
    active_classes = [cls for cls in classes if cls.room_id == room.id]
    if room.status == RoomStatus.blocked:
        return RoomStatus.blocked
    if any(cls for cls in active_classes):
        return RoomStatus.occupied
    return RoomStatus.available


# ---------------------------------------------------------------------------
# Room operations
# ---------------------------------------------------------------------------

def list_rooms() -> List[Room]:
    rooms, _ = load_data()
    return rooms


def create_room(payload: RoomCreate) -> Room:
    rooms, classes = load_data()
    room = Room(id=_generate_id(), **payload.dict())
    rooms.append(room)
    save_data(rooms, classes)
    return room


def update_room(room_id: str, payload: RoomUpdate) -> Room:
    rooms, classes = load_data()
    for idx, room in enumerate(rooms):
        if room.id == room_id:
            updated = room.copy(update=payload.dict(exclude_unset=True))
            if updated.status != RoomStatus.blocked:
                updated = updated.copy(update={"status": _update_room_status(updated, classes)})
            rooms[idx] = updated
            save_data(rooms, classes)
            return updated
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sala não encontrada")


def search_rooms(filters: Dict[str, str]) -> Dict[RoomStatus, List[Room]]:
    rooms, classes = load_data()
    status_map = {status: [] for status in RoomStatus}
    for room in rooms:
        match = True
        if "room_type" in filters and filters["room_type"] != room.room_type:
            match = False
        if "status" in filters:
            try:
                filter_status = RoomStatus(filters["status"])
            except ValueError:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Status inválido")
            if filter_status != room.status:
                match = False
        if "capacity_min" in filters and room.capacity < int(filters["capacity_min"]):
            match = False
        if match:
            room.status = _update_room_status(room, classes)
            status_map[room.status].append(room)
    return status_map


# ---------------------------------------------------------------------------
# Classroom operations
# ---------------------------------------------------------------------------

def list_classes() -> List[Classroom]:
    _, classes = load_data()
    return classes


def create_class(payload: ClassCreate) -> Classroom:
    rooms, classes = load_data()
    if payload.room_id:
        room = next((room for room in rooms if room.id == payload.room_id), None)
        if not room:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sala informada não existe")
        eligible_rooms = _eligible_rooms([room], payload.schedule, payload.student_count, classes)
    else:
        eligible_rooms = _eligible_rooms(rooms, payload.schedule, payload.student_count, classes)

    if not eligible_rooms:
        suggestion = _suggest_next_gap(rooms, payload.schedule, payload.student_count, classes)
        message = "Não há sala disponível para os critérios informados."
        if suggestion:
            message += f" Próxima janela a partir de {suggestion.isoformat()}."
        raise HTTPException(status.HTTP_409_CONFLICT, detail=message)

    assigned_room = eligible_rooms[0]
    classroom = Classroom(
        id=_generate_id(),
        name=payload.name,
        schedule=payload.schedule,
        student_count=payload.student_count,
        room_id=assigned_room.id,
    )
    classes.append(classroom)
    # update room status
    for idx, room in enumerate(rooms):
        if room.id == assigned_room.id:
            rooms[idx] = room.copy(update={"status": RoomStatus.occupied})
            break
    save_data(rooms, classes)
    return classroom


def update_class(class_id: str, payload: ClassUpdate) -> Classroom:
    rooms, classes = load_data()
    for idx, cls in enumerate(classes):
        if cls.id != class_id:
            continue
        new_schedule = payload.schedule or cls.schedule
        new_room_id = payload.room_id or cls.room_id
        room = next((room for room in rooms if room.id == new_room_id), None)
        if not room:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sala informada não existe")
        eligible = _eligible_rooms([room], new_schedule, payload.student_count or cls.student_count, [c for c in classes if c.id != cls.id])
        if not eligible:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Sala indisponível para os novos critérios")
        updated = cls.copy(update=payload.dict(exclude_unset=True))
        updated.room_id = new_room_id
        updated.schedule = new_schedule
        classes[idx] = updated
        # refresh room statuses
        for ridx, r in enumerate(rooms):
            rooms[ridx] = r.copy(update={"status": _update_room_status(r, classes)})
        save_data(rooms, classes)
        return updated
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")


def release_class_day(class_id: str, payload: ReleaseRequest) -> Classroom:
    rooms, classes = load_data()
    for idx, cls in enumerate(classes):
        if cls.id == class_id:
            releases = cls.released_slots + [payload]
            updated = cls.copy(update={"released_slots": releases})
            classes[idx] = updated
            save_data(rooms, classes)
            return updated
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")


def reserve_room(payload: ReservationRequest) -> ReservationResponse:
    rooms, classes = load_data()
    requesting = next((cls for cls in classes if cls.id == payload.requesting_class_id), None)
    if not requesting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Turma solicitante não encontrada")

    target_room = next((room for room in rooms if room.id == payload.desired_room_id), None)
    if not target_room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sala desejada não encontrada")

    occupant = next((cls for cls in classes if cls.room_id == target_room.id), None)
    displaced_class_id = None
    new_room_for_displaced = None

    if occupant:
        # find alternative room for displaced class
        alt_rooms = _eligible_rooms(
            [room for room in rooms if room.id != target_room.id],
            occupant.schedule,
            occupant.student_count,
            [c for c in classes if c.id != occupant.id],
        )
        if not alt_rooms:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Não há como realocar a turma atual para concluir a reserva",
            )
        alternative_room = alt_rooms[0]
        occupant.room_id = alternative_room.id
        displaced_class_id = occupant.id
        new_room_for_displaced = alternative_room.id

    requesting.room_id = target_room.id
    for idx, cls in enumerate(classes):
        if cls.id == requesting.id:
            classes[idx] = requesting
        elif displaced_class_id and cls.id == displaced_class_id:
            classes[idx] = occupant

    for idx, room in enumerate(rooms):
        status_value = RoomStatus.reserved if room.id == target_room.id else _update_room_status(room, classes)
        rooms[idx] = room.copy(update={"status": status_value})

    save_data(rooms, classes)
    message = "Sala reservada com sucesso"
    return ReservationResponse(
        requesting_class_id=requesting.id,
        displaced_class_id=displaced_class_id,
        new_room_for_requesting=target_room.id,
        new_room_for_displaced=new_room_for_displaced,
        status=RoomStatus.reserved,
        message=message,
    )


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------

def dashboard_overview() -> Dict[str, Dict[str, int]]:
    rooms, classes = load_data()
    overview = {period.value: {"ocupadas": 0, "disponíveis": 0} for period in Period}
    for room in rooms:
        status_value = _update_room_status(room, classes)
        assigned_classes = [cls for cls in classes if cls.room_id == room.id]
        for period in Period:
            if any(cls.schedule.period == period for cls in assigned_classes):
                overview[period.value]["ocupadas"] += 1
            else:
                overview[period.value]["disponíveis"] += 1
    return overview

