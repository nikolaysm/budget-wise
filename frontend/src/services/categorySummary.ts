import axios from 'axios';

export interface CategorySummaryItem {
  category: string | null;
  count: number;
  total_amount: number; // parsed to number in client even if backend returns string
}

export interface CategorySummaryEnvelope {
  items: CategorySummaryItem[];
  date_from?: string | null;
  date_to?: string | null;
  total_amount: number;
  total_count: number;
}

export async function getCategorySummary(
  params: { date_from?: string; date_to?: string } = {}
): Promise<CategorySummaryEnvelope> {
  const response = await axios.get(`/transactions/category-summary`, {
    baseURL: '/api',
    params,
  });
  const raw = response.data;
  // Normalize potential decimal-as-string fields
  const toNum = (v: any) => (typeof v === 'string' ? parseFloat(v) : v ?? 0);
  const items: CategorySummaryItem[] = (raw.items || []).map((r: any) => ({
    category: r.category ?? null,
    count: Number(r.count ?? 0),
    total_amount: toNum(r.total_amount),
  }));
  return {
    items,
    date_from: raw.date_from ?? null,
    date_to: raw.date_to ?? null,
    total_amount: toNum(raw.total_amount),
    total_count: Number(raw.total_count ?? items.reduce((a, r) => a + r.count, 0)),
  };
}
