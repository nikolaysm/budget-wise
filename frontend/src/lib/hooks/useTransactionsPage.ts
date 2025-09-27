import useSWR from 'swr';
import { listTransactions, PaginationResponse, Transaction } from '@/services/api';

export interface UseTransactionsOptions {
  offset: number;
  limit: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
  // future: filters, search
}

function keyFactory({ offset, limit, sortBy, sortDir }: UseTransactionsOptions) {
  return ['transactions', offset, limit, sortBy, sortDir];
}

async function fetcher([_k, offset, limit, sortBy, sortDir]: ReturnType<typeof keyFactory>): Promise<PaginationResponse<Transaction>> {
  return listTransactions(offset as number, limit as number, sortBy as string | undefined, sortDir as 'asc' | 'desc' | undefined);
}

export function useTransactionsPage(opts: UseTransactionsOptions) {
  const swr = useSWR(keyFactory(opts), fetcher, {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });
  return swr;
}
