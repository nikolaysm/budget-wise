import React, { useState } from 'react';
import axios from 'axios';

/**
 * FileUpload component allows users to select and submit CSV or Excel files
 * to the FastAPI backend. Once uploaded, the response is printed to the console.
 */
const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!file) return;
    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('/transactions/upload', formData, {
        baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // Handle the parsed transactions here (e.g. update state or navigate)
      console.log('Uploaded transactions:', response.data);
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
    <form onSubmit={handleSubmit} style={{ marginTop: '1rem' }}>
      <input
        type="file"
        accept=".csv,.xls,.xlsx"
        onChange={handleChange}
        disabled={isUploading}
      />
      <button type="submit" disabled={!file || isUploading} style={{ marginLeft: '0.5rem' }}>
        {isUploading ? 'Uploading…' : 'Upload'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  );
};

export default FileUpload;