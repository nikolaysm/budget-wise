import '../styles/globals.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Budget App',
  description: 'Upload your bank statements and categorize transactions',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
