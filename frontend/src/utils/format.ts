export const formatMoney = (amount: number) => {
  const sign = amount < 0 ? '-' : ''
  const value = Math.abs(amount) / 100
  return `${sign}¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export const centsToYuan = (amount: number) => (amount / 100).toFixed(2)

export const yuanToCents = (value: string) => {
  const normalized = value.replace(/[^\d.]/g, '')
  if (!normalized) return 0
  return Math.round(Number(normalized) * 100)
}

export const formatMonth = (month: string) => {
  const [year, monthValue] = month.split('-')
  return `${year}年${monthValue}月`
}

export const formatDateLabel = (date: string) => {
  const [, month, day] = date.split('-')
  return `${month}-${day}`
}
