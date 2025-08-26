export default function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="w-full border-t bg-white">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-4 text-sm text-gray-500 flex items-center justify-between">
        <span>© {year} Budget Wise</span>
        <a
          href="https://github.com/nikolaysm/budget-wise"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-gray-700"
        >
          GitHub
        </a>
      </div>
    </footer>
  )
}
