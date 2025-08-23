import FileUpload from '@/components/FileUpload'

export default function Home() {
  return (
    <main className="p-8 flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold">Budget Control</h1>
      <p className="text-gray-600 mt-2">Upload your CSV or Excel files to parse and store your transactions.</p>
      <FileUpload />
    </main>
  )
}
