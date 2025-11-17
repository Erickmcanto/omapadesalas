from fastapi import FastAPI

from . import services
from .models import (
    ClassCreate,
    ClassUpdate,
    ReleaseRequest,
    ReservationRequest,
    RoomCreate,
    RoomUpdate,
)

app = FastAPI(title="Gerenciamento de Salas", version="1.0.0")


@app.get("/rooms")
def get_rooms():
    return services.list_rooms()


@app.post("/rooms", status_code=201)
def post_room(payload: RoomCreate):
    return services.create_room(payload)


@app.patch("/rooms/{room_id}")
def patch_room(room_id: str, payload: RoomUpdate):
    return services.update_room(room_id, payload)


@app.get("/rooms/search")
def search_rooms(room_type: str | None = None, status: str | None = None, capacity_min: int | None = None):
    filters = {}
    if room_type:
        filters["room_type"] = room_type
    if status:
        filters["status"] = status
    if capacity_min is not None:
        filters["capacity_min"] = str(capacity_min)
    return services.search_rooms(filters)


@app.get("/classes")
def get_classes():
    return services.list_classes()


@app.post("/classes", status_code=201)
def post_class(payload: ClassCreate):
    return services.create_class(payload)


@app.patch("/classes/{class_id}")
def patch_class(class_id: str, payload: ClassUpdate):
    return services.update_class(class_id, payload)


@app.post("/classes/{class_id}/release")
def release_class(class_id: str, payload: ReleaseRequest):
    return services.release_class_day(class_id, payload)


@app.post("/rooms/reserve")
def reserve_room(payload: ReservationRequest):
    return services.reserve_room(payload)


@app.get("/dashboard")
def dashboard():
    return services.dashboard_overview()

