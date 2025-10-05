import useSWR from 'swr';
import { listTransactions, PaginationResponse, Transaction, TransactionListFilters } from '@/services/api';

export interface UseTransactionsOptions {
  offset: number;
  limit: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
  filters?: TransactionListFilters;
}

function keyFactory({ offset, limit, sortBy, sortDir, filters }: UseTransactionsOptions) {
  return ['transactions', offset, limit, sortBy, sortDir, filters || {}];
}

async function fetcher([_k, offset, limit, sortBy, sortDir, filters]: ReturnType<typeof keyFactory>): Promise<PaginationResponse<Transaction>> {
  return listTransactions(offset as number, limit as number, sortBy as string | undefined, sortDir as 'asc' | 'desc' | undefined, filters as TransactionListFilters);
}

export function useTransactionsPage(opts: UseTransactionsOptions) {
  const swr = useSWR(keyFactory(opts), fetcher, {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });
  return swr;
}
