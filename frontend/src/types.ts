export type EntryType = 'income' | 'expense'

export interface User {
  id: number
  email: string
}

export interface Category {
  id: number
  name: string
  type: EntryType
  isDefault: boolean
}

export interface Transaction {
  id: number
  type: EntryType
  amount: number
  categoryId: number
  transactionDate: string
  note: string
}
