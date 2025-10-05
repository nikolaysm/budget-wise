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