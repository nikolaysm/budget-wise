"use client"

import * as React from "react"
import { ChevronDownIcon } from "lucide-react"
import { type DateRange } from "react-day-picker"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

export interface DateRangePickerProps {
    value?: DateRange | undefined
    onChange?: (value: DateRange | undefined) => void
    onApply?: (value: DateRange | undefined) => void | Promise<void>
    id?: string
    label?: string
    align?: 'start' | 'center' | 'end'
    className?: string
    numberOfMonths?: number
    applyOnComplete?: boolean // if true, fire onApply automatically when both from & to selected
    captionLayout?: 'label' | 'dropdown'
    density?: 'compact' | 'normal' | 'comfortable'
    calendarProps?: Partial<React.ComponentProps<typeof Calendar>> // escape hatch for additional Calendar props
}

// ---- Date helper utilities (module scope to avoid hook deps noise) -------
const startOfDay = (d: Date) => { const nd = new Date(d); nd.setHours(0, 0, 0, 0); return nd }
const endOfDay = (d: Date) => { const nd = new Date(d); nd.setHours(23, 59, 59, 999); return nd }
const startOfMonth = (d: Date) => startOfDay(new Date(d.getFullYear(), d.getMonth(), 1))
const endOfMonth = (d: Date) => endOfDay(new Date(d.getFullYear(), d.getMonth() + 1, 0))

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
    value,
    onChange,
    id = 'dates',
    label = 'Select your stay',
    align = 'start',
    className,
    numberOfMonths = 2,
    onApply,
    applyOnComplete = true,
    captionLayout = 'dropdown',
    density = 'normal',
    calendarProps
}) => {
    const [internal, setInternal] = React.useState<DateRange | undefined>(value)
    React.useEffect(() => { if (value) setInternal(value) }, [value])

    const range = value ?? internal
    const setRange = (r: DateRange | undefined) => {
        if (!value) setInternal(r)
        onChange?.(r)
    }

    // Track previous applied signature to avoid duplicate onApply calls
    const lastAppliedRef = React.useRef<string | null>(null)
    React.useEffect(() => {
        if (!applyOnComplete || !onApply) return
        if (range?.from && range?.to) {
            const sig = `${range.from.toISOString().slice(0, 10)}_${range.to.toISOString().slice(0, 10)}`
            if (sig !== lastAppliedRef.current) {
                lastAppliedRef.current = sig
                void onApply(range)
            }
        }
    }, [range, applyOnComplete, onApply])

    // --- Shortcut helpers --------------------------------------------------
    const todayRef = React.useRef<Date>(new Date())
    const today = todayRef.current

    const buildLast30Days = (): DateRange => {
        const to = today
        const from = new Date(to)
        from.setDate(from.getDate() - 29) // inclusive 30 days window
        return { from: startOfDay(from), to: endOfDay(to) }
    }

    const applyShortcut = (builder: () => DateRange) => {
        const r = builder()
        setRange(r)
        // Manually trigger apply since user explicitly chose a shortcut
        if (onApply) {
            const sig = `${r.from?.toISOString().slice(0, 10)}_${r.to?.toISOString().slice(0, 10)}`
            lastAppliedRef.current = sig
            void onApply(r)
        }
    }

    // Dynamic last six calendar months (including current)
    const lastSixMonths = React.useMemo(() => {
        const base = todayRef.current; // stable across renders
        const months: { label: string; builder: () => DateRange }[] = []
        for (let i = 0; i < 6; i++) {
            const ref = new Date(base.getFullYear(), base.getMonth() - i, 1)
            const label = ref.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
            months.push({
                label,
                builder: () => ({ from: startOfMonth(ref), to: endOfMonth(ref) })
            })
        }
        return months
    }, [])

    return (
        <div className={cn("grid gap-2", className)}>
            <Label htmlFor={id} className="px-1">
                {label}
            </Label>
            <Popover>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        id={id}
                        className="w-56 justify-between font-normal"
                    >
                        {range?.from && range?.to
                            ? `${range.from.toLocaleDateString()} - ${range.to.toLocaleDateString()}`
                            : "Select date"}
                        <ChevronDownIcon />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto overflow-hidden p-0" align={align}>
                    <div className="flex gap-1 p-2 pb-0 flex-wrap">
                        <button
                            type="button"
                            onClick={() => applyShortcut(buildLast30Days)}
                            className="text-[10px] uppercase tracking-wide px-2 py-1 rounded border bg-background hover:bg-muted transition"
                        >Last 30 days</button>
                        {lastSixMonths.map(m => (
                            <button
                                key={m.label}
                                type="button"
                                onClick={() => applyShortcut(m.builder)}
                                className="text-[10px] uppercase tracking-wide px-2 py-1 rounded border bg-background hover:bg-muted transition"
                                title={`Select full month: ${m.label}`}
                            >{m.label}</button>
                        ))}
                    </div>
                    <Calendar
                        mode="range"
                        // @ts-expect-error force range selection typing due to DayPicker union complexity
                        selected={range}
                        captionLayout={captionLayout}
                        numberOfMonths={numberOfMonths}
                        density={density}
                        {...calendarProps}
                        onSelect={(range) => {
                            setRange(range as DateRange | undefined)
                        }}
                    />
                </PopoverContent>
            </Popover>
        </div>
    )
}

DateRangePicker.displayName = 'DateRangePicker'

export default DateRangePicker