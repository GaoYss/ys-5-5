import { reactive } from 'vue'
import { loyaltyApi } from '../api/loyalty'

const state = reactive({
  loading: false,
  error: '',
  notice: '',
  dashboard: null,
  members: [],
  rules: [],
  gifts: [],
  tiers: [],
  vouchers: [],
  transactions: []
})

async function run(action, successMessage = '') {
  state.loading = true
  state.error = ''
  try {
    const result = await action()
    state.notice = successMessage
    return result
  } catch (error) {
    state.error = error.message
    throw error
  } finally {
    state.loading = false
  }
}

async function refreshAll() {
  state.loading = true
  state.error = ''
  try {
    const [dashboard, members, rules, gifts, tiers, vouchers, transactions] = await Promise.all([
      loyaltyApi.dashboard(),
      loyaltyApi.members(),
      loyaltyApi.rules(),
      loyaltyApi.gifts(),
      loyaltyApi.tiers(),
      loyaltyApi.vouchers(),
      loyaltyApi.transactions()
    ])
    Object.assign(state, { dashboard, members, rules, gifts, tiers, vouchers, transactions })
  } catch (error) {
    state.error = error.message
  } finally {
    state.loading = false
  }
}

export function useLoyaltyData() {
  return {
    state,
    refreshAll,
    async createMember(payload) {
      await run(() => loyaltyApi.createMember(payload), '会员已创建')
      await refreshAll()
    },
    async earnPoints(payload) {
      await run(() => loyaltyApi.earnPoints(payload), '积分已入账')
      await refreshAll()
    },
    async redeemGift(payload) {
      await run(() => loyaltyApi.redeemGift(payload), '礼品已兑换')
      await refreshAll()
    },
    async issueBirthdayVouchers() {
      const vouchers = await run(() => loyaltyApi.issueBirthdayVouchers(), '生日礼券发放完成')
      await refreshAll()
      return vouchers
    },
    async updateTier(tierId, payload) {
      const result = await run(() => loyaltyApi.updateTier(tierId, payload), '等级已更新')
      await refreshAll()
      return result
    },
    async previewDisableTier(tierId) {
      return await run(() => loyaltyApi.previewDisableTier(tierId))
    },
    async moveTierOrder(tierId, direction) {
      await run(() => loyaltyApi.moveTierOrder(tierId, direction), '排序已调整')
      await refreshAll()
    },
    async getMemberDetail(memberId) {
      return await run(() => loyaltyApi.memberDetail(memberId))
    },
    async getMemberTierMigrations(memberId) {
      return await run(() => loyaltyApi.memberTierMigrations(memberId))
    }
  }
}
