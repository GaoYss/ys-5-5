<script setup>
import { onMounted } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, updateTier, moveTierOrder } = useLoyaltyData()

onMounted(refreshAll)

function tierIndex(id) {
  return state.tiers.findIndex(t => t.id === id)
}

function canMoveUp(tier) {
  return tierIndex(tier.id) > 0
}

function canMoveDown(tier) {
  return tierIndex(tier.id) < state.tiers.length - 1
}

async function handleToggleActive(tier) {
  await updateTier(tier.id, { active: !tier.active })
}

async function handleMoveUp(tier) {
  if (!canMoveUp(tier)) return
  await moveTierOrder(tier.id, 'up')
}

async function handleMoveDown(tier) {
  if (!canMoveDown(tier)) return
  await moveTierOrder(tier.id, 'down')
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Tier Benefits</p>
        <h2>等级权益</h2>
        <p class="hint">提示：按顺序上下调整等级显示，停用后新会员将不再分配该等级，已有会员会平滑迁移。</p>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="tier-timeline">
      <article v-for="tier in state.tiers" :key="tier.id" class="tier-item" :class="{ disabled: !tier.active }">
        <div class="tier-head">
          <div>
            <h3>
              {{ tier.name }}
              <span v-if="!tier.active" class="badge badge-off">已停用</span>
            </h3>
            <p>{{ tier.min_points }} 积分起</p>
          </div>
          <div class="tier-actions">
            <button
              class="icon-btn"
              title="上移"
              :disabled="!canMoveUp(tier)"
              @click="handleMoveUp(tier)"
            >▲</button>
            <button
              class="icon-btn"
              title="下移"
              :disabled="!canMoveDown(tier)"
              @click="handleMoveDown(tier)"
            >▼</button>
            <label class="switch" :title="tier.active ? '点击停用' : '点击启用'">
              <input type="checkbox" :checked="tier.active" @change="handleToggleActive(tier)" />
              <span class="slider"></span>
            </label>
          </div>
        </div>
        <strong>{{ tier.discount_percent ? `${100 - tier.discount_percent}折` : '原价' }}</strong>
        <span>生日加赠 {{ tier.birthday_bonus }} 积分</span>
        <ul>
          <li v-for="benefit in tier.benefits" :key="benefit">{{ benefit }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>

<style scoped>
.hint {
  color: #6b7280;
  font-size: 13px;
  margin-top: 6px;
}

.tier-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.tier-item.disabled {
  opacity: 0.55;
  background: repeating-linear-gradient(45deg, #f3f4f6, #f3f4f6 6px, #e5e7eb 6px, #e5e7eb 12px);
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 6px;
}

.badge-off {
  background: #fee2e2;
  color: #b91c1c;
}

.tier-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.15s;
}

.icon-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.icon-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  cursor: pointer;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  background: #d1d5db;
  border-radius: 999px;
  transition: 0.2s;
}

.slider::before {
  content: "";
  position: absolute;
  left: 3px;
  top: 3px;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  transition: 0.2s;
}

.switch input:checked + .slider {
  background: #10b981;
}

.switch input:checked + .slider::before {
  transform: translateX(20px);
}
</style>
