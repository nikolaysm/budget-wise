"use client";

import React, { useState } from 'react';
import { Check, X } from 'lucide-react';
import { mutate as globalMutate } from 'swr';
import { setTransactionNumber, Transaction } from '@/services/api';

interface Props {
  id: string;
  transactionNumber: number | string | null | undefined;
  mutatePages: () => void; // revalidation callback from parent
}

/**
 * Cell UI component for displaying or adding a transaction number.
 * Business rule: only allow adding if the number is currently null/undefined.
 */
const TransactionNumberCell: React.FC<Props> = ({ id, transactionNumber, mutatePages }) => {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const begin = () => {
    if (transactionNumber != null) return; // do not edit existing numbers (out of scope)
    setEditing(true);
    setValue('');
    setError(null);
  };

  const cancel = () => {
    setEditing(false);
    setValue('');
    setError(null);
  };

  const commit = async () => {
    const raw = value.trim();
    if (!raw) return;
    const parsed = Number(raw);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setError('Invalid');
      return;
    }
    setBusy(true);
    setError(null);
    // Optimistic update of SWR transaction pages cache
    (globalMutate as any)((key: any) => Array.isArray(key) && key[0] === 'transactions', (data: any) => {
      if (!data) return data;
      const copy = { ...data };
      copy.items = data.items.map((tx: Transaction) => tx.id === id ? { ...tx, transaction_number: parsed } : tx);
      return copy;
    }, { revalidate: false });
    try {
      await setTransactionNumber(id, parsed);
      mutatePages();
      setEditing(false);
    } catch (e: any) {
      console.error(e);
      setError(e?.message || 'Failed');
    } finally {
      setBusy(false);
    }
  };

  if (transactionNumber != null) {
    return <span className="text-xs">{transactionNumber}</span>;
  }

  if (!editing) {
    return (
      <button onClick={begin} className="text-xs underline" aria-label="Add transaction number">Add</button>
    );
  }

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (!busy) commit(); }}
      className="flex items-center gap-1"
    >
      <input
        type="number"
        min={1}
        inputMode="numeric"
        value={value}
        onChange={(e) => setValue(e.target.value.replace(/[^0-9]/g, ''))}
        className="w-20 px-1 py-0.5 text-xs border rounded"
        autoFocus
        placeholder="#"
        aria-label="Transaction number"
        disabled={busy}
      />
      <button
        type="submit"
        className="inline-flex items-center justify-center text-xs text-green-600 hover:text-green-700 disabled:opacity-40"
        disabled={!value || busy}
        aria-label="Save number"
      >
        <Check className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={cancel}
        className="inline-flex items-center justify-center text-xs text-gray-500 hover:text-gray-700"
        aria-label="Cancel"
        disabled={busy}
      >
        <X className="h-4 w-4" />
      </button>
      {error && <span className="text-[10px] text-red-600">{error}</span>}
    </form>
  );
};

export default TransactionNumberCell;
