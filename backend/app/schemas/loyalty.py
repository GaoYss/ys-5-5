from pydantic import BaseModel, Field


class Tier(BaseModel):
    id: int
    name: str
    min_points: int
    discount_percent: int
    birthday_bonus: int
    benefits: list[str]
    sort_order: int
    active: bool


class TierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    min_points: int | None = Field(default=None, ge=0)
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    birthday_bonus: int | None = Field(default=None, ge=0)
    benefits: list[str] | None = None
    sort_order: int | None = Field(default=None, ge=0)
    active: bool | None = None


class TierUpdateResult(BaseModel):
    id: int
    name: str
    min_points: int
    discount_percent: int
    birthday_bonus: int
    benefits: list[str]
    sort_order: int
    active: bool
    migrations_triggered: int


class TierDisablePreview(BaseModel):
    tier_id: int
    tier_name: str
    affected_members: int
    active_tiers_count: int


class TierMigration(BaseModel):
    id: int
    member_id: int
    from_tier_id: int | None = None
    from_tier_name: str | None = None
    from_tier_min_points: int | None = None
    from_tier_discount_percent: int | None = None
    from_tier_birthday_bonus: int | None = None
    from_tier_benefits: list[str] | None = None
    to_tier_id: int
    to_tier_name: str
    to_tier_min_points: int
    to_tier_discount_percent: int
    to_tier_birthday_bonus: int
    to_tier_benefits: list[str]
    reason: str
    created_at: str


class Member(BaseModel):
    id: int
    name: str
    phone: str
    birthday: str
    points: int
    tier_id: int
    tier_name: str
    discount_percent: int
    birthday_bonus: int
    benefits: list[str]
    created_at: str


class MemberDetail(BaseModel):
    id: int
    name: str
    phone: str
    birthday: str
    points: int
    tier_id: int
    tier_name: str
    discount_percent: int
    birthday_bonus: int
    benefits: list[str]
    created_at: str
    tier_migrations: list[TierMigration]


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    phone: str = Field(min_length=6, max_length=20)
    birthday: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class PointRule(BaseModel):
    id: int
    name: str
    description: str
    amount_per_point: float
    multiplier: float
    active: bool


class EarnPointsRequest(BaseModel):
    member_id: int
    amount: float = Field(gt=0)
    rule_id: int


class Gift(BaseModel):
    id: int
    name: str
    points_cost: int
    stock: int
    description: str
    active: bool


class RedeemGiftRequest(BaseModel):
    member_id: int
    gift_id: int


class Transaction(BaseModel):
    id: int
    member_id: int
    member_name: str | None = None
    type: str
    points: int
    note: str
    created_at: str


class Voucher(BaseModel):
    id: int
    member_id: int
    member_name: str | None = None
    title: str
    value: str
    status: str
    issued_at: str
    expires_at: str


class OperationResult(BaseModel):
    member: Member
    transaction: Transaction | None = None
    voucher: Voucher | None = None
    message: str


class Dashboard(BaseModel):
    members_count: int
    total_points: int
    gifts_count: int
    active_vouchers: int
