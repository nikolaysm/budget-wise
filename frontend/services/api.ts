import axios from 'axios';

/**
 * Interface mirroring the Transaction model from the backend. Optional fields are
 * marked accordingly. Use this for strong typing when interacting with the API.
 */
export interface Transaction {
  id?: number;
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

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
  const response = await axios.post<Transaction[]>(
    '/transactions/upload',
    formData,
    {
      baseURL: API_BASE_URL,
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  );
  return response.data;
}

/**
 * Fetch a paginated list of transactions.
 *
 * @param skip - How many records to skip.
 * @param limit - Maximum number of records to fetch.
 * @returns A promise resolving to an array of `Transaction` objects.
 */
export async function listTransactions(skip = 0, limit = 100): Promise<Transaction[]> {
  const response = await axios.get<Transaction[]>(
    '/transactions',
    {
      baseURL: API_BASE_URL,
      params: { skip, limit },
    },
  );
  return response.data;
}

/**
 * Retrieve a single transaction by ID.
 *
 * @param id - Primary key of the transaction.
 * @returns A promise resolving to a single `Transaction` object.
 */
export async function getTransaction(id: number): Promise<Transaction> {
  const response = await axios.get<Transaction>(
    `/transactions/${id}`,
    {
      baseURL: API_BASE_URL,
    },
  );
  return response.data;
}