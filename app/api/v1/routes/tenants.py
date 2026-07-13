"""
Tenant Routes — Internal provisioning API.

These endpoints are for the FujiFood operations team ONLY.
They are NOT public. Access is restricted to platform_admin role (future)
or internal API keys.

Endpoints:
  POST   /tenants/provision    → Provision a new tenant (full setup)
  GET    /tenants              → List all tenants
  GET    /tenants/{id}         → Get tenant details
  PATCH  /tenants/{id}         → Update tenant
  POST   /tenants/{id}/activate   → Activate tenant
  POST   /tenants/{id}/suspend    → Suspend tenant
  POST   /tenants/{id}/cancel     → Cancel tenant
  DELETE /tenants/{id}         → Soft delete tenant
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tenant import (
    ProvisionTenantRequest,
    UpdateTenantRequest,
    TenantResponse,
    TenantListResponse,
    ProvisionTenantResponse,
    RestaurantSummaryResponse,
)
from app.schemas.auth import ErrorResponse
from app.services.tenant_service import TenantService

router = APIRouter()


@router.post(
    "/provision",
    response_model=ProvisionTenantResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Provision a new tenant",
    description=(
        "Complete tenant provisioning — creates tenant, restaurant, theme, "
        "and admin user in one atomic operation. Internal use only."
    ),
)
async def provision_tenant(
    request: ProvisionTenantRequest,
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    result, error = service.provision_tenant(request)

    if error:
        status_code = status.HTTP_409_CONFLICT if "already" in error else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error)

    tenant = result["tenant"]
    restaurant = result["restaurant"]
    admin_user = result["admin_user"]

    return ProvisionTenantResponse(
        tenant=TenantResponse(
            id=tenant.id,
            uuid=tenant.uuid,
            name=tenant.name,
            slug=tenant.slug,
            custom_domain=tenant.custom_domain,
            status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
            plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
            owner_name=tenant.owner_name,
            owner_email=tenant.owner_email,
            owner_phone=tenant.owner_phone,
            is_verified=tenant.is_verified,
            onboarding_notes=tenant.onboarding_notes,
            created_at=str(tenant.created_at),
            updated_at=str(tenant.updated_at),
        ),
        restaurant=RestaurantSummaryResponse(
            id=restaurant.id,
            uuid=restaurant.uuid,
            name=restaurant.name,
            city=restaurant.city,
            is_online=restaurant.is_online,
            is_published=restaurant.is_published,
        ),
        admin_user_id=admin_user.id,
        admin_phone=admin_user.phone,
        storefront_url=result["storefront_url"],
    )


@router.get(
    "",
    response_model=TenantListResponse,
    summary="List all tenants",
    description="Paginated list of tenants with optional status filter.",
)
async def list_tenants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    tenants, total = service.list_tenants(page, page_size, status_filter)

    return TenantListResponse(
        tenants=[
            TenantResponse(
                id=t.id,
                uuid=t.uuid,
                name=t.name,
                slug=t.slug,
                custom_domain=t.custom_domain,
                status=t.status.value if hasattr(t.status, 'value') else t.status,
                plan=t.plan.value if hasattr(t.plan, 'value') else t.plan,
                owner_name=t.owner_name,
                owner_email=t.owner_email,
                owner_phone=t.owner_phone,
                is_verified=t.is_verified,
                onboarding_notes=t.onboarding_notes,
                created_at=str(t.created_at),
                updated_at=str(t.updated_at),
            )
            for t in tenants
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get tenant details",
)
async def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant = service.get_tenant_by_id(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(
        id=tenant.id,
        uuid=tenant.uuid,
        name=tenant.name,
        slug=tenant.slug,
        custom_domain=tenant.custom_domain,
        status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
        plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
        owner_name=tenant.owner_name,
        owner_email=tenant.owner_email,
        owner_phone=tenant.owner_phone,
        is_verified=tenant.is_verified,
        onboarding_notes=tenant.onboarding_notes,
        created_at=str(tenant.created_at),
        updated_at=str(tenant.updated_at),
    )


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update tenant details",
)
async def update_tenant(
    tenant_id: int,
    request: UpdateTenantRequest,
    db: Session = Depends(get_db),
):
    service = TenantService(db)
    tenant, error = service.update_tenant(tenant_id, request)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return TenantResponse(
        id=tenant.id,
        uuid=tenant.uuid,
        name=tenant.name,
        slug=tenant.slug,
        custom_domain=tenant.custom_domain,
        status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
        plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
        owner_name=tenant.owner_name,
        owner_email=tenant.owner_email,
        owner_phone=tenant.owner_phone,
        is_verified=tenant.is_verified,
        onboarding_notes=tenant.onboarding_notes,
        created_at=str(tenant.created_at),
        updated_at=str(tenant.updated_at),
    )


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Activate tenant",
    description="Set tenant status to active — enables their storefront.",
)
async def activate_tenant(tenant_id: int, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant, error = service.activate_tenant(tenant_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return TenantResponse(
        id=tenant.id, uuid=tenant.uuid, name=tenant.name, slug=tenant.slug,
        custom_domain=tenant.custom_domain,
        status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
        plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
        owner_name=tenant.owner_name, owner_email=tenant.owner_email,
        owner_phone=tenant.owner_phone, is_verified=tenant.is_verified,
        onboarding_notes=tenant.onboarding_notes,
        created_at=str(tenant.created_at), updated_at=str(tenant.updated_at),
    )


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Suspend tenant",
    description="Suspend tenant — disables their storefront.",
)
async def suspend_tenant(tenant_id: int, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant, error = service.suspend_tenant(tenant_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return TenantResponse(
        id=tenant.id, uuid=tenant.uuid, name=tenant.name, slug=tenant.slug,
        custom_domain=tenant.custom_domain,
        status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
        plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
        owner_name=tenant.owner_name, owner_email=tenant.owner_email,
        owner_phone=tenant.owner_phone, is_verified=tenant.is_verified,
        onboarding_notes=tenant.onboarding_notes,
        created_at=str(tenant.created_at), updated_at=str(tenant.updated_at),
    )


@router.post(
    "/{tenant_id}/cancel",
    response_model=TenantResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Cancel tenant subscription",
)
async def cancel_tenant(tenant_id: int, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant, error = service.cancel_tenant(tenant_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return TenantResponse(
        id=tenant.id, uuid=tenant.uuid, name=tenant.name, slug=tenant.slug,
        custom_domain=tenant.custom_domain,
        status=tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
        plan=tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan,
        owner_name=tenant.owner_name, owner_email=tenant.owner_email,
        owner_phone=tenant.owner_phone, is_verified=tenant.is_verified,
        onboarding_notes=tenant.onboarding_notes,
        created_at=str(tenant.created_at), updated_at=str(tenant.updated_at),
    )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}},
    summary="Soft delete tenant",
    description="Soft deletes the tenant and associated restaurant data.",
)
async def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    service = TenantService(db)
    success, error = service.delete_tenant(tenant_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return {"success": True, "message": "Tenant deleted successfully"}
