"use client";

import React, { useState } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import Link from 'next/link';

import { addCategory, updateCategory, useCategories } from '@/lib/hooks/use-categories';
import { ClientTransactionStatsCards } from '@/components/client-transaction-stats-cards';

export default function CategoriesPage() {
    const { data: categories, isLoading, mutate } = useCategories();
    const [renameId, setRenameId] = useState<string | null>(null);
    // react-hook-form types
    interface CategoryFormValues {
        name: string;
        expanded_phrase?: string | null;
        aliases?: string; // comma separated input field, transformed before submit
    }

    const createForm = useForm<CategoryFormValues>({
        defaultValues: { name: '', expanded_phrase: '', aliases: '' },
        mode: 'onBlur'
    });

    const editForm = useForm<CategoryFormValues>({
        defaultValues: { name: '', expanded_phrase: '', aliases: '' },
        mode: 'onBlur'
    });
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false); // busy state now only for rename

    const beginRename = (id: string, current: string, expanded?: string | null, aliases?: string[]) => {
        setRenameId(id);
        editForm.reset({
            name: current,
            expanded_phrase: expanded || '',
            aliases: (aliases || []).join(', '),
        });
    };

    const commitRename: SubmitHandler<CategoryFormValues> = async (data) => {
        if (!renameId) return;
        setBusy(true);
        try {
            const aliasesArr = (data.aliases || '')
                .split(',')
                .map(a => a.trim())
                .filter(Boolean);
            await updateCategory(renameId, {
                name: data.name.trim(),
                expanded_phrase: (data.expanded_phrase || '').trim() || null,
                aliases: aliasesArr,
            }, mutate);
            setRenameId(null);
            editForm.reset();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Update failed';
            setError(message);
        } finally {
            setBusy(false);
        }
    };

    const createNew: SubmitHandler<CategoryFormValues> = async (data) => {
        setBusy(true);
        try {
            const aliasesArr = (data.aliases || '')
                .split(',')
                .map(a => a.trim())
                .filter(Boolean);
            await addCategory({
                name: data.name.trim(),
                expanded_phrase: (data.expanded_phrase || '').trim() || null,
                aliases: aliasesArr,
            }, mutate);
            createForm.reset();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Create failed';
            setError(message);
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
            <ClientTransactionStatsCards className="mb-4" />
            <form onSubmit={createForm.handleSubmit(createNew)} className="space-y-2 border rounded p-3 bg-background">
                <h2 className="text-sm font-medium">Create New Category</h2>
                <div className="grid md:grid-cols-3 gap-2">
                    <div className="flex flex-col">
                        <input
                            className="border rounded px-2 py-1 text-sm"
                            placeholder="Name *"
                            {...createForm.register('name', { required: 'Name is required', maxLength: { value: 128, message: 'Max 128 chars' } })}
                        />
                        {createForm.formState.errors.name && <span className="text-[10px] text-red-600">{createForm.formState.errors.name.message}</span>}
                    </div>
                    <div className="flex flex-col">
                        <input
                            className="border rounded px-2 py-1 text-sm"
                            placeholder="Expanded phrase"
                            {...createForm.register('expanded_phrase', { maxLength: { value: 512, message: 'Too long' } })}
                        />
                        {createForm.formState.errors.expanded_phrase && <span className="text-[10px] text-red-600">{createForm.formState.errors.expanded_phrase.message}</span>}
                    </div>
                    <div className="flex flex-col">
                        <input
                            className="border rounded px-2 py-1 text-sm"
                            placeholder="Aliases (comma separated)"
                            {...createForm.register('aliases')}
                        />
                    </div>
                </div>
                <div className="flex gap-2">
                    <button disabled={busy || !createForm.formState.isValid} className="bg-secondary text-secondary-foreground px-3 py-1 rounded text-sm">Add</button>
                    <button type="button" onClick={() => { createForm.reset(); }} className="text-xs underline">Reset</button>
                </div>
            </form>
            {renameId && (
                <form onSubmit={editForm.handleSubmit(commitRename)} className="space-y-2 border rounded p-3 bg-background">
                    <h2 className="text-sm font-medium">Edit Category</h2>
                    <div className="grid md:grid-cols-3 gap-2">
                        <div className="flex flex-col">
                            <label className="text-xs text-muted-foreground">Name</label>
                            <input
                                className="border rounded px-2 py-1 text-sm"
                                {...editForm.register('name', { required: 'Name is required', maxLength: { value: 128, message: 'Max 128 chars' } })}
                            />
                            {editForm.formState.errors.name && <span className="text-[10px] text-red-600">{editForm.formState.errors.name.message}</span>}
                        </div>
                        <div className="flex flex-col">
                            <label className="text-xs text-muted-foreground">Expanded phrase</label>
                            <input
                                className="border rounded px-2 py-1 text-sm"
                                placeholder="Optional"
                                {...editForm.register('expanded_phrase', { maxLength: { value: 512, message: 'Too long' } })}
                            />
                            {editForm.formState.errors.expanded_phrase && <span className="text-[10px] text-red-600">{editForm.formState.errors.expanded_phrase.message}</span>}
                        </div>
                        <div className="flex flex-col">
                            <label className="text-xs text-muted-foreground">Aliases</label>
                            <input
                                className="border rounded px-2 py-1 text-sm"
                                placeholder="food, groceries, ..."
                                {...editForm.register('aliases')}
                            />
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button disabled={busy || !editForm.formState.isValid} className="bg-secondary text-secondary-foreground px-3 py-1 rounded text-sm">Save</button>
                        <button type="button" onClick={() => { setRenameId(null); editForm.reset(); }} className="text-sm underline">Cancel</button>
                    </div>
                </form>
            )}
            {error && <div className="text-sm text-red-600">{error}</div>}
            <div className="border rounded bg-background">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="bg-muted text-left">
                            <th className="p-2 font-medium">Name</th>
                            <th className="p-2 font-medium">Expanded</th>
                            <th className="p-2 font-medium">Aliases</th>
                            <th className="p-2 font-medium w-40">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            <tr><td className="p-2" colSpan={2}>Loading...</td></tr>
                        )}
                        {(categories || []).map(cat => (
                            <tr key={cat.id} className="border-t align-top">
                                <td className="p-2 font-medium">{cat.name}</td>
                                <td className="p-2 text-xs whitespace-pre-wrap max-w-xs">{cat.expanded_phrase || <span className="text-muted-foreground">—</span>}</td>
                                <td className="p-2 text-xs max-w-xs">
                                    {(cat.aliases && cat.aliases.length > 0) ? (
                                        <div className="flex flex-wrap gap-1">
                                            {cat.aliases.map(a => <span key={a} className="px-1 py-0.5 bg-muted rounded text-[10px]">{a}</span>)}
                                        </div>
                                    ) : <span className="text-muted-foreground">—</span>}
                                </td>
                                <td className="p-2 flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => beginRename(cat.id, cat.name, cat.expanded_phrase, cat.aliases)}
                                        className="text-xs underline"
                                    >Edit</button>
                                </td>
                            </tr>
                        ))}
                        {!isLoading && categories?.length === 0 && (
                            <tr><td className="p-2 text-muted-foreground" colSpan={4}>No categories yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
