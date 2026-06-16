<script setup>
import { onMounted, reactive, ref } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, createMember, getMemberDetail } = useLoyaltyData()
const form = reactive({ name: '', phone: '', birthday: '2000-01-01' })

const detailVisible = ref(false)
const detailLoading = ref(false)
const memberDetail = ref(null)

onMounted(refreshAll)

async function submitMember() {
  await createMember({ ...form })
  Object.assign(form, { name: '', phone: '', birthday: '2000-01-01' })
}

async function openDetail(member) {
  detailVisible.value = true
  detailLoading.value = true
  memberDetail.value = null
  try {
    memberDetail.value = await getMemberDetail(member.id)
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detailVisible.value = false
  memberDetail.value = null
}

function formatDiscount(pct) {
  if (pct == null) return '—'
  return pct ? `${100 - pct}折` : '原价'
}

function benefitsList(arr) {
  if (!arr || !arr.length) return '—'
  return arr.join('、')
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Members</p>
        <h2>会员管理</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="two-column">
      <form class="panel" @submit.prevent="submitMember">
        <h3>新增会员</h3>
        <label>
          姓名
          <input v-model.trim="form.name" required type="text" />
        </label>
        <label>
          手机号
          <input v-model.trim="form.phone" required type="tel" />
        </label>
        <label>
          生日
          <input v-model="form.birthday" required type="date" />
        </label>
        <button class="primary-button" type="submit">创建会员</button>
      </form>

      <section class="panel wide-panel">
        <h3>会员列表</h3>
        <div class="data-table">
          <div class="table-head">
            <span>会员</span>
            <span>等级</span>
            <span>积分</span>
            <span>权益</span>
            <span>操作</span>
          </div>
          <div v-for="member in state.members" :key="member.id" class="table-row clickable" @click="openDetail(member)">
            <span>{{ member.name }}<small>{{ member.phone }}</small></span>
            <span class="tier-tag">{{ member.tier_name }}</span>
            <span>{{ member.points }}</span>
            <span>{{ member.benefits.join('、') }}</span>
            <span>
              <button class="link-btn" @click.stop="openDetail(member)">查看详情</button>
            </span>
          </div>
        </div>
      </section>
    </div>

    <Teleport to="body">
      <div v-if="detailVisible" class="modal-mask" @click.self="closeDetail">
        <div class="modal-panel">
          <div class="modal-header">
            <div>
              <h3 v-if="memberDetail">
                {{ memberDetail.name }}
                <small>{{ memberDetail.phone }}</small>
              </h3>
              <p v-if="memberDetail" class="modal-sub">生日：{{ memberDetail.birthday }} · 注册时间：{{ memberDetail.created_at }}</p>
            </div>
            <button class="close-btn" @click="closeDetail">×</button>
          </div>

          <div v-if="detailLoading" class="loading-placeholder">加载会员详情中...</div>

          <div v-else-if="memberDetail" class="modal-body">
            <div class="summary-cards">
              <div class="summary-card">
                <span>当前积分</span>
                <strong>{{ memberDetail.points }}</strong>
              </div>
              <div class="summary-card highlight">
                <span>当前等级</span>
                <strong>{{ memberDetail.tier_name }}</strong>
              </div>
              <div class="summary-card">
                <span>享受折扣</span>
                <strong>{{ formatDiscount(memberDetail.discount_percent) }}</strong>
              </div>
              <div class="summary-card">
                <span>生日加赠</span>
                <strong>{{ memberDetail.birthday_bonus }} 积分</strong>
              </div>
            </div>

            <div class="benefits-block">
              <h4>当前权益</h4>
              <div class="benefits-tags">
                <span v-for="b in memberDetail.benefits" :key="b" class="chip">{{ b }}</span>
              </div>
            </div>

            <div class="migration-block">
              <h4>等级变更历史</h4>
              <p class="migration-hint">可查看每次等级调整前后的权益对比变化。</p>

              <div v-if="!memberDetail.tier_migrations || !memberDetail.tier_migrations.length" class="empty-state">
                暂无等级变更记录
              </div>

              <div v-else class="migration-list">
                <div
                  v-for="m in memberDetail.tier_migrations"
                  :key="m.id"
                  class="migration-item"
                >
                  <div class="migration-head">
                    <span class="mig-reason">{{ m.reason }}</span>
                    <span class="mig-time">{{ m.created_at }}</span>
                  </div>

                  <div class="mig-compare">
                    <div class="mig-col mig-from">
                      <div class="col-title">变更前</div>
                      <div class="mig-tier-name" :class="{ dim: !m.from_tier_name }">
                        {{ m.from_tier_name || '（初始创建）' }}
                      </div>
                      <ul>
                        <li>
                          <label>门槛积分</label>
                          <span>{{ m.from_tier_min_points != null ? m.from_tier_min_points + ' 积分' : '—' }}</span>
                        </li>
                        <li>
                          <label>消费折扣</label>
                          <span>{{ formatDiscount(m.from_tier_discount_percent) }}</span>
                        </li>
                        <li>
                          <label>生日加赠</label>
                          <span>{{ m.from_tier_birthday_bonus != null ? m.from_tier_birthday_bonus + ' 积分' : '—' }}</span>
                        </li>
                        <li class="benefit-line">
                          <label>专属权益</label>
                          <span>{{ benefitsList(m.from_tier_benefits) }}</span>
                        </li>
                      </ul>
                    </div>

                    <div class="mig-arrow">
                      <span>→</span>
                    </div>

                    <div class="mig-col mig-to">
                      <div class="col-title">变更后</div>
                      <div class="mig-tier-name">{{ m.to_tier_name }}</div>
                      <ul>
                        <li>
                          <label>门槛积分</label>
                          <span>{{ m.to_tier_min_points }} 积分</span>
                        </li>
                        <li>
                          <label>消费折扣</label>
                          <span>{{ formatDiscount(m.to_tier_discount_percent) }}</span>
                        </li>
                        <li>
                          <label>生日加赠</label>
                          <span>{{ m.to_tier_birthday_bonus }} 积分</span>
                        </li>
                        <li class="benefit-line">
                          <label>专属权益</label>
                          <span>{{ benefitsList(m.to_tier_benefits) }}</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.tier-tag {
  display: inline-block;
  padding: 2px 10px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.table-row.clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.table-row.clickable:hover {
  background: #f9fafb;
}

.link-btn {
  border: none;
  background: transparent;
  color: #2563eb;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
}

.link-btn:hover {
  background: #eff6ff;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 1000;
  padding: 40px 20px;
  overflow-y: auto;
}

.modal-panel {
  background: white;
  border-radius: 14px;
  width: 100%;
  max-width: 860px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.2);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 22px 28px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(135deg, #f8fafc, #eef2ff);
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  color: #0f172a;
}

.modal-header h3 small {
  display: inline-block;
  margin-left: 10px;
  color: #64748b;
  font-weight: 400;
  font-size: 13px;
}

.modal-sub {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: #e2e8f0;
  color: #475569;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #cbd5e1;
}

.modal-body {
  padding: 24px 28px 28px;
}

.loading-placeholder {
  padding: 60px 28px;
  text-align: center;
  color: #64748b;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.summary-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
}

.summary-card.highlight {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-color: #fbbf24;
}

.summary-card span {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.summary-card strong {
  display: block;
  font-size: 20px;
  color: #0f172a;
}

.benefits-block {
  margin-bottom: 26px;
}

.benefits-block h4,
.migration-block h4 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #0f172a;
}

.benefits-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  background: #dbeafe;
  color: #1e40af;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 13px;
}

.migration-hint {
  color: #64748b;
  font-size: 12px;
  margin: 0 0 14px;
}

.empty-state {
  padding: 30px;
  background: #f8fafc;
  border-radius: 10px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.migration-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.migration-item {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.migration-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 8px;
}

.mig-reason {
  color: #0f172a;
  font-weight: 500;
  font-size: 14px;
}

.mig-time {
  color: #64748b;
  font-size: 12px;
}

.mig-compare {
  display: grid;
  grid-template-columns: 1fr 40px 1fr;
  gap: 0;
}

.mig-col {
  padding: 16px 18px;
}

.mig-from {
  background: #fff1f2;
}

.mig-to {
  background: #ecfdf5;
}

.col-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mig-from .col-title {
  color: #be123c;
}

.mig-to .col-title {
  color: #047857;
}

.mig-tier-name {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #0f172a;
}

.mig-tier-name.dim {
  color: #94a3b8;
  font-weight: 400;
  font-style: italic;
}

.mig-col ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mig-col li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.mig-col li label {
  color: #64748b;
  flex-shrink: 0;
}

.mig-col li span {
  color: #0f172a;
  text-align: right;
}

.benefit-line {
  align-items: flex-start;
}

.benefit-line span {
  max-width: 260px;
  white-space: normal;
}

.mig-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  color: #94a3b8;
  font-size: 22px;
  font-weight: bold;
}

@media (max-width: 720px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .mig-compare {
    grid-template-columns: 1fr;
  }
  .mig-arrow {
    padding: 6px 0;
    transform: rotate(90deg);
  }
}
</style>
