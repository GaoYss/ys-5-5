<script setup>
import { onMounted, ref } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, updateTier, moveTierOrder, previewDisableTier } = useLoyaltyData()

const confirmVisible = ref(false)
const confirmLoading = ref(false)
const confirmTarget = ref(null)
const confirmPreview = ref(null)

const migrationResult = ref(null)

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

function activeTiersCount() {
  return state.tiers.filter(t => t.active).length
}

async function handleToggleActive(tier) {
  if (tier.active) {
    if (activeTiersCount() <= 1) {
      state.error = '至少需要保留一个可用等级，无法停用最后一个可用等级'
      return
    }
    try {
      const preview = await previewDisableTier(tier.id)
      confirmTarget.value = tier
      confirmPreview.value = preview
      confirmVisible.value = true
    } catch (e) {
      state.error = e.message
    }
  } else {
    migrationResult.value = null
    const result = await updateTier(tier.id, { active: true })
    if (result && result.migrations_triggered !== undefined) {
      migrationResult.value = { tierName: tier.name, count: result.migrations_triggered, action: '启用' }
    }
  }
}

function cancelConfirm() {
  confirmVisible.value = false
  confirmTarget.value = null
  confirmPreview.value = null
}

async function executeDisable() {
  if (!confirmTarget.value) return
  confirmLoading.value = true
  try {
    const result = await updateTier(confirmTarget.value.id, { active: false })
    migrationResult.value = {
      tierName: confirmTarget.value.name,
      count: result.migrations_triggered,
      action: '停用'
    }
  } finally {
    confirmLoading.value = false
    confirmVisible.value = false
    confirmTarget.value = null
    confirmPreview.value = null
  }
}

async function handleMoveUp(tier) {
  if (!canMoveUp(tier)) return
  migrationResult.value = null
  await moveTierOrder(tier.id, 'up')
}

async function handleMoveDown(tier) {
  if (!canMoveDown(tier)) return
  migrationResult.value = null
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

    <div v-if="migrationResult" class="migration-result-bar">
      <span>
        已{{ migrationResult.action }}等级「{{ migrationResult.tierName }}」，
        <strong>{{ migrationResult.count }}</strong> 位会员完成了等级迁移。
      </span>
      <button class="dismiss-btn" @click="migrationResult = null">×</button>
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

    <Teleport to="body">
      <div v-if="confirmVisible" class="modal-mask" @click.self="cancelConfirm">
        <div class="confirm-panel">
          <h3>确认停用等级</h3>
          <div class="confirm-body">
            <p>
              即将停用等级「<strong>{{ confirmPreview?.tier_name }}</strong>」，
              该等级下有 <strong class="highlight-num">{{ confirmPreview?.affected_members }}</strong> 位会员将受到影响。
            </p>
            <p>停用后，这些会员将按当前积分平滑迁移到其他可用等级。新会员将不再分配此等级。</p>
            <p class="confirm-sub">当前可用等级数量：{{ confirmPreview?.active_tiers_count }}</p>
          </div>
          <div class="confirm-footer">
            <button class="btn-cancel" :disabled="confirmLoading" @click="cancelConfirm">取消</button>
            <button class="btn-danger" :disabled="confirmLoading" @click="executeDisable">
              {{ confirmLoading ? '处理中...' : '确认停用' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.hint {
  color: #6b7280;
  font-size: 13px;
  margin-top: 6px;
}

.migration-result-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #ecfdf5;
  border: 1px solid #6ee7b7;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #065f46;
}

.migration-result-bar strong {
  font-size: 18px;
  color: #047857;
}

.dismiss-btn {
  border: none;
  background: transparent;
  color: #6ee7b7;
  cursor: pointer;
  font-size: 18px;
  padding: 0 4px;
  line-height: 1;
}

.dismiss-btn:hover {
  color: #047857;
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

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.confirm-panel {
  background: white;
  border-radius: 14px;
  width: 100%;
  max-width: 460px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.2);
  overflow: hidden;
}

.confirm-panel h3 {
  margin: 0;
  padding: 20px 24px 0;
  font-size: 18px;
  color: #0f172a;
}

.confirm-body {
  padding: 16px 24px;
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}

.confirm-body p {
  margin: 0 0 8px;
}

.confirm-body p:last-child {
  margin-bottom: 0;
}

.highlight-num {
  font-size: 22px;
  color: #dc2626;
}

.confirm-sub {
  color: #6b7280;
  font-size: 13px;
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px 20px;
}

.btn-cancel {
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s;
}

.btn-cancel:hover:not(:disabled) {
  background: #f3f4f6;
}

.btn-danger {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: #dc2626;
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

.btn-cancel:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
