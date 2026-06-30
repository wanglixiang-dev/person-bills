import { apiRequest } from './client'
import type { Category, CategoryMetric, EntryType, MonthlySummary, Transaction } from '../types'

export interface TransactionPayload {
  type: EntryType
  amount: number
  category_id: number
  transaction_date: string
  note: string | null
}

export const ledgerApi = {
  categories: (includeInactive = false) => apiRequest<Category[]>(`/categories?include_inactive=${includeInactive}`),
  createCategory: (name: string, type: EntryType) =>
    apiRequest<Category>('/categories', { method: 'POST', body: JSON.stringify({ name, type }) }),
  updateCategory: (id: number, name: string, type: EntryType) =>
    apiRequest<Category>(`/categories/${id}`, { method: 'PATCH', body: JSON.stringify({ name, type }) }),
  deactivateCategory: (id: number) => apiRequest<{ message: string }>(`/categories/${id}`, { method: 'DELETE' }),
  transactions: (params: { month?: string; category_id?: number | null; type?: EntryType | '' }) => {
    const search = new URLSearchParams()
    if (params.month) search.set('month', params.month)
    if (params.category_id) search.set('category_id', String(params.category_id))
    if (params.type) search.set('type', params.type)
    return apiRequest<{ items: Transaction[]; total: number; page: number; page_size: number }>(`/transactions?${search}`)
  },
  createTransaction: (payload: TransactionPayload) =>
    apiRequest<Transaction>('/transactions', { method: 'POST', body: JSON.stringify(payload) }),
  updateTransaction: (id: number, payload: TransactionPayload) =>
    apiRequest<Transaction>(`/transactions/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteTransaction: (id: number) => apiRequest<{ message: string }>(`/transactions/${id}`, { method: 'DELETE' }),
  summary: (month: string) => apiRequest<MonthlySummary>(`/reports/monthly-summary?month=${month}`),
  ratios: (month: string) => apiRequest<{ month: string; items: CategoryMetric[] }>(`/reports/category-expense-ratio?month=${month}`),
  ranking: (month: string) =>
    apiRequest<{ month: string; items: CategoryMetric[] }>(`/reports/category-expense-ranking?month=${month}`),
  trend: (month: string) => apiRequest<{ items: MonthlySummary[] }>(`/reports/six-month-trend?month=${month}`),
}
