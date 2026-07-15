"""
Staff Routes — Owner manages restaurant staff accounts.

Only accessible by restaurant_admin + is_owner = True.

Endpoints:
  GET    /staff/           → List all staff for this tenant
  POST   /staff/           → Create a new staff account
  PATCH  /staff/{id}       → Update staff (name, phone, password, active status)
  DELETE /staff/{id}       → Deactivate staff (soft disable — can't login)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import require_role
from app.models.user import User, UserRole, UserStatus
from app.core.security import hash_password

router = APIRouter()


# ─── Request/Response Schemas ─────────────────────────────────────

class CreateStaffRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class UpdateStaffRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    id: int
    name: Optional[str]
    phone: str
    email: Optional[str]
    is_active: bool
    created_at: Optional[str]

    class Config:
        from_attributes = True


# ─── Helper: Require Owner ────────────────────────────────────────

def _require_owner(current_user: User = Depends(require_role("restaurant_admin"))):
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Only the restaurant owner can manage staff")
    return current_user


# ─── List Staff ───────────────────────────────────────────────────

@router.get("/", response_model=list[StaffResponse], summary="List all staff")
async def list_staff(
    current_user: User = Depends(_require_owner),
    db: Session = Depends(get_db),
):
    staff = (
        db.query(User)
        .filter(
            User.tenant_id == current_user.tenant_id,
            User.role == UserRole.RESTAURANT_ADMIN,
            User.is_owner == False,
            User.deleted_at.is_(None),
        )
        .order_by(User.created_at.desc())
        .all()
    )
    return [
        StaffResponse(
            id=s.id,
            name=s.name,
            phone=s.phone,
            email=s.email,
            is_active=s.is_active,
            created_at=str(s.created_at) if s.created_at else None,
        )
        for s in staff
    ]


# ─── Create Staff ────────────────────────────────────────────────

@router.post("/", response_model=StaffResponse, status_code=201, summary="Add staff member")
async def create_staff(
    request: CreateStaffRequest,
    current_user: User = Depends(_require_owner),
    db: Session = Depends(get_db),
):
    # Check if phone already exists in this tenant
    exists = (
        db.query(User)
        .filter(
            User.tenant_id == current_user.tenant_id,
            User.phone == request.phone,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="A user with this phone already exists")

    user = User(
        tenant_id=current_user.tenant_id,
        name=request.name,
        phone=request.phone,
        email=request.email,
        password_hash=hash_password(request.password),
        role=UserRole.RESTAURANT_ADMIN,
        status=UserStatus.ACTIVE,
        phone_verified=True,
        is_active=True,
        is_owner=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return StaffResponse(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        is_active=user.is_active,
        created_at=str(user.created_at),
    )


# ─── Update Staff ────────────────────────────────────────────────

@router.patch("/{staff_id}", response_model=StaffResponse, summary="Update staff member")
async def update_staff(
    staff_id: int,
    request: UpdateStaffRequest,
    current_user: User = Depends(_require_owner),
    db: Session = Depends(get_db),
):
    staff = (
        db.query(User)
        .filter(
            User.id == staff_id,
            User.tenant_id == current_user.tenant_id,
            User.role == UserRole.RESTAURANT_ADMIN,
            User.is_owner == False,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    if request.name is not None:
        staff.name = request.name
    if request.phone is not None:
        staff.phone = request.phone
    if request.password is not None:
        staff.password_hash = hash_password(request.password)
    if request.is_active is not None:
        staff.is_active = request.is_active

    db.commit()
    db.refresh(staff)

    return StaffResponse(
        id=staff.id,
        name=staff.name,
        phone=staff.phone,
        email=staff.email,
        is_active=staff.is_active,
        created_at=str(staff.created_at),
    )


# ─── Delete (Deactivate) Staff ───────────────────────────────────

@router.delete("/{staff_id}", summary="Remove staff member")
async def delete_staff(
    staff_id: int,
    current_user: User = Depends(_require_owner),
    db: Session = Depends(get_db),
):
    staff = (
        db.query(User)
        .filter(
            User.id == staff_id,
            User.tenant_id == current_user.tenant_id,
            User.role == UserRole.RESTAURANT_ADMIN,
            User.is_owner == False,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # Soft deactivate — they can't login anymore
    staff.is_active = False
    staff.status = UserStatus.SUSPENDED
    db.commit()

    return {"success": True, "message": f"Staff member {staff.name} has been removed"}
