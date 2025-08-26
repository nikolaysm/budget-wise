import Link from 'next/link'
import Image from 'next/image'

export default function Header() {
  return (
    <header className="w-full border-b bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-3 px-4 sm:px-6">
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
      </div>
    </header>
  )
}
