import Link from 'next/link'
import Image from 'next/image'

export default function Header() {
  return (
    <header className="w-full border-b bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4 sm:px-6 justify-between">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/budget-wise-logo.min.svg"
            alt="Budget Wise logo"
            width={28}
            height={28}
            priority
          />
          <span className="font-semibold">Budget Wise</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm text-gray-600">
          <Link href="/dashboard" className="hover:text-gray-900 transition-colors">Dashboard</Link>
          <Link href="/transactions" className="hover:text-gray-900 transition-colors">Transactions</Link>
        </nav>
      </div>
    </header>
  )
}
