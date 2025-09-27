"use client";
import React from 'react';
import AsyncSelect from 'react-select/async';
import axios from 'axios';

interface Option { label: string; value: string; }

interface AsyncCategorySelectProps {
    value: string | null;
    onChange: (value: string | null) => void;
    placeholder?: string;
    autoFocus?: boolean;
    className?: string;
    menuPortalTarget?: HTMLElement | null;
    minLength?: number; // characters before searching
    debounceMs?: number; // debounce between keystrokes before firing request
}

export const AsyncCategorySelect: React.FC<AsyncCategorySelectProps> = ({
    value,
    onChange,
    placeholder = 'Category',
    autoFocus,
    className,
    menuPortalTarget,
    minLength = 1,
    debounceMs = 250,
}) => {
    const timeoutRef = React.useRef<any>();
    const [initialOptions, setInitialOptions] = React.useState<Option[]>([]);
    const [initialLoaded, setInitialLoaded] = React.useState(false);

    // Fetch an initial batch so menu shows options immediately when opened
    React.useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const resp = await axios.get<{ id: string; name: string }[]>(`/api/categories`, { params: { limit: 50 } });
                if (!cancelled) {
                    setInitialOptions(resp.data.map(c => ({ label: c.name, value: c.name })));
                }
            } catch {
                if (!cancelled) setInitialOptions([]);
            } finally {
                if (!cancelled) setInitialLoaded(true);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const loadOptions = (inputValue: string, callback: (options: Option[]) => void) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        if (!inputValue || inputValue.length < minLength) {
            callback([]);
            return;
        }
        timeoutRef.current = setTimeout(async () => {
            try {
                const resp = await axios.get<{ id: string; name: string }[]>(`/api/categories/search`, { params: { q: inputValue, limit: 20 } });
                callback(resp.data.map(c => ({ label: c.name, value: c.name })));
            } catch {
                callback([]);
            }
        }, debounceMs);
    };

    const selected: Option | null = value ? { label: value, value } : null;

    return (
        <AsyncSelect
            cacheOptions
            // Provide preloaded category list so results show immediately on open
            defaultOptions={initialOptions}
            loadOptions={loadOptions}
            value={selected}
            onChange={(opt: any) => onChange(opt ? opt.value : null)}
            placeholder={placeholder}
            isClearable
            inputId="transaction-category-async"
            classNamePrefix="category-select"
            className={className}
            menuPortalTarget={menuPortalTarget || (typeof window !== 'undefined' ? document.body : null)}
            isLoading={!initialLoaded}
            loadingMessage={() => 'Loading categories...'}
            noOptionsMessage={({ inputValue }) => (
                inputValue && inputValue.length < minLength ? `Type ${minLength} char` : 'No matches'
            )}
            styles={{
                control: (base: any) => ({ ...base, minHeight: 26, height: 26, fontSize: 12 }),
                valueContainer: (base: any) => ({ ...base, padding: '0 4px' }),
                indicatorsContainer: (base: any) => ({ ...base, height: 24 }),
                dropdownIndicator: (base: any) => ({ ...base, padding: 2 }),
                clearIndicator: (base: any) => ({ ...base, padding: 2 }),
                menuPortal: (base: any) => ({ ...base, zIndex: 9999 }),
                menu: (base: any) => ({ ...base, fontSize: 12 }),
                option: (base: any) => ({ ...base, padding: '4px 8px' }),
            }}
            autoFocus={autoFocus}
        />
    );
};

export default AsyncCategorySelect;
