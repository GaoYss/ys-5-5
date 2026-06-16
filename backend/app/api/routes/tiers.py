from fastapi import APIRouter, HTTPException

from app.schemas.loyalty import Tier, TierUpdate
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("", response_model=list[Tier])
def list_tiers() -> list[dict]:
    return service.list_tiers()


@router.patch("/{tier_id}", response_model=Tier)
def update_tier(tier_id: int, payload: TierUpdate) -> dict:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供需要更新的字段")
    return service.update_tier(tier_id, data)


@router.post("/{tier_id}/move", response_model=list[Tier])
def move_tier_order(tier_id: int, direction: str = "up") -> list[dict]:
    return service.move_tier_order(tier_id, direction)
