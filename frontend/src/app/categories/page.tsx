"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useCategories, updateCategory } from '@/lib/hooks/useCategories';
import { QuickCategoryBar } from '@/components/quick-category-bar';

export default function CategoriesPage() {
    const { data: categories, isLoading, mutate } = useCategories();
    const [renameId, setRenameId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false); // busy state now only for rename

    const beginRename = (id: string, current: string) => {
        setRenameId(id);
        setRenameValue(current);
    };

    const commitRename = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!renameId) return;
        setBusy(true);
        try {
            await updateCategory(renameId, renameValue.trim(), mutate);
            setRenameId(null);
            setRenameValue('');
        } catch (err: any) {
            setError(err?.message || 'Rename failed');
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Categories</h1>
                <Link href="/transactions" className="text-sm underline">← Transactions</Link>
            </div>
            <QuickCategoryBar size="md" label="New Category" showManageLink={false} className="mb-2" buttonStyle="solid" />
            {renameId && (
                <form onSubmit={commitRename} className="flex gap-2 items-end">
                    <div className="flex flex-col">
                        <label htmlFor="rename-category" className="text-sm font-medium">Rename Category</label>
                        <input
                            className="border rounded px-2 py-1 text-sm"
                            value={renameValue}
                            onChange={e => setRenameValue(e.target.value)}
                            id="rename-category"
                            name="rename_category_name"
                        />
                    </div>
                    <button disabled={busy} className="bg-secondary text-secondary-foreground px-3 py-1 rounded text-sm">Save</button>
                    <button type="button" onClick={() => { setRenameId(null); setRenameValue(''); }} className="text-sm underline">Cancel</button>
                </form>
            )}
            {error && <div className="text-sm text-red-600">{error}</div>}
            <div className="border rounded bg-background">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="bg-muted text-left">
                            <th className="p-2 font-medium">Name</th>
                            <th className="p-2 font-medium w-40">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            <tr><td className="p-2" colSpan={2}>Loading...</td></tr>
                        )}
                        {(categories || []).map(cat => (
                            <tr key={cat.id} className="border-t">
                                <td className="p-2">{cat.name}</td>
                                <td className="p-2 flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => beginRename(cat.id, cat.name)}
                                        className="text-xs underline"
                                    >Rename</button>
                                </td>
                            </tr>
                        ))}
                        {!isLoading && categories?.length === 0 && (
                            <tr><td className="p-2 text-muted-foreground" colSpan={2}>No categories yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
