from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


app = FastAPI(
    title="MiniFactory Mock WMS",
    description="Mock WMS API for the MiniFactory AMR project",
    version="1.0.0",
)


class MissionStatus(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MissionCreate(BaseModel):
    robot_id: str = Field(
        default="AMR_01",
        min_length=1,
        max_length=50,
    )
    pickup: str = Field(
        min_length=1,
        max_length=100,
    )
    dropoff: str = Field(
        min_length=1,
        max_length=100,
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
    )

class MissionStatusUpdate(BaseModel):
    status: MissionStatus

class Mission(BaseModel):
    mission_id: UUID
    robot_id: str
    pickup: str
    dropoff: str
    priority: int
    status: MissionStatus
    created_at: datetime


missions: dict[UUID, Mission] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "UP",
        "service": "mock-wms",
    }


@app.post(
    "/missions",
    response_model=Mission,
    status_code=status.HTTP_201_CREATED,
)
def create_mission(request: MissionCreate) -> Mission:
    mission = Mission(
        mission_id=uuid4(),
        robot_id=request.robot_id,
        pickup=request.pickup,
        dropoff=request.dropoff,
        priority=request.priority,
        status=MissionStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
    )

    missions[mission.mission_id] = mission

    return mission


@app.get(
    "/missions",
    response_model=list[Mission],
)
def list_missions() -> list[Mission]:
    return sorted(
        missions.values(),
        key=lambda mission: (
            -mission.priority,
            mission.created_at,
        ),
    )


@app.get(
    "/missions/{mission_id}",
    response_model=Mission,
)
def get_mission(mission_id: UUID) -> Mission:
    mission = missions.get(mission_id)

    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    return mission

@app.patch(
    "/missions/{mission_id}/status",
    response_model=Mission,
)
def update_mission_status(
    mission_id: UUID,
    request: MissionStatusUpdate,
) -> Mission:
    mission = missions.get(mission_id)

    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    updated_mission = mission.model_copy(
        update={
            "status": request.status,
        }
    )

    missions[mission_id] = updated_mission

    return updated_mission	
