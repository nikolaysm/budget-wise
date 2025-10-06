import TransactionsTable from '@/components/transactions-table'
import { QuickCategoryBar } from '@/components/quick-category-bar'
import { ClientTransactionStatsCards } from '@/components/client-transaction-stats-cards'

export const metadata = {
  title: 'Transactions | Budget Wise',
}

export default async function TransactionsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams
  const categoryNameParam = typeof sp?.category_name === 'string' ? sp.category_name : undefined
  const hasCategoryParam = typeof sp?.has_category === 'string' ? sp.has_category : undefined
  const initialHasCategory = hasCategoryParam === '1' ? true : hasCategoryParam === '0' ? false : undefined
  const dateFrom = typeof sp?.date_from === 'string' ? sp.date_from : undefined
  const dateTo = typeof sp?.date_to === 'string' ? sp.date_to : undefined
  return (
    <main className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Transactions</h1>
      <ClientTransactionStatsCards className="mb-4" />
      <QuickCategoryBar size="md" label="New Category" showManageLink={true} className="mb-2" buttonStyle="solid" />
      <TransactionsTable
        initialCategoryName={categoryNameParam}
        initialHasCategory={initialHasCategory}
        initialDateFrom={dateFrom}
        initialDateTo={dateTo}
      />
    </main>
  )
}
