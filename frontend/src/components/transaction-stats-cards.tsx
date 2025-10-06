interface StatsData { total: number; with_category: number; without_category: number }

function StatsCardsUI({ stats, className = '' }: { stats: StatsData; className?: string }) {
    return (
        <div className={"grid grid-cols-1 sm:grid-cols-3 gap-4 " + className}>
            <div className="rounded-md bg-white shadow p-4 border">
                <p className="text-xs uppercase tracking-wide text-gray-500">Total</p>
                <p className="text-xl font-semibold">{stats.total}</p>
            </div>
            <div className="rounded-md bg-white shadow p-4 border">
                <p className="text-xs uppercase tracking-wide text-gray-500">With Category</p>
                <p className="text-xl font-semibold text-green-600">{stats.with_category}</p>
            </div>
            <div className="rounded-md bg-white shadow p-4 border">
                <p className="text-xs uppercase tracking-wide text-gray-500">Without Category</p>
                <p className="text-xl font-semibold text-red-600">{stats.without_category}</p>
            </div>
        </div>
    )
}

/**
 * Server component (no "use client"): fetches stats with native fetch for reliability.
 */
export async function TransactionStatsCards({ className = '', revalidateSeconds = 60 }: { className?: string; revalidateSeconds?: number }) {
    const backendUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    let stats: StatsData | null = null
    try {
        const res = await fetch(`${backendUrl}/transactions/stats`, {
            // Provide a small revalidation window (optional; Next 13+ caching semantics)
            next: { revalidate: revalidateSeconds },
            headers: { 'Accept': 'application/json' },
        })
        if (res.ok) {
            stats = (await res.json()) as StatsData
        }
    } catch {
        // swallow; return null
    }
    if (!stats) return null
    return <StatsCardsUI stats={stats} className={className} />
}

// Re-export UI for client wrapper reuse if needed
export { StatsCardsUI }
