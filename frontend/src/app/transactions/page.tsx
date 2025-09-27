import TransactionsTable from '@/components/transactions-table'
import { QuickCategoryBar } from '@/components/quick-category-bar'

export const metadata = {
  title: 'Transactions | Budget Wise',
}

export default function TransactionsPage() {
  return (
    <main className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Transactions</h1>
      <p className="text-gray-600 text-sm">Browse your imported transactions.</p>
      <QuickCategoryBar size="md" label="New Category" showManageLink={true} className="mb-2" buttonStyle="solid" />
      <TransactionsTable />
    </main>
  )
}
