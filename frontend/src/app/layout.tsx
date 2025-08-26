import '../styles/globals.css'
import type { ReactNode } from 'react'
import Header from '@/components/header'
import Footer from '@/components/footer'

export const metadata = {
  title: 'Budget App',
  description: 'Upload your bank statements and categorize transactions',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 flex flex-col">
        <Header />
        <div className="mx-auto max-w-5xl px-4 sm:px-6 py-6 flex-1 w-full">
          {children}
        </div>
        <Footer />
      </body>
    </html>
  )
}
