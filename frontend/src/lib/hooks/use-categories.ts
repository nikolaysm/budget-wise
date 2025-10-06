import useSWR from 'swr';

import { Category, CategoryInput, createCategory, listCategories, updateCategoryApi } from '@/services/api';

const key = ['categories'];

async function fetcher() {
    return listCategories();
}

export function useCategories() {
    const swr = useSWR<Category[]>(key, fetcher, { revalidateOnFocus: false });
    return swr;
}

export async function addCategory(input: CategoryInput, mutate: () => void) {
    await createCategory(input);
    mutate();
}

export async function updateCategory(id: string, input: Partial<CategoryInput>, mutate: () => void) {
    await updateCategoryApi(id, input);
    mutate();
}