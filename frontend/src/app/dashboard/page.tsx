import CategorySummary from '@/components/category-summary';

export const dynamic = 'force-dynamic';

// Next.js 15 PageProps expects `searchParams?: Promise<any>` in some dynamic contexts.
// We model it accordingly and await if present.
export default async function DashboardPage({
    searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
    const sp = searchParams ? await searchParams : {};
    const initialFrom = typeof sp.date_from === 'string' ? sp.date_from : undefined;
    const initialTo = typeof sp.date_to === 'string' ? sp.date_to : undefined;
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
                <p className="text-sm text-muted-foreground mt-1">Select a date range to see spending grouped by category.</p>
            </div>
            <CategorySummary initialFrom={initialFrom} initialTo={initialTo} />
        </div>
    );
}
