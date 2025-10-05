"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { RotateCw } from 'lucide-react';
import type { DateRange } from 'react-day-picker';

import { Button } from '@/components/ui/button';

import { getCategorySummary, CategorySummaryItem, CategorySummaryEnvelope } from '../services/categorySummary';

import { DateRangePicker } from './DateRangePicker';

interface Props {
    initialFrom?: string;
    initialTo?: string;
}

function formatCurrency(n: number) {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(n);
}

export const CategorySummary: React.FC<Props> = ({ initialFrom, initialTo }) => {
    const [range, setRange] = useState<DateRange | undefined>(() => {
        const from = initialFrom ? new Date(initialFrom) : undefined;
        const to = initialTo ? new Date(initialTo) : undefined;
        if (from || to) return { from, to } as DateRange;
        return undefined;
    });
    const [envelope, setEnvelope] = useState<CategorySummaryEnvelope | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    // Avoid hydration mismatches from Radix generated IDs by only rendering interactive
    // controls after the component has mounted on the client.
    const [mounted, setMounted] = useState(false);

    async function load() {
        setLoading(true);
        setError(null);
        try {
            const params: any = {};
            if (range?.from) params.date_from = range.from.toISOString().slice(0, 10);
            if (range?.to) params.date_to = range.to.toISOString().slice(0, 10);
            const res = await getCategorySummary(params);
            setEnvelope(res);
        } catch (e: any) {
            setError(e?.message || 'Failed to load');
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        setMounted(true);
        // Load data once mounted (ensures consistent server/client markup before hydration)
         
        load();
    }, []);

    const items: CategorySummaryItem[] = envelope?.items || [];
    const total = envelope ? envelope.total_amount : items.reduce((acc, r) => acc + r.total_amount, 0);
    const overallCount = envelope ? envelope.total_count : items.reduce((a, r) => a + r.count, 0);

    // Server-side (pre-hydration) render: provide a lightweight deterministic placeholder.
    if (!mounted) {
        return (
            <div className="space-y-4">
                <div className="flex flex-wrap items-end gap-4">
                    <div className="flex flex-col gap-1 w-[280px]">
                        <span className="text-sm font-medium">Date Range</span>
                        <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
                    </div>
                    <div className="h-9 w-24 animate-pulse rounded-md bg-muted" />
                </div>
                <div className="text-sm text-muted-foreground">Loading summary...</div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap items-end gap-4">
                <DateRangePicker
                    value={range}
                    onChange={setRange}
                    onApply={load}
                />
                <Button
                    type="button"
                    onClick={load}
                    variant="secondary"
                    className="self-end cursor-pointer"
                    aria-label="Refresh summary"
                >
                    <RotateCw className="h-4 w-4 mr-1" /> Refresh
                </Button>
            </div>
            {loading && <div>Loading...</div>}
            {error && <div className="text-red-600">{error}</div>}
            {!loading && !error && items.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {items.map((row) => {
                        const pct = total !== 0 ? (row.total_amount / total) * 100 : 0;
                        // Build link to transactions with pre-selected category (by name) or uncategorized filter
                        const isUncat = !row.category;
                        const qs = new URLSearchParams();
                        if (isUncat) {
                            qs.set('has_category', '0');
                        } else if (row.category) {
                            qs.set('category_name', row.category);
                        }
                        if (range?.from) qs.set('date_from', range.from.toISOString().slice(0, 10));
                        if (range?.to) qs.set('date_to', range.to.toISOString().slice(0, 10));
                        const href = `/transactions?${qs.toString()}`;
                        return (
                            <Link
                                key={row.category || '(uncategorized)'}
                                href={href}
                                className="rounded-lg border p-4 flex flex-col gap-2 bg-background transition hover:bg-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                title={isUncat ? 'View uncategorized transactions' : `View transactions in ${row.category}`}
                                prefetch={false}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <h3 className="text-sm font-medium leading-tight">
                                        {row.category || <span className="italic text-muted-foreground">(Uncategorized)</span>}
                                    </h3>
                                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted">{pct.toFixed(1)}%</span>
                                </div>
                                <div className="text-lg font-semibold tabular-nums">{formatCurrency(row.total_amount)}</div>
                                <div className="text-xs text-muted-foreground">{row.count} {row.count === 1 ? 'tx' : 'txs'}</div>
                                <div className="h-2 w-full rounded bg-muted overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all"
                                        style={{ width: `${pct}%` }}
                                        aria-hidden="true"
                                    />
                                </div>
                            </Link>
                        );
                    })}
                    <div className="rounded-lg border p-4 flex flex-col gap-2 bg-accent/30">
                        <h3 className="text-sm font-medium">Total</h3>
                        <div className="text-lg font-semibold tabular-nums">{formatCurrency(total || 0)}</div>
                        <div className="text-xs text-muted-foreground">{overallCount} total transactions</div>
                        <div className="h-2 w-full rounded bg-muted overflow-hidden">
                            <div className="h-full bg-primary" style={{ width: '100%' }} aria-hidden="true" />
                        </div>
                    </div>
                </div>
            )}
            {!loading && !error && items.length === 0 && (
                <div className="text-sm text-muted-foreground border rounded-md p-6">
                    No transactions found for the selected range.
                </div>
            )}
        </div>
    );
};

export default CategorySummary;
