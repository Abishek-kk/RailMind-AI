from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.incident import (
    IncidentFalsePositiveRequest,
    IncidentRead,
    IncidentResolveRequest,
)
from app.services.incident_service import IncidentService

router = APIRouter()

@router.get("", response_model=List[IncidentRead])
async def list_incidents(
    camera_id: Optional[str] = None,
    incident_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    filters = {
        "camera_id": camera_id,
        "incident_type": incident_type,
        "risk_level": risk_level,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
    }
    return service.list_incidents({k: v for k, v in filters.items() if v is not None}, limit=limit)


@router.get("/{id}", response_model=IncidentRead)
async def get_incident(id: int, db: Session = Depends(get_db)):
    service = IncidentService(db)
    incident = service.get_incident(id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident record not found")
    return incident


@router.post("/{id}/acknowledge", response_model=IncidentRead)
async def acknowledge_incident(id: int, db: Session = Depends(get_db)):
    service = IncidentService(db)
    incident = service.acknowledge_incident(id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident record not found")
    return incident


@router.post("/{id}/resolve", response_model=IncidentRead)
async def resolve_incident(
    id: int,
    payload: IncidentResolveRequest,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incident = service.resolve_incident(id, payload.resolution_notes)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident record not found")
    return incident


@router.post("/{id}/false-positive", response_model=IncidentRead)
async def false_positive_incident(
    id: int,
    payload: IncidentFalsePositiveRequest,
    db: Session = Depends(get_db),
):
    service = IncidentService(db)
    incident = service.mark_false_positive(id, payload.staff_id, payload.notes)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident record not found")
    return incident
