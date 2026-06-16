from datetime import date, datetime, timedelta

from fastapi import HTTPException, status

from app.repositories.loyalty_repository import LoyaltyRepository


class LoyaltyService:
    def __init__(self, repo: LoyaltyRepository | None = None) -> None:
        self.repo = repo or LoyaltyRepository()

    def _normalize_member(self, member: dict) -> dict:
        normalized = dict(member)
        benefits = normalized.get("benefits") or ""
        normalized["benefits"] = [item for item in benefits.split(";") if item]
        return normalized

    def _normalize_tier(self, tier: dict) -> dict:
        normalized = dict(tier)
        benefits = normalized.get("benefits") or ""
        normalized["benefits"] = [item for item in benefits.split(";") if item]
        return normalized

    def _normalize_tier_migration(self, mig: dict) -> dict:
        normalized = dict(mig)
        for prefix in ("from_tier_", "to_tier_"):
            key = prefix + "benefits"
            b = normalized.get(key) or ""
            if isinstance(b, str):
                normalized[key] = [item for item in b.split(";") if item] if b else []
        return normalized

    def _get_current_tier_snapshot(self, tier_id: int) -> dict | None:
        tier = self.repo.get_tier(tier_id)
        return dict(tier) if tier else None

    def _refresh_member_tier(self, member: dict, reason: str = "积分变更自动调整") -> dict:
        current_tier_id = member["tier_id"]
        current_tier_snapshot = self._get_current_tier_snapshot(current_tier_id)
        tier = self.repo.best_tier_for_points(member["points"])
        if current_tier_id != tier["id"]:
            self.repo.update_member_tier(member["id"], tier["id"])
            self.repo.add_tier_migration(
                member_id=member["id"],
                from_tier=current_tier_snapshot,
                to_tier=tier,
                reason=reason,
            )
        refreshed = self.repo.get_member(member["id"])
        if refreshed is None:
            raise HTTPException(status_code=404, detail="会员不存在")
        return self._normalize_member(refreshed)

    def _migrate_members_from_tier(self, tier_id: int, reason: str) -> list[dict]:
        migrations = []
        members = self.repo.list_members_in_tier(tier_id)
        for member in members:
            current_snapshot = self._get_current_tier_snapshot(tier_id)
            new_tier = self.repo.best_tier_for_points(member["points"])
            if new_tier["id"] == tier_id:
                active_tiers = [t for t in self.repo.list_tiers() if t.get("active", 1)]
                if active_tiers:
                    active_tiers.sort(key=lambda t: t["min_points"])
                    new_tier = active_tiers[0]
            if new_tier["id"] != tier_id:
                self.repo.update_member_tier(member["id"], new_tier["id"])
                mig = self.repo.add_tier_migration(
                    member_id=member["id"],
                    from_tier=current_snapshot,
                    to_tier=new_tier,
                    reason=reason,
                )
                migrations.append(mig)
        return migrations

    def list_members(self) -> list[dict]:
        return [self._normalize_member(member) for member in self.repo.list_members()]

    def create_member(self, name: str, phone: str, birthday: str) -> dict:
        try:
            datetime.strptime(birthday, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="生日格式必须为 YYYY-MM-DD") from exc

        tier = self.repo.best_tier_for_points(0)
        try:
            member = self._normalize_member(self.repo.create_member(name, phone, birthday, tier["id"]))
            self.repo.add_tier_migration(
                member_id=member["id"],
                from_tier=None,
                to_tier=tier,
                reason="新会员注册分配初始等级",
            )
            return member
        except Exception as exc:
            raise HTTPException(status_code=409, detail="手机号已存在或会员创建失败") from exc

    def get_member_or_404(self, member_id: int) -> dict:
        member = self.repo.get_member(member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="会员不存在")
        return self._normalize_member(member)

    def get_member_detail(self, member_id: int) -> dict:
        member = self.get_member_or_404(member_id)
        migrations = [
            self._normalize_tier_migration(m)
            for m in self.repo.list_tier_migrations(member_id)
        ]
        detail = dict(member)
        detail["tier_migrations"] = migrations
        return detail

    def list_tier_migrations(self, member_id: int) -> list[dict]:
        self.get_member_or_404(member_id)
        return [
            self._normalize_tier_migration(m)
            for m in self.repo.list_tier_migrations(member_id)
        ]

    def list_tiers(self) -> list[dict]:
        return [self._normalize_tier(tier) for tier in self.repo.list_tiers()]

    def get_tier_or_404(self, tier_id: int) -> dict:
        tier = self.repo.get_tier(tier_id)
        if tier is None:
            raise HTTPException(status_code=404, detail="等级不存在")
        return self._normalize_tier(tier)

    def update_tier(self, tier_id: int, payload: dict) -> dict:
        self.get_tier_or_404(tier_id)
        fields: dict = {}
        if payload.get("name") is not None:
            fields["name"] = payload["name"]
        if payload.get("min_points") is not None:
            fields["min_points"] = payload["min_points"]
        if payload.get("discount_percent") is not None:
            fields["discount_percent"] = payload["discount_percent"]
        if payload.get("birthday_bonus") is not None:
            fields["birthday_bonus"] = payload["birthday_bonus"]
        if payload.get("benefits") is not None:
            fields["benefits"] = ";".join(payload["benefits"])
        if payload.get("sort_order") is not None:
            fields["sort_order"] = payload["sort_order"]

        previous_active = None
        if payload.get("active") is not None:
            before = self.repo.get_tier(tier_id)
            previous_active = bool(before["active"]) if before else None
            fields["active"] = 1 if payload["active"] else 0

        updated = self.repo.update_tier(tier_id, fields)
        if updated is None:
            raise HTTPException(status_code=404, detail="等级不存在")

        migrations_count = 0
        if payload.get("active") is not None and previous_active is True and payload["active"] is False:
            migs = self._migrate_members_from_tier(tier_id, reason="原等级已停用，按积分平滑迁移")
            migrations_count = len(migs)
        elif payload.get("min_points") is not None:
            migs = []
            for member in self.repo.list_members_in_tier(tier_id):
                member_norm = self._normalize_member(member)
                self._refresh_member_tier(member_norm, reason=f"等级门槛调整（{payload['min_points']}积分）")
            migrations_count = len(migs)

        result = self._normalize_tier(updated)
        result["migrations_triggered"] = migrations_count
        return result

    def move_tier_order(self, tier_id: int, direction: str) -> list[dict]:
        tiers = self.repo.list_tiers()
        if len(tiers) < 2:
            raise HTTPException(status_code=400, detail="至少需要两个等级才能调整排序")
        idx = next((i for i, t in enumerate(tiers) if t["id"] == tier_id), None)
        if idx is None:
            raise HTTPException(status_code=404, detail="等级不存在")
        if direction == "up":
            if idx == 0:
                raise HTTPException(status_code=400, detail="已是最高等级，无法上移")
            swap_idx = idx - 1
        elif direction == "down":
            if idx == len(tiers) - 1:
                raise HTTPException(status_code=400, detail="已是最低等级，无法下移")
            swap_idx = idx + 1
        else:
            raise HTTPException(status_code=400, detail="direction 只能是 up 或 down")
        self.repo.swap_tier_order(tiers[idx]["id"], tiers[swap_idx]["id"])
        return self.list_tiers()

    def list_point_rules(self) -> list[dict]:
        return self.repo.list_point_rules()

    def earn_points(self, member_id: int, amount: float, rule_id: int) -> dict:
        member = self.get_member_or_404(member_id)
        rule = self.repo.get_point_rule(rule_id)
        if rule is None or not rule["active"]:
            raise HTTPException(status_code=404, detail="积分规则不存在或未启用")

        points = int(amount / rule["amount_per_point"] * rule["multiplier"])
        if points <= 0:
            raise HTTPException(status_code=400, detail="本次消费未达到积分门槛")

        new_points = member["points"] + points
        self.repo.update_member_points(member_id, new_points)
        tx = self.repo.add_transaction(member_id, "earn", points, f"{rule['name']}：消费 {amount:.2f} 元")
        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {"member": refreshed, "transaction": tx, "message": f"已增加 {points} 积分"}

    def list_gifts(self) -> list[dict]:
        return self.repo.list_gifts()

    def redeem_gift(self, member_id: int, gift_id: int) -> dict:
        member = self.get_member_or_404(member_id)
        gift = self.repo.get_gift(gift_id)
        if gift is None or not gift["active"]:
            raise HTTPException(status_code=404, detail="礼品不存在或不可兑换")
        if gift["stock"] <= 0:
            raise HTTPException(status_code=400, detail="礼品库存不足")
        if member["points"] < gift["points_cost"]:
            raise HTTPException(status_code=400, detail="会员积分不足")

        new_points = member["points"] - gift["points_cost"]
        self.repo.update_member_points(member_id, new_points)
        self.repo.reduce_gift_stock(gift_id)
        tx = self.repo.add_transaction(member_id, "redeem", -gift["points_cost"], f"兑换礼品：{gift['name']}")
        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {"member": refreshed, "transaction": tx, "message": f"已兑换 {gift['name']}"}

    def issue_birthday_vouchers(self, today: date | None = None) -> list[dict]:
        today = today or date.today()
        issued = []
        for member in self.repo.list_members():
            birthday = datetime.strptime(member["birthday"], "%Y-%m-%d").date()
            if birthday.month != today.month or birthday.day != today.day:
                continue
            if self.repo.birthday_voucher_exists(member["id"], today.year):
                continue

            tier = self.repo.best_tier_for_points(member["points"])
            voucher = self.repo.create_voucher(
                member["id"],
                "生日礼券",
                f"{100 - tier['discount_percent']}折生日饮品券 + {tier['birthday_bonus']}积分"
                if tier["discount_percent"]
                else f"生日饮品券 + {tier['birthday_bonus']}积分",
                (today + timedelta(days=30)).isoformat(),
            )
            new_points = member["points"] + tier["birthday_bonus"]
            self.repo.update_member_points(member["id"], new_points)
            self.repo.add_transaction(member["id"], "birthday", tier["birthday_bonus"], "生日礼遇积分")
            issued.append(voucher)
        return issued

    def list_vouchers(self) -> list[dict]:
        return self.repo.list_vouchers()

    def list_transactions(self, member_id: int | None = None) -> list[dict]:
        return self.repo.list_transactions(member_id)

    def dashboard(self) -> dict:
        members = self.repo.list_members()
        gifts = self.repo.list_gifts()
        vouchers = self.repo.list_vouchers()
        return {
            "members_count": len(members),
            "total_points": sum(member["points"] for member in members),
            "gifts_count": len([gift for gift in gifts if gift["active"]]),
            "active_vouchers": len([voucher for voucher in vouchers if voucher["status"] == "unused"]),
        }
