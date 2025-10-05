import CategorySummary from '@/components/CategorySummary';

export const dynamic = 'force-dynamic';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Select a date range to see spending grouped by category.</p>
      </div>
      <CategorySummary />
    </div>
  );
}
