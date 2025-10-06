"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Plus } from 'lucide-react';

import { useCategories, addCategory } from '@/lib/hooks/use-categories';
import { cn } from '@/lib/utils';

export interface QuickCategoryBarProps {
    label?: string;
    inputPlaceholder?: string;
    size?: 'sm' | 'md';
    showManageLink?: boolean;
    className?: string;
    buttonStyle?: 'underline' | 'solid';
    onCreated?: (name: string) => void;
    inputId?: string; // optional explicit id
}

export function QuickCategoryBar({
    label = 'Quick Add Category',
    inputPlaceholder = 'e.g. Groceries',
    size = 'md',
    showManageLink = true,
    className,
    buttonStyle = 'underline',
    onCreated,
    inputId = 'quick-category-name',
}: QuickCategoryBarProps) {
    const { mutate } = useCategories();
    const [name, setName] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = name.trim();
        if (!trimmed) return;
        setBusy(true);
        setError(null);
        try {
            await addCategory({ name: trimmed }, mutate);
            setName('');
            onCreated?.(trimmed);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed to create');
        } finally {
            setBusy(false);
        }
    };

    const textSize = size === 'sm' ? 'text-xs' : 'text-sm';
    const inputPadding = size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm';
    // Match button height to input by reusing padding; keep variant distinctions
    const buttonPadding = inputPadding.replace('text-xs', '').replace('text-sm', '').trim(); // remove text size for reuse
    const buttonClasses = buttonStyle === 'underline'
        ? cn(textSize, 'underline disabled:opacity-50 inline-flex items-center justify-center', buttonPadding)
        : cn(textSize, 'bg-primary text-primary-foreground rounded disabled:opacity-50 inline-flex items-center justify-center', buttonPadding);

    return (
        <div className={cn('flex flex-wrap gap-4 items-end', className)}>
            <form onSubmit={submit} className="flex gap-2 items-end">
                <div className="flex flex-col">
                    <label htmlFor={inputId} className={cn('font-medium', textSize)}>{label}</label>
                    <input
                        className={cn('border rounded', inputPadding)}
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder={inputPlaceholder}
                        id={inputId}
                        name="category_name"
                    />
                </div>
                <button
                    type="submit"
                    disabled={busy}
                    className={cn(buttonClasses, 'gap-1')}
                    aria-label="Add category"
                >
                    <Plus className={cn(size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
                    {buttonStyle === 'solid' && <span>Add</span>}
                </button>
            </form>
            {showManageLink && (
                <Link href="/categories" className={cn(textSize, 'underline')}>Manage Categories</Link>
            )}
            {error && <div className={cn('basis-full text-red-600', textSize)}>{error}</div>}
        </div>
    );
}
