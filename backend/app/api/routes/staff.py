from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffRead, StaffAvailabilityUpdate

router = APIRouter()

@router.get("/available", response_model=List[StaffRead])
async def get_available_staff(
    platform_zone: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Staff).filter(Staff.is_available.is_(True))
    if platform_zone:
        query = query.filter(Staff.platform_zone == platform_zone)
    return query.order_by(Staff.name).all()

@router.get("", response_model=List[StaffRead])
async def list_staff(db: Session = Depends(get_db)):
    return db.query(Staff).order_by(Staff.name).all()

@router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(staff: StaffCreate, db: Session = Depends(get_db)):
    new_staff = Staff(**staff.dict())
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

@router.patch("/{id}/availability", response_model=StaffRead)
async def update_staff_availability(
    id: int,
    payload: StaffAvailabilityUpdate,
    db: Session = Depends(get_db),
):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff record not found")

    staff.is_available = payload.is_available
    db.commit()
    db.refresh(staff)
    return staff
