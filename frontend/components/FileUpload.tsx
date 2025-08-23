import React, { useCallback, useRef, useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Upload, Loader2 } from 'lucide-react';

/**
 * FileUpload component allows users to select and submit CSV or Excel files
 * to the FastAPI backend. Once uploaded, the response is printed to the console.
 */
const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }, []);

  const onDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setSuccess(null);
    setProgress(0);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('/api/transactions/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          if (!evt.total) return;
          const p = Math.round((evt.loaded * 100) / evt.total);
          setProgress(p);
        },
      });
      // Handle the parsed transactions here (e.g. update state or navigate)
      console.log('Uploaded transactions:', response.data);
      setSuccess('File uploaded successfully');
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data.detail || err.message);
      } else {
        setError('An unknown error occurred.');
      }
    } finally {
      setIsUploading(false);
      setFile(null);
    }
  };

  return (
    <div className="mt-6 max-w-xl">
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          'rounded-lg border border-dashed p-6 transition-colors',
          isDragging ? 'border-black bg-gray-50' : 'border-gray-300'
        )}
      >
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 flex items-center justify-center rounded-md bg-gray-100">
            <svg className="h-5 w-5 text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 5 17 10" />
              <line x1="12" y1="5" x2="12" y2="21" />
            </svg>
          </div>
          <div>
            <p className="font-medium">Upload transactions</p>
            <p className="text-sm text-gray-500">Drag and drop a CSV or Excel file here, or browse to select</p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <input
            ref={inputRef}
            id="file-input"
            type="file"
            accept=".csv,.xls,.xlsx"
            onChange={handleChange}
            disabled={isUploading}
            className="hidden"
          />
          <Button type="button" onClick={() => inputRef.current?.click()} variant="outline">
            Choose file
          </Button>
          <Button type="button" variant="ghost" onClick={() => setFile(null)} disabled={!file || isUploading}>
            Clear
          </Button>
          <div className="text-sm text-gray-600 truncate max-w-[50%] flex items-center gap-2">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            {file ? file.name : 'No file selected'}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-4">
          <Button
            type="submit"
            size="lg"
            disabled={!file || isUploading}
            className={cn(
              'group shadow-sm hover:shadow-md transition-all',
              'ring-1 ring-black/10 hover:ring-black/20'
            )}
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Uploading…</span>
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" />
                <span>Upload</span>
              </>
            )}
          </Button>
        </form>

        {isUploading && (
          <div className="mt-3 h-2 w-full rounded bg-gray-100">
            <div className="h-2 rounded bg-black transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}

        {success && (
          <div className="mt-3 inline-flex items-center gap-2 text-green-600 text-sm">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            {success}
          </div>
        )}
        {error && (
          <div className="mt-3 inline-flex items-center gap-2 text-red-600 text-sm">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;