import React, { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Upload, Loader2 } from 'lucide-react';
import { Dropzone, DropzoneContent, DropzoneEmptyState } from '@/components/ui/shadcn-io/dropzone';
import { Progress } from '@/components/ui/progress';

/**
 * FileUpload component allows users to select and submit CSV or Excel files
 * to the FastAPI backend. Once uploaded, the response is printed to the console.
 */
const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Drag-and-drop is handled within Dropzone

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
    <div className="mt-6 max-w-xl space-y-4">
      <Dropzone
        accept={{
          'text/csv': ['.csv'],
          'application/vnd.ms-excel': ['.xls'],
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        }}
        maxFiles={1}
        disabled={isUploading}
        src={file ? [file] : undefined}
        onDrop={(accepted) => setFile(accepted[0] || null)}
      >
        <DropzoneContent />
        <DropzoneEmptyState />
      </Dropzone>

      <div className="flex items-center gap-3">
        <Button type="button" variant="ghost" onClick={() => setFile(null)} disabled={!file || isUploading}>
          Clear
        </Button>
      </div>

      <form onSubmit={handleSubmit}>
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
          <div className="mt-3">
            <Progress value={progress} />
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
  );
};

export default FileUpload;