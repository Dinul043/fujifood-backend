"""
Address Routes — Customer saved delivery addresses.

Endpoints:
  GET    /addresses/         → List my addresses
  POST   /addresses/         → Add new address
  PATCH  /addresses/{id}     → Update address
  DELETE /addresses/{id}     → Delete address
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.user_address import UserAddress

router = APIRouter()


class AddressRequest(BaseModel):
    label: str = Field(default="Home", max_length=50)
    address_line1: str = Field(..., min_length=3, max_length=300)
    address_line2: Optional[str] = Field(None, max_length=300)
    city: str = Field(..., max_length=100)
    state: str = Field(default="Tamil Nadu", max_length=100)
    pincode: str = Field(..., min_length=5, max_length=10)
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    label: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    pincode: str
    is_default: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[AddressResponse], summary="List my addresses")
async def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    addrs = (
        db.query(UserAddress)
        .filter(UserAddress.user_id == current_user.id, UserAddress.tenant_id == current_user.tenant_id, UserAddress.deleted_at.is_(None))
        .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
        .all()
    )
    return [AddressResponse.model_validate(a) for a in addrs]


@router.post("/", response_model=AddressResponse, status_code=201, summary="Add address")
async def add_address(
    request: AddressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # If setting as default, unset others
    if request.is_default:
        db.query(UserAddress).filter(
            UserAddress.user_id == current_user.id, UserAddress.tenant_id == current_user.tenant_id, UserAddress.deleted_at.is_(None)
        ).update({"is_default": False})

    addr = UserAddress(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        label=request.label,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        pincode=request.pincode,
        is_default=request.is_default,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return AddressResponse.model_validate(addr)


@router.patch("/{addr_id}", response_model=AddressResponse, summary="Update address")
async def update_address(
    addr_id: int,
    request: AddressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    addr = db.query(UserAddress).filter(
        UserAddress.id == addr_id, UserAddress.user_id == current_user.id, UserAddress.deleted_at.is_(None)
    ).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")

    addr.label = request.label
    addr.address_line1 = request.address_line1
    addr.address_line2 = request.address_line2
    addr.city = request.city
    addr.state = request.state
    addr.pincode = request.pincode
    addr.is_default = request.is_default
    db.commit()
    db.refresh(addr)
    return AddressResponse.model_validate(addr)


@router.delete("/{addr_id}", summary="Delete address")
async def delete_address(
    addr_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    addr = db.query(UserAddress).filter(
        UserAddress.id == addr_id, UserAddress.user_id == current_user.id, UserAddress.deleted_at.is_(None)
    ).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")

    addr.deleted_at = datetime.utcnow()
    db.commit()
    return {"success": True}
