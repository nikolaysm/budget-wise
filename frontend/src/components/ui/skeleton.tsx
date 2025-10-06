import * as React from 'react'

import { cn } from '@/lib/utils'

// Basic shadcn-style Skeleton component
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return <div className={cn('animate-pulse rounded-md bg-gray-200 dark:bg-gray-800', className)} {...props} />
}
