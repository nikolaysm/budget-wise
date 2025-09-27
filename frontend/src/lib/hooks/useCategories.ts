import useSWR from 'swr';
import { listCategories, createCategory, renameCategory, Category } from '@/services/api';

const key = ['categories'];

async function fetcher() {
  return listCategories();
}

export function useCategories() {
  const swr = useSWR<Category[]>(key, fetcher, { revalidateOnFocus: false });
  return swr;
}

export async function addCategory(name: string, mutate: () => void) {
  await createCategory(name);
  mutate();
}

export async function updateCategory(id: string, name: string, mutate: () => void) {
  await renameCategory(id, name);
  mutate();
}