import TransactionsTable from '@/components/transactions-table'
import { QuickCategoryBar } from '@/components/quick-category-bar'
import { ClientTransactionStatsCards } from '@/components/client-transaction-stats-cards'

export const metadata = {
  title: 'Transactions | Budget Wise',
}

export default function TransactionsPage({ searchParams }: { searchParams?: Record<string, string | string[] | undefined> }) {
  const categoryNameParam = typeof searchParams?.category_name === 'string' ? searchParams?.category_name : undefined
  const hasCategoryParam = typeof searchParams?.has_category === 'string' ? searchParams?.has_category : undefined
  const initialHasCategory = hasCategoryParam === '1' ? true : hasCategoryParam === '0' ? false : undefined
  const dateFrom = typeof searchParams?.date_from === 'string' ? searchParams?.date_from : undefined
  const dateTo = typeof searchParams?.date_to === 'string' ? searchParams?.date_to : undefined
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
