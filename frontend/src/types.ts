export type EntryType = 'income' | 'expense'

export interface User {
  id: number
  email: string
}

export interface Category {
  id: number
  name: string
  type: EntryType
  is_default: boolean
  is_active: boolean
}

export interface Transaction {
  id: number
  type: EntryType
  amount: number
  category_id: number
  category_name: string
  transaction_date: string
  note: string
}

export interface MonthlySummary {
  month: string
  income_total: number
  expense_total: number
  balance: number
}

export interface CategoryMetric {
  category_id: number
  category_name: string
  amount: number
  ratio: number
  rank?: number
}
