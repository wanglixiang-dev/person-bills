import { defineStore } from 'pinia'
import { ledgerApi, type TransactionPayload } from '../api/ledger'
import type { Category, CategoryMetric, EntryType, MonthlySummary, Transaction } from '../types'

const today = new Date()
const monthId = (offset = 0) => {
  const date = new Date(today.getFullYear(), today.getMonth() + offset, 1)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

interface LedgerState {
  currentMonth: string
  categories: Category[]
  transactions: Transaction[]
  summary: MonthlySummary
  categoryRatios: CategoryMetric[]
  categoryRanking: CategoryMetric[]
  sixMonthTrend: MonthlySummary[]
  filters: {
    category_id: number | null
    type: EntryType | ''
  }
  loading: boolean
  error: string
}

const emptySummary = (month: string): MonthlySummary => ({
  month,
  income_total: 0,
  expense_total: 0,
  balance: 0,
})

export const useLedgerStore = defineStore('ledger', {
  state: (): LedgerState => ({
    currentMonth: monthId(),
    categories: [],
    transactions: [],
    summary: emptySummary(monthId()),
    categoryRatios: [],
    categoryRanking: [],
    sixMonthTrend: [],
    filters: {
      category_id: null,
      type: '',
    },
    loading: false,
    error: '',
  }),
  getters: {
    monthTransactions: (state) => state.transactions,
    expenseCategories: (state) => state.categories.filter((category) => category.type === 'expense' && category.is_active),
    incomeCategories: (state) => state.categories.filter((category) => category.type === 'income' && category.is_active),
  },
  actions: {
    setMonth(month: string) {
      this.currentMonth = month
    },
    async shiftMonth(offset: number) {
      const [year, month] = this.currentMonth.split('-').map(Number)
      const next = new Date(year, month - 1 + offset, 1)
      this.currentMonth = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`
      await this.loadHomeData()
    },
    categoryName(categoryId: number) {
      return this.categories.find((category) => category.id === categoryId)?.name || '未分类'
    },
    categoriesByType(type: EntryType) {
      return this.categories.filter((category) => category.type === type && category.is_active)
    },
    async loadCategories(includeInactive = false) {
      this.categories = await ledgerApi.categories(includeInactive)
    },
    async loadHomeData() {
      this.loading = true
      this.error = ''
      try {
        const [categories, transactions, summary, ratios, ranking, trend] = await Promise.all([
          ledgerApi.categories(),
          ledgerApi.transactions({
            month: this.currentMonth,
            category_id: this.filters.category_id,
            type: this.filters.type,
          }),
          ledgerApi.summary(this.currentMonth),
          ledgerApi.ratios(this.currentMonth),
          ledgerApi.ranking(this.currentMonth),
          ledgerApi.trend(this.currentMonth),
        ])
        this.categories = categories
        this.transactions = transactions.items
        this.summary = summary
        this.categoryRatios = ratios.items
        this.categoryRanking = ranking.items
        this.sixMonthTrend = trend.items
      } catch (err: any) {
        this.error = err.message || '加载失败'
        throw err
      } finally {
        this.loading = false
      }
    },
    async createCategory(name: string, type: EntryType) {
      await ledgerApi.createCategory(name, type)
      await this.loadCategories(true)
    },
    async updateCategory(id: number, name: string, type: EntryType) {
      await ledgerApi.updateCategory(id, name, type)
      await this.loadCategories(true)
    },
    async deactivateCategory(id: number) {
      await ledgerApi.deactivateCategory(id)
      await this.loadCategories(true)
    },
    async saveTransaction(payload: TransactionPayload & { id?: number }) {
      if (payload.id) {
        await ledgerApi.updateTransaction(payload.id, payload)
      } else {
        await ledgerApi.createTransaction(payload)
      }
      await this.loadHomeData()
    },
    async deleteTransaction(id: number) {
      await ledgerApi.deleteTransaction(id)
      await this.loadHomeData()
    },
  },
})
