'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { listUploadedFiles } from '@/lib/api';

interface UploadedFile {
  name: string;
  type: string;
  size: number;
  uploadDate: string;
}

const fileTypeIcons: Record<string, string> = {
  csv: '📊',
  pdf: '📄',
  docx: '📝',
  pptx: '📑',
  html: '🌐',
  default: '📁',
};

export default function FilesPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true);
        const response = await listUploadedFiles();
        setFiles(response.files || []);
      } catch (error) {
        console.error('Error fetching files:', error);
        toast.error('Error loading files');
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, []);

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase() || 'default';
    return fileTypeIcons[extension] || fileTypeIcons.default;
  };

  const formatFileSize = (size: number) => {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Uploaded Files</h1>

      {loading ? (
        <p>Loading files...</p>
      ) : files.length === 0 ? (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold mb-2">No Uploaded Files</h2>
          <p className="text-muted-foreground mb-6">
            You haven't uploaded any files yet.
          </p>
          <Button onClick={() => window.location.href = '/'}>
            Go to Create Agent
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {files.map((file) => (
            <Card key={file.name}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getFileIcon(file.name)}</span>
                    <CardTitle className="text-lg truncate max-w-[200px]" title={file.name}>
                      {file.name}
                    </CardTitle>
                  </div>
                  <span className="text-xs bg-muted px-2 py-1 rounded-md">
                    {file.type.toUpperCase()}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>Size: {formatFileSize(file.size)}</p>
                  <p>Uploaded: {formatDate(file.uploadDate)}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
} 