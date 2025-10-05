"use client";

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Check, X, ArrowUp, ArrowDown, ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight } from 'lucide-react';
import { mutate as globalMutate } from 'swr';
import {
	ColumnDef,
	flexRender,
	getCoreRowModel,
	getSortedRowModel,
	SortingState,
	useReactTable,
	RowSelectionState,
} from '@tanstack/react-table';
import clsx from 'clsx';

import { assignTransactionCategory, optimisticUpdateTransactionCategories, bulkAssignTransactionCategory, Transaction } from '@/services/api';
import { useCategories } from '@/lib/hooks/useCategories';
import { useTransactionsPage } from '@/lib/hooks/useTransactionsPage';
import { Skeleton } from '@/components/ui/skeleton';

import TransactionNumberCell from './TransactionNumberCell';
import AsyncCategorySelect from './AsyncCategorySelect';


// --- Type augmentation for custom column meta fields -----------------------
declare module '@tanstack/react-table' {
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	interface ColumnMeta<TData extends unknown, TValue> {
		width?: string;
		sticky?: boolean;
		left?: string;
		numeric?: boolean;
	}
}

// Helper to get meta with inferred type (avoids many optional chains)
function meta<T extends object>(col: any): import('@tanstack/react-table').ColumnMeta<T, unknown> | undefined {
	return col.columnDef?.meta as any;
}

interface TransactionsTableProps { initialLimit?: number; initialCategoryName?: string; initialHasCategory?: boolean; initialDateFrom?: string; initialDateTo?: string }

type Row = Transaction;

export const TransactionsTable: React.FC<TransactionsTableProps> = ({ initialLimit = 25, initialCategoryName, initialHasCategory, initialDateFrom, initialDateTo }) => {
	// server paging & sorting
	const [offset, setOffset] = useState(0);
	const [limit, setLimit] = useState(initialLimit);
	const [sortBy, setSortBy] = useState<string | undefined>('transaction_number');
	const [sortDir, setSortDir] = useState<'asc' | 'desc' | undefined>('desc');
	// Filters state
	const [counterpartySearch, setCounterpartySearch] = useState('');
	const [typeSearch, setTypeSearch] = useState('');
	const [notesSearch, setNotesSearch] = useState('');
	const [categoryIdFilter, setCategoryIdFilter] = useState<string | undefined>(undefined);
	const [hasCategory, setHasCategory] = useState<boolean | undefined>(initialHasCategory);

	const [dateFrom, setDateFrom] = useState<string | undefined>(initialDateFrom);
	const [dateTo, setDateTo] = useState<string | undefined>(initialDateTo);

	const filters = useMemo(() => ({
		counterparty_name_ilike: counterpartySearch || undefined,
		transaction_type_ilike: typeSearch || undefined,
		notes_ilike: notesSearch || undefined,
		category_id: categoryIdFilter || undefined,
		has_category: hasCategory,
		booking_date_gte: dateFrom || undefined,
		booking_date_lte: dateTo || undefined,
	}), [counterpartySearch, typeSearch, notesSearch, categoryIdFilter, hasCategory, dateFrom, dateTo]);

	const { data, isLoading, mutate: mutatePages } = useTransactionsPage({ offset, limit, sortBy, sortDir, filters });
	const rows = data?.items ?? [];
	const total = data?.total;
	const hasMore = data?.has_more ?? false;
	const { data: categories } = useCategories();

	// Apply initial category name -> id mapping once categories load
	useEffect(() => {
		if (!categories) return;
		if (initialCategoryName && !categoryIdFilter) {
			const match = categories.find(c => c.name.toLowerCase() === initialCategoryName.toLowerCase());
			if (match) {
				setCategoryIdFilter(match.id);
				setOffset(0);
			}
		}
	}, [categories, initialCategoryName, categoryIdFilter]);

	// Inline category editing
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editingValue, setEditingValue] = useState('');
	const beginEdit = (row: Row) => { setEditingId(row.id); setEditingValue(row.category || ''); };
	const cancelEdit = () => { setEditingId(null); setEditingValue(''); };
	const commitEdit = async (row: Row) => {
		const value = editingValue.trim();
		setEditingId(null);
		if (!value) return;
		optimisticUpdateTransactionCategories(globalMutate as any, (tx) => tx.id === row.id, (tx) => ({ ...tx, category: value }));
		try { await assignTransactionCategory(row.id, value); mutatePages(); } catch (e) { console.error(e); }
	};

	// Bulk selection operations
	const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
	const selectedRows = useMemo(() => Object.keys(rowSelection).map(id => rows.find(r => r.id === id)).filter(Boolean) as Row[], [rowSelection, rows]);
	const [bulkCategory, setBulkCategory] = useState('');
	const [bulkBusy, setBulkBusy] = useState(false);
	const [bulkError, setBulkError] = useState<string | null>(null);
	const handleBulkAssign = async () => {
		const name = bulkCategory.trim();
		if (!name || selectedRows.length === 0) return;
		setBulkBusy(true); setBulkError(null);
		optimisticUpdateTransactionCategories(globalMutate as any, (tx) => selectedRows.some(r => r.id === tx.id), (tx) => ({ ...tx, category: name }));
		try { await bulkAssignTransactionCategory(selectedRows.map(r => r.id), name); setBulkCategory(''); setRowSelection({}); mutatePages(); }
		catch (e: any) { setBulkError(e?.message || 'Bulk assign failed'); }
		finally { setBulkBusy(false); }
	};

	const categorySuggestions = useMemo(() => (categories || []).map(c => c.name), [categories]);

	// React Table column definitions (excluding selection column added separately)
	const columns = useMemo<ColumnDef<Row>[]>(() => [
		{
			id: 'account',
			accessorKey: 'account',
			header: () => 'Account',
			enableSorting: true,
			cell: info => {
				const r = info.row.original;
				const val = info.getValue<string>();
				return (
					<Link
						href={`/transactions/${r.id}`}
						className="whitespace-nowrap text-primary underline hover:underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 rounded-sm"
						title="View transaction details"
					>
						{val}
					</Link>
				);
			},
			meta: { width: '15rem', sticky: true, left: 'var(--tx-sticky-offset-account, 2.25rem)' },
		},
		{
			id: 'booking_date',
			accessorKey: 'booking_date',
			header: () => 'Booking Date',
			cell: info => <span className="block text-center w-full">{info.getValue<string>() || '-'}</span>,
			enableSorting: true,
			meta: { width: '8rem' },
		},
		{
			id: 'transaction_number',
			accessorKey: 'transaction_number',
			header: () => 'Transaction Number',
			enableSorting: true,
			cell: ({ row }) => (
				<div className="flex items-center justify-center w-full min-w-[6rem]">
					<TransactionNumberCell id={row.original.id} transactionNumber={row.original.transaction_number} mutatePages={mutatePages} />
				</div>
			),
			meta: { width: '11rem' },
		},
		{
			id: 'amount',
			accessorKey: 'amount',
			header: () => 'Amount',
			enableSorting: true,
			cell: info => {
				const v = info.getValue<number>();
				const formatted = v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
				return <span className={clsx('tabular-nums flex justify-end w-full', v < 0 ? 'text-red-600' : v > 0 ? 'text-green-600' : '')}>{formatted}</span>;
			},
			meta: { width: '7rem', numeric: true },
		},
		{
			id: 'category',
			accessorKey: 'category',
			header: () => 'Category',
			enableSorting: false,
			cell: ({ row }) => {
				const r = row.original;
				const isEditing = editingId === r.id;
				return (
					<div className="flex items-center justify-center min-w-[8rem]">
						{isEditing ? (
							<form onSubmit={(e) => { e.preventDefault(); commitEdit(r); }} className="flex items-center gap-1 w-40">
								<div className="w-full">
									<AsyncCategorySelect
										value={editingValue || null}
										onChange={(val) => setEditingValue(val || '')}
										placeholder="Search..."
										autoFocus
										className="text-xs"
									/>
								</div>
								<button
									type="submit"
									className="inline-flex items-center justify-center text-xs text-green-600 hover:text-green-700 focus:outline-none disabled:opacity-40"
									aria-label="Save category"
									disabled={!editingValue}
								>
									<Check className="h-4 w-4" />
								</button>
								<button
									type="button"
									onClick={cancelEdit}
									className="inline-flex items-center justify-center text-xs text-gray-500 hover:text-gray-700 focus:outline-none"
									aria-label="Cancel edit"
								>
									<X className="h-4 w-4" />
								</button>
							</form>
						) : (
							<button onClick={() => beginEdit(r)} className="text-xs underline min-w-[4rem]">
								{r.category || '—'}
							</button>
						)}
					</div>
				);
			},
			meta: { width: '9rem' },
		},
		{
			id: 'counterparty',
			header: () => 'Counterparty',
			accessorFn: r => r.counterparty_name || r.counterparty_account || '-',
			cell: info => <span className="break-words">{info.getValue<string>()}</span>,
			meta: { width: '12rem' },
		},
		{
			id: 'transaction_type',
			accessorKey: 'transaction_type',
			header: () => 'Type',
			cell: info => <span className="break-words">{info.getValue<string>() || '-'}</span>,
			meta: { width: '14rem' },
		},
		{
			id: 'notes',
			accessorKey: 'notes',
			header: () => 'Notes',
			cell: info => <span className="break-words">{info.getValue<string>() || '-'}</span>,
			meta: { width: '16rem' },
		},
		{
			id: 'currency',
			accessorKey: 'currency',
			header: () => 'Currency',
			enableSorting: true,
			cell: info => <span>{info.getValue<string>() || '-'}</span>,
			meta: { width: '5rem', numeric: true },
		},
	], [editingId, editingValue]);

	// React Table instance (selection column added dynamically)
	const [sorting, setSorting] = useState<SortingState>([{ id: sortBy || 'transaction_number', desc: sortDir === 'desc' }]);

	useEffect(() => {
		// When user sorts via table, propagate to server fetch state
		if (sorting.length) {
			const s = sorting[0];
			setSortBy(s.id === 'account' || s.id === 'transaction_number' || s.id === 'amount' || s.id === 'booking_date' ? s.id : undefined);
			setSortDir(s.desc ? 'desc' : 'asc');
			setOffset(0);
		}
		 
	}, [sorting]);

	const table = useReactTable({
		data: rows,
		columns,
		state: { sorting, rowSelection },
		onSortingChange: setSorting,
		onRowSelectionChange: setRowSelection,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		manualSorting: true, // server side
		enableSortingRemoval: false,
		getRowId: (row) => row.id,
	});

	// Paging helpers
	const currentPage = Math.floor(offset / limit) + 1;
	const totalRows = typeof total === 'number' ? total : (hasMore ? offset + rows.length + 1 : offset + rows.length);
	const totalPages = totalRows ? Math.max(1, Math.ceil(totalRows / limit)) : currentPage + (hasMore ? 1 : 0);

	const goToPage = (page: number) => { if (page < 1) return; const max = totalPages; if (page > max) return; setOffset((page - 1) * limit); };
	const changePageSize = (size: number) => { setLimit(size); setOffset(0); };

	const initialSkeleton = (
		<div className="space-y-3 p-3" aria-label="Loading transactions" aria-busy="true">
			<div className="flex gap-4 text-sm font-medium">
				<Skeleton className="h-5 w-28" />
				<Skeleton className="h-5 w-24" />
				<Skeleton className="h-5 w-20" />
				<Skeleton className="h-5 w-16" />
				<Skeleton className="h-5 w-40" />
				<Skeleton className="h-5 w-14" />
				<Skeleton className="h-5 w-32" />
			</div>
			<div className="space-y-2">
				{Array.from({ length: Math.min(limit, 12) }).map((_, i) => (
					<div key={i} className="flex gap-4 text-sm">
						<Skeleton className="h-4 w-28" />
						<Skeleton className="h-4 w-24" />
						<Skeleton className="h-4 w-20" />
						<Skeleton className="h-4 w-16" />
						<Skeleton className="h-4 w-40" />
						<Skeleton className="h-4 w-14" />
						<Skeleton className="h-4 w-32" />
					</div>
				))}
			</div>
		</div>
	);

	// Render helpers
	const renderSortIcon = (colId: string) => {
		const s = sorting.find(s => s.id === colId);
		if (!s) return null;
		return s.desc ? <ArrowDown className="h-3 w-3 inline ml-1" /> : <ArrowUp className="h-3 w-3 inline ml-1" />;
	};

	return (
		<div className="rounded-md border bg-background p-2 min-h-[420px] space-y-2" data-tx-table-wrapper>
			{/* Filter bar */}
			<div className="flex flex-col gap-2 p-1 border-b pb-2">
				<div className="flex flex-wrap gap-2 items-end">
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Counterparty</label>
						<input value={counterpartySearch} onChange={e => { setCounterpartySearch(e.target.value); setOffset(0); }} placeholder="Search name..." className="border rounded px-2 py-1 text-xs w-44" />
					</div>
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Type</label>
						<input value={typeSearch} onChange={e => { setTypeSearch(e.target.value); setOffset(0); }} placeholder="Search type..." className="border rounded px-2 py-1 text-xs w-40" />
					</div>
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Notes</label>
						<input value={notesSearch} onChange={e => { setNotesSearch(e.target.value); setOffset(0); }} placeholder="Search notes..." className="border rounded px-2 py-1 text-xs w-48" />
					</div>
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Category</label>
						<select value={categoryIdFilter || ''} onChange={e => { setCategoryIdFilter(e.target.value || undefined); setOffset(0); }} className="border rounded px-1 py-1 text-xs w-40">
							<option value="">All</option>
							{(categories || []).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
						</select>
					</div>
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Date From</label>
						<input type="date" value={dateFrom || ''} onChange={e => { setDateFrom(e.target.value || undefined); setOffset(0); }} className="border rounded px-2 py-1 text-xs w-36" />
					</div>
					<div className="flex flex-col">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Date To</label>
						<input type="date" value={dateTo || ''} onChange={e => { setDateTo(e.target.value || undefined); setOffset(0); }} className="border rounded px-2 py-1 text-xs w-36" />
					</div>
					<div className="flex items-center gap-2 mt-4">
						<label className="text-[10px] uppercase tracking-wide text-muted-foreground">Has Category</label>
						<select value={hasCategory === undefined ? '' : hasCategory ? '1' : '0'} onChange={e => { const val = e.target.value; setHasCategory(val === '' ? undefined : val === '1'); setOffset(0); }} className="border rounded px-1 py-1 text-xs">
							<option value="">Any</option>
							<option value="1">Yes</option>
							<option value="0">No</option>
						</select>
					</div>
					<button type="button" onClick={() => { setCounterpartySearch(''); setTypeSearch(''); setNotesSearch(''); setCategoryIdFilter(undefined); setHasCategory(undefined); setDateFrom(undefined); setDateTo(undefined); setOffset(0); }} className="text-xs underline ml-auto">Reset</button>
				</div>
			</div>
			{selectedRows.length > 0 && (
				<div className="flex flex-wrap items-center gap-2 px-1 text-xs">
					<span className="text-muted-foreground">{selectedRows.length} selected</span>
					<form onSubmit={(e) => { e.preventDefault(); handleBulkAssign(); }} className="flex items-center gap-1 w-64">
						<div className="flex-1 min-w-[8rem]">
							<AsyncCategorySelect
								value={bulkCategory || null}
								onChange={(val) => setBulkCategory(val || '')}
								placeholder="Bulk category..."
							/>
						</div>
						<button disabled={bulkBusy || !bulkCategory} className="underline disabled:opacity-50">Apply</button>
					</form>
					<button type="button" onClick={() => setRowSelection({})} className="underline">Clear</button>
					{bulkError && <span className="text-red-600">{bulkError}</span>}
				</div>
			)}
			<datalist id="category-datalist">
				{categorySuggestions.map(n => <option key={n} value={n} />)}
			</datalist>
			{isLoading && rows.length === 0 ? (
				initialSkeleton
			) : (
				<div className="overflow-auto max-h-[60vh]" data-tx-table-container style={{ ['--tx-selection-col-width' as any]: '2.25rem' }}>
					<table className="w-full text-xs border-collapse" data-tx-table>
						<thead className="bg-background sticky top-0 z-30">
							<tr>
								<th
									className="px-2 py-2 align-middle font-semibold text-left sticky left-0 z-40 bg-background border-b w-[var(--tx-selection-col-width)]"
									style={{ minWidth: 'var(--tx-selection-col-width)' }}
								>
									<input
										type="checkbox"
										aria-label="Select page"
										checked={table.getIsAllPageRowsSelected()}
										onChange={table.getToggleAllPageRowsSelectedHandler()}
										className="rounded border"
									/>
								</th>
								{table.getFlatHeaders().map(header => {
									const m = meta<Row>(header.column);
									return (
										<th
											key={header.id}
											colSpan={header.colSpan}
											className={clsx(
												'px-3 py-2 font-semibold text-center align-middle border-b bg-background',
												header.column.getCanSort() && 'cursor-pointer select-none',
												m?.sticky && 'sticky z-30',
												m?.sticky && 'tx-sticky-account',
												m?.sticky && 'text-left'
											)}
											style={{
												width: m?.width,
												minWidth: m?.width,
												left: m?.left,
											}}
											onClick={header.column.getToggleSortingHandler?.()}
										>
											{flexRender(header.column.columnDef.header, header.getContext())}
											{renderSortIcon(header.column.id)}
										</th>
									);
								})}
							</tr>
						</thead>
						<tbody>
							{table.getRowModel().rows.map(row => (
								<tr key={row.id} data-selected={row.getIsSelected() || undefined} className={clsx('hover:bg-muted/40', row.getIsSelected() && 'bg-muted/60')}>
									<td className="px-2 py-1 sticky left-0 bg-background z-20 border-b w-[var(--tx-selection-col-width)]" style={{ minWidth: 'var(--tx-selection-col-width)' }}>
										<input
											type="checkbox"
											aria-label="Select row"
											checked={row.getIsSelected()}
											onChange={row.getToggleSelectedHandler()}
											className="rounded border"
										/>
									</td>
									{row.getVisibleCells().map(cell => {
										const m = meta<Row>(cell.column);
										return (
											<td
												key={cell.id}
												className={clsx(
													'px-3 py-1 border-b align-middle',
													m?.sticky && 'sticky bg-background z-10',
													cell.column.id === 'account' && 'tx-sticky-account'
												)}
												style={{
													width: m?.width,
													minWidth: m?.width,
													left: m?.left,
													textAlign: m?.numeric ? 'right' as const : undefined,
												}}
											>
												{flexRender(cell.column.columnDef.cell, cell.getContext())}
											</td>
										);
									})}
								</tr>
							))}
							{rows.length === 0 && !isLoading && (
								<tr>
									<td colSpan={columns.length + 1} className="text-center py-6 text-sm text-muted-foreground">No transactions</td>
								</tr>
							)}
							{isLoading && rows.length > 0 && (
								<tr>
									<td colSpan={columns.length + 1} className="text-center py-2 text-muted-foreground text-xs">Loading…</td>
								</tr>
							)}
						</tbody>
					</table>
				</div>
			)}
			{/* Pagination controls */}
			<div className="flex flex-wrap items-center gap-2 justify-between text-xs pt-1">
				<div className="flex items-center gap-2">
					<span className="text-muted-foreground">Rows per page:</span>
					<select value={limit} onChange={e => changePageSize(Number(e.target.value))} className="border rounded px-1 py-0.5 bg-background">
						{[10, 25, 50, 100].map(s => <option key={s} value={s}>{s}</option>)}
					</select>
					<span className="text-muted-foreground">{(offset + 1)}-{Math.min(offset + rows.length, totalRows)} of {totalRows}</span>
				</div>
				<div className="flex items-center gap-1">
					<button onClick={() => goToPage(1)} disabled={currentPage === 1} className="p-1 disabled:opacity-40" aria-label="First page"><ChevronsLeft className="h-4 w-4" /></button>
					<button onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 1} className="p-1 disabled:opacity-40" aria-label="Previous page"><ChevronLeft className="h-4 w-4" /></button>
					<span className="px-2">Page {currentPage} / {totalPages}</span>
					<button onClick={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages} className="p-1 disabled:opacity-40" aria-label="Next page"><ChevronRight className="h-4 w-4" /></button>
					<button onClick={() => goToPage(totalPages)} disabled={currentPage >= totalPages} className="p-1 disabled:opacity-40" aria-label="Last page"><ChevronsRight className="h-4 w-4" /></button>
				</div>
			</div>
		</div>
	);
};

export default TransactionsTable;
