// Clean reimplementation below ----------------------------------------------
import axios, { AxiosRequestConfig } from 'axios'

export interface Transaction {
  id: string
  account: string
  booking_date?: string | null
  statement_number?: string | null
  transaction_number?: string | null
  counterparty_account?: string | null
  counterparty_name?: string | null
  street_number?: string | null
  postal_code_city?: string | null
  transaction_type?: string | null
  value_date?: string | null
  amount: number
  currency?: string | null
  bic?: string | null
  country_code?: string | null
  notes?: string | null
  category?: string | null
}

export interface Category {
  id: string
  name: string
  slug?: string
  expanded_phrase?: string | null
  aliases?: string[]
}

export interface CategoryInput {
  name: string
  expanded_phrase?: string | null
  aliases?: string[]
}

const BACKEND_DIRECT = process.env.API_BASE_URL_INTERNAL || process.env.API_BASE_URL || 'http://localhost:8000'
const API_BASE_URL = typeof window === 'undefined' ? BACKEND_DIRECT : '/api'
const apiClient = axios.create({ baseURL: API_BASE_URL })

if (process.env.NODE_ENV !== 'production') {
  apiClient.interceptors.request.use((cfg) => {
    console.debug('[api.request]', cfg.method?.toUpperCase(), (cfg.baseURL || '') + (cfg.url || ''))
    return cfg
  })
  apiClient.interceptors.response.use(
    (resp) => { console.debug('[api.response]', resp.status, resp.config.method?.toUpperCase(), (resp.config.baseURL || '') + (resp.config.url || '')); return resp },
    (error) => { const cfg = error.config as AxiosRequestConfig | undefined; console.warn('[api.error]', cfg?.method?.toUpperCase(), (cfg?.baseURL || '') + (cfg?.url || ''), error.response?.status, error.message); return Promise.reject(error) }
  )
}

export async function listCategories(): Promise<Category[]> { return (await apiClient.get<Category[]>('/categories/')).data }
export async function createCategory(input: CategoryInput): Promise<Category> { return (await apiClient.post<Category>('/categories/', input)).data }
export async function updateCategoryApi(id: string, input: Partial<CategoryInput>): Promise<Category> { return (await apiClient.put<Category>(`/categories/${id}`, input)).data }
export async function assignTransactionCategory(transactionId: string, category: string): Promise<void> { await apiClient.post(`/categories/assign/${transactionId}`, { category }) }
export async function bulkAssignTransactionCategory(transactionIds: string[], category: string): Promise<number> { return (await apiClient.post<{ updated: number }>(`/categories/assign/bulk`, { transaction_ids: transactionIds, category })).data.updated }

export function optimisticUpdateTransactionCategories(
  mutate: (key?: any, data?: any, opts?: any) => Promise<any>,
  predicate: (tx: Transaction) => boolean,
  updater: (old: Transaction) => Transaction,
) {
  mutate((key: any) => Array.isArray(key) && key[0] === 'transactions', (data: any) => {
    if (!data) return data
    const copy = { ...data }
    copy.items = data.items.map((tx: Transaction) => predicate(tx) ? updater(tx) : tx)
    return copy
  }, { revalidate: false })
}

export interface PaginationResponse<T> { items: T[]; offset: number; limit: number; total?: number; has_more: boolean; next?: number | null; previous?: number | null }
export interface TransactionListFilters { counterparty_name_ilike?: string; transaction_type_ilike?: string; notes_ilike?: string; category_id?: string; has_category?: boolean }

export async function uploadTransactions(file: File): Promise<Transaction[]> { const form = new FormData(); form.append('file', file); return (await apiClient.post<Transaction[]>('/transactions/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })).data }
export async function listTransactions(offset = 0, limit = 100, sortBy?: string, sortDir?: 'asc' | 'desc', filters?: TransactionListFilters): Promise<PaginationResponse<Transaction>> {
  const params: Record<string, any> = { offset, limit }
  if (sortBy) params.sort_by = sortBy
  if (sortDir) params.sort_dir = sortDir
  if (filters) for (const [k, v] of Object.entries(filters)) if (v !== undefined && v !== null && v !== '') params[k] = v
  return (await apiClient.get<PaginationResponse<Transaction>>('/transactions/', { params })).data
}
export async function getTransaction(id: string): Promise<Transaction> { return (await apiClient.get<Transaction>(`/transactions/${id}`)).data }
export async function setTransactionNumber(id: string, number: number): Promise<Transaction> { return (await apiClient.patch<Transaction>(`/transactions/${id}/set-number`, { number })).data }

export interface TransactionStats { total: number; with_category: number; without_category: number }
export async function getTransactionStats(): Promise<TransactionStats> { return (await apiClient.get<TransactionStats>('/transactions/stats')).data }