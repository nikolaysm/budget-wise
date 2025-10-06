import FileUpload from '@/components/file-upload'

export default function Home() {
    return (
        <main className="p-8 flex flex-col items-center justify-start min-h-screen gap-6 bg-gray-50 w-full">
            <div className="w-full max-w-3xl">
                <h1 className="text-3xl font-bold">Budget Control</h1>
                <p className="text-gray-600 mt-2">Upload your CSV or Excel files to parse and store your transactions.</p>
            </div>
            <div className="w-full max-w-3xl">
                <FileUpload />
            </div>
        </main>
    )
}
