import axios from 'axios';

/**
 * Interface mirroring the Transaction model from the backend. Optional fields are
 * marked accordingly. Use this for strong typing when interacting with the API.
 */
export interface Transaction {
  // Backend uses UUID (string). Make required for consistency.
  id: string;
  account: string;
  booking_date?: string | null;
  statement_number?: string | null;
  transaction_number?: string | null;
  counterparty_account?: string | null;
  counterparty_name?: string | null;
  street_number?: string | null;
  postal_code_city?: string | null;
  transaction_type?: string | null;
  value_date?: string | null;
  amount: number;
  currency?: string | null;
  bic?: string | null;
  country_code?: string | null;
  notes?: string | null;
  category?: string | null;
}

// ---------------- Categories ----------------
export interface Category {
  id: string;
  name: string;
  slug?: string;
  expanded_phrase?: string | null;
  aliases?: string[];
}

export async function listCategories(): Promise<Category[]> {
  const response = await axios.get<Category[]>('/categories/', { baseURL: API_BASE_URL });
  return response.data;
}

export interface CategoryInput {
  name: string;
  expanded_phrase?: string | null;
  aliases?: string[];
}

export async function createCategory(input: CategoryInput): Promise<Category> {
  const response = await axios.post<Category>('/categories/', input, { baseURL: API_BASE_URL });
  return response.data;
}

export async function updateCategoryApi(id: string, input: Partial<CategoryInput>): Promise<Category> {
  const response = await axios.put<Category>(`/categories/${id}`, input, { baseURL: API_BASE_URL });
  return response.data;
}

export async function assignTransactionCategory(transactionId: string, category: string): Promise<void> {
  await axios.post(`/categories/assign/${transactionId}`, { category }, { baseURL: API_BASE_URL });
}

export async function bulkAssignTransactionCategory(transactionIds: string[], category: string): Promise<number> {
  const response = await axios.post<{ updated: number }>(`/categories/assign/bulk`, { transaction_ids: transactionIds, category }, { baseURL: API_BASE_URL });
  return response.data.updated;
}

// --- Optimistic helpers (frontend only) -------------------------------------
/**
 * Mutate a paginated transaction SWR cache optimistically updating category names.
 * keyMatcher: function deciding whether a given SWR key represents transaction page data.
 */
export function optimisticUpdateTransactionCategories(
  mutate: (key?: any, data?: any, opts?: any) => Promise<any>,
  predicate: (tx: Transaction) => boolean,
  updater: (old: Transaction) => Transaction,
) {
  mutate((key: any) => Array.isArray(key) && key[0] === 'transactions', (data: any) => {
    if (!data) return data;
    const copy = { ...data };
    copy.items = data.items.map((tx: Transaction) => predicate(tx) ? updater(tx) : tx);
    return copy;
  }, { revalidate: false });
}

// Use Next.js rewrite proxy to avoid exposing backend URL to the client.
// All client-side requests go to /api/* and are rewritten server-side.
const API_BASE_URL = '/api';

/**
 * Upload a file containing transactions to the backend and return the persisted
 * transactions.
 *
 * @param file - The CSV or Excel file to upload.
 * @returns A promise resolving to an array of `Transaction` objects.
 */
export async function uploadTransactions(file: File): Promise<Transaction[]> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post<Transaction[]>('/transactions/upload', formData, {
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Fetch a paginated list of transactions.
 *
 * @param offset - How many records to offset.
 * @param limit - Maximum number of records to fetch.
 * @returns A promise resolving to an array of `Transaction` objects.
 */
export interface PaginationResponse<T> {
  items: T[];
  offset: number;
  limit: number;
  total?: number;
  has_more: boolean;
  next?: number | null;
  previous?: number | null;
}

export async function listTransactions(
  offset = 0,
  limit = 100,
  sortBy?: string,
  sortDir?: 'asc' | 'desc',
): Promise<PaginationResponse<Transaction>> {
  const response = await axios.get<PaginationResponse<Transaction>>('/transactions/', {
    baseURL: API_BASE_URL,
    params: { offset, limit, sort_by: sortBy, sort_dir: sortDir },
  });
  return response.data;
}

/**
 * Retrieve a single transaction by ID.
 *
 * @param id - Primary key of the transaction.
 * @returns A promise resolving to a single `Transaction` object.
 */
export async function getTransaction(id: string): Promise<Transaction> {
  const response = await axios.get<Transaction>(`/transactions/${id}`, {
    baseURL: API_BASE_URL,
  });
  return response.data;
}

export async function setTransactionNumber(id: string, number: number): Promise<Transaction> {
  const response = await axios.patch<Transaction>(`/transactions/${id}/set-number`, { number }, {
    baseURL: API_BASE_URL,
  });
  return response.data;
}