import { Metadata } from 'next'
import { getTransaction } from '@/services/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface PageProps {
    params: Promise<{ id: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    const { id } = await params;
    try {
        const tx = await getTransaction(id)
        return { title: `Transaction ${tx.transaction_number ?? ''} | Budget Wise` }
    } catch {
        return { title: 'Transaction | Budget Wise' }
    }
}

function formatDate(d?: string | null) {
    if (!d) return '—'
    try { return new Date(d).toLocaleDateString() } catch { return d }
}

function formatAmount(amount: number, currency?: string | null) {
    try {
        return new Intl.NumberFormat(undefined, { style: 'currency', currency: currency || 'EUR' }).format(amount)
    } catch {
        return amount.toFixed(2)
    }
}

export default async function TransactionDetailPage({ params }: PageProps) {
    const { id } = await params;
    let tx;
    let notFoundError = false;
    try {
        tx = await getTransaction(id);
    } catch (e: any) {
        notFoundError = true;
    }

    if (notFoundError || !tx) {
        return (
            <main className="flex flex-col gap-6">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-semibold">Transaction Details</h1>
                    <div className="ml-auto flex gap-2">
                        <Button asChild variant="outline">
                            <Link href="/transactions">Back</Link>
                        </Button>
                    </div>
                </div>
                <Card>
                    <CardHeader>
                        <CardTitle>Transaction Not Found</CardTitle>
                        <CardDescription>The transaction with id {id} could not be located. It may have been deleted or the database was reset.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-muted-foreground">Verify the ID or return to the list.</p>
                    </CardContent>
                    <CardFooter>
                        <Button asChild variant="default">
                            <Link href="/transactions">Return to Transactions</Link>
                        </Button>
                    </CardFooter>
                </Card>
            </main>
        )
    }

    const rows: Array<[string, string | number | null]> = [
        ['ID', tx.id],
        ['Account', tx.account],
        ['Booking Date', formatDate(tx.booking_date)],
        ['Value Date', formatDate(tx.value_date)],
        ['Amount', formatAmount(tx.amount, tx.currency)],
        ['Currency', tx.currency ?? '—'],
        ['Statement #', tx.statement_number ?? '—'],
        ['Transaction #', tx.transaction_number ?? '—'],
        ['Counterparty Name', tx.counterparty_name ?? '—'],
        ['Counterparty Account', tx.counterparty_account ?? '—'],
        ['Address', tx.street_number ?? '—'],
        ['Postal / City', tx.postal_code_city ?? '—'],
        ['Type / Description', tx.transaction_type ?? '—'],
        ['Notes', tx.notes ?? '—'],
        ['Category', tx.category ?? '—'],
    ]

    return (
        <main className="flex flex-col gap-6">
            <div className="flex items-center gap-4">
                <h1 className="text-2xl font-semibold">Transaction Details</h1>
                <div className="ml-auto flex gap-2">
                    <Button asChild variant="outline">
                        <Link href="/transactions">Back</Link>
                    </Button>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>
                        {tx.transaction_type || tx.counterparty_name || 'Transaction'}
                    </CardTitle>
                    <CardDescription>
                        {formatDate(tx.booking_date)} · {formatAmount(tx.amount, tx.currency)}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-y-2 sm:grid-cols-2 sm:gap-x-8">
                        {rows.map(([label, value]) => (
                            <div key={label} className="flex flex-col py-1 min-w-0">
                                <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
                                <span className="text-sm break-words">{value}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
                <CardFooter>
                    <div className="text-xs text-muted-foreground">ID: {tx.id}</div>
                </CardFooter>
            </Card>

            {/* Placeholder for future actions (assign category inline, etc.) */}
        </main>
    )
}
