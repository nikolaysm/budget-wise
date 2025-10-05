"use client";
import { useEffect, useState } from 'react';
import { getTransactionStats, TransactionStats } from '@/services/api';
import { StatsCardsUI } from './transaction-stats-cards';

export function ClientTransactionStatsCards({ className = '' }: { className?: string }) {
    const [stats, setStats] = useState<TransactionStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const s = await getTransactionStats();
            setStats(s);
            setLastUpdated(new Date());
        } catch {
            // ignore
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const s = await getTransactionStats();
                if (!cancelled) {
                    setStats(s);
                    setLastUpdated(new Date());
                }
            } catch {/* ignore initial */ }
        })();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className={className + ' flex flex-col gap-2'}>
            <div className="flex items-center gap-3">
                <h2 className="text-sm font-medium text-gray-700">Categorization Stats</h2>
                <button
                    type="button"
                    onClick={fetchStats}
                    disabled={loading}
                    className="text-xs px-2 py-1 rounded border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Refreshing…' : 'Refresh'}
                </button>
                {lastUpdated && !loading && (
                    <span className="text-[10px] text-gray-500">{lastUpdated.toLocaleTimeString()}</span>
                )}
            </div>
            {stats ? (
                <StatsCardsUI stats={stats} />
            ) : (
                <div className="text-xs text-gray-500">Loading stats…</div>
            )}
        </div>
    );
}
