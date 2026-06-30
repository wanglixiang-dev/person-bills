import { defineStore } from 'pinia'
import type { Category, EntryType, Transaction } from '../types'

const today = new Date()
const monthId = (offset = 0) => {
  const date = new Date(today.getFullYear(), today.getMonth() + offset, 1)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}
const dateInMonth = (month: string, day: number) => `${month}-${String(day).padStart(2, '0')}`

interface LedgerState {
  currentMonth: string
  categories: Category[]
  transactions: Transaction[]
  nextCategoryId: number
  nextTransactionId: number
}

export const useLedgerStore = defineStore('ledger', {
  state: (): LedgerState => {
    const current = monthId()
    const previous = monthId(-1)
    return {
      currentMonth: current,
      categories: [
        { id: 1, name: '餐饮', type: 'expense', isDefault: true },
        { id: 2, name: '交通', type: 'expense', isDefault: true },
        { id: 3, name: '购物', type: 'expense', isDefault: true },
        { id: 4, name: '娱乐', type: 'expense', isDefault: true },
        { id: 5, name: '住房', type: 'expense', isDefault: true },
        { id: 6, name: '收入', type: 'income', isDefault: true },
        { id: 7, name: '设计设备', type: 'expense', isDefault: false },
      ],
      transactions: [
        { id: 1, type: 'income', amount: 800000, categoryId: 6, transactionDate: dateInMonth(current, 1), note: '工资' },
        { id: 2, type: 'expense', amount: 3800, categoryId: 1, transactionDate: dateInMonth(current, 5), note: '午餐' },
        { id: 3, type: 'expense', amount: 6200, categoryId: 1, transactionDate: dateInMonth(current, 8), note: '朋友聚餐' },
        { id: 4, type: 'expense', amount: 600, categoryId: 2, transactionDate: dateInMonth(current, 9), note: '地铁' },
        { id: 5, type: 'expense', amount: 129900, categoryId: 3, transactionDate: dateInMonth(current, 12), note: '耳机' },
        { id: 6, type: 'expense', amount: 4200, categoryId: 4, transactionDate: dateInMonth(current, 16), note: '电影' },
        { id: 7, type: 'expense', amount: 260000, categoryId: 5, transactionDate: dateInMonth(current, 20), note: '房租' },
        { id: 8, type: 'income', amount: 120000, categoryId: 6, transactionDate: dateInMonth(previous, 4), note: '兼职收入' },
        { id: 9, type: 'expense', amount: 4800, categoryId: 1, transactionDate: dateInMonth(previous, 7), note: '早餐和咖啡' },
        { id: 10, type: 'expense', amount: 29900, categoryId: 7, transactionDate: dateInMonth(previous, 11), note: '手绘板配件' },
      ],
      nextCategoryId: 8,
      nextTransactionId: 11,
    }
  },
  getters: {
    monthTransactions: (state) =>
      state.transactions
        .filter((item) => item.transactionDate.startsWith(state.currentMonth))
        .sort((a, b) => b.transactionDate.localeCompare(a.transactionDate) || b.id - a.id),
    expenseCategories: (state) => state.categories.filter((category) => category.type === 'expense'),
    incomeCategories: (state) => state.categories.filter((category) => category.type === 'income'),
    summary(): { income: number; expense: number; balance: number } {
      const income = this.monthTransactions
        .filter((item) => item.type === 'income')
        .reduce((sum, item) => sum + item.amount, 0)
      const expense = this.monthTransactions
        .filter((item) => item.type === 'expense')
        .reduce((sum, item) => sum + item.amount, 0)
      return { income, expense, balance: income - expense }
    },
    categoryRatios(): Array<{ name: string; amount: number; ratio: number }> {
      const totals = new Map<number, number>()
      this.monthTransactions
        .filter((item) => item.type === 'expense')
        .forEach((item) => totals.set(item.categoryId, (totals.get(item.categoryId) || 0) + item.amount))
      const totalExpense = Array.from(totals.values()).reduce((sum, amount) => sum + amount, 0)
      if (!totalExpense) return []
      return Array.from(totals.entries())
        .map(([categoryId, amount]) => ({
          name: this.categories.find((category) => category.id === categoryId)?.name || '未分类',
          amount,
          ratio: Number(((amount / totalExpense) * 100).toFixed(1)),
        }))
        .sort((a, b) => b.amount - a.amount)
    },
  },
  actions: {
    setMonth(month: string) {
      this.currentMonth = month
    },
    shiftMonth(offset: number) {
      const [year, month] = this.currentMonth.split('-').map(Number)
      const next = new Date(year, month - 1 + offset, 1)
      this.currentMonth = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`
    },
    categoryName(categoryId: number) {
      return this.categories.find((category) => category.id === categoryId)?.name || '未分类'
    },
    categoriesByType(type: EntryType) {
      return this.categories.filter((category) => category.type === type)
    },
    createCategory(name: string, type: EntryType) {
      const normalized = name.trim()
      if (!normalized) return
      const exists = this.categories.some((category) => category.type === type && category.name === normalized)
      if (exists) return
      this.categories.push({ id: this.nextCategoryId++, name: normalized, type, isDefault: false })
    },
    saveTransaction(payload: Omit<Transaction, 'id'> & { id?: number }) {
      if (payload.id) {
        const index = this.transactions.findIndex((item) => item.id === payload.id)
        if (index >= 0) this.transactions[index] = { ...payload, id: payload.id }
        return
      }
      this.transactions.unshift({ ...payload, id: this.nextTransactionId++ })
    },
    deleteTransaction(id: number) {
      this.transactions = this.transactions.filter((item) => item.id !== id)
    },
  },
})
