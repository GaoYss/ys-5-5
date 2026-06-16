import { http } from './http'

export const loyaltyApi = {
  dashboard: () => http.get('/members/dashboard'),
  members: () => http.get('/members'),
  createMember: (payload) => http.post('/members', payload),
  memberDetail: (memberId) => http.get(`/members/${memberId}/detail`),
  memberTierMigrations: (memberId) => http.get(`/members/${memberId}/tier-migrations`),
  rules: () => http.get('/points/rules'),
  earnPoints: (payload) => http.post('/points/earn', payload),
  transactions: () => http.get('/points/transactions'),
  gifts: () => http.get('/gifts'),
  redeemGift: (payload) => http.post('/gifts/redeem', payload),
  tiers: () => http.get('/tiers'),
  updateTier: (tierId, payload) => http.patch(`/tiers/${tierId}`, payload),
  moveTierOrder: (tierId, direction) => http.post(`/tiers/${tierId}/move?direction=${direction}`),
  previewDisableTier: (tierId) => http.get(`/tiers/${tierId}/disable-preview`),
  vouchers: () => http.get('/vouchers'),
  issueBirthdayVouchers: () => http.post('/vouchers/birthday/issue', {})
}
