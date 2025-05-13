import React, { useState, useEffect } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import FileUpload from "../components/ui/file-upload";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { 
  FileIcon, 
  FolderIcon, 
  CalendarIcon, 
  DownloadIcon, 
  Share2Icon, 
  TrashIcon, 
  UploadIcon, 
  FileTextIcon, 
  BookOpenIcon, 
  FileSpreadsheetIcon as FileSpreadsheetIconLucide,
  CreditCard,
  X,
  DatabaseIcon,
  MessageSquareIcon,
  BarChartIcon
} from "lucide-react";
import { 
  Dialog, 
  DialogTrigger, 
  DialogContent, 
  DialogHeader, 
  DialogFooter, 
  DialogTitle, 
  DialogDescription,
  DialogClose
} from "../components/ui/nested-dialog";
import { Card, CardContent } from '../components/ui/card';
import { FileUploadFeatures } from '../components/blocks/file-upload-features';

// Create an alias for FileSpreadsheetIcon to use in components
const FileSpreadsheetIcon = FileSpreadsheetIconLucide;

export default function FileUploadPage() {
  // This will store the files data that will come from the backend
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for document upload dialog
  const [docTitle, setDocTitle] = useState('');
  const [docDescription, setDocDescription] = useState('');
  const [tags, setTags] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = React.useRef(null);

  // Fetch files from the backend
  useEffect(() => {
    // Simulate loading state
    const timer = setTimeout(() => {
      try {
        // In a real implementation, you would fetch data from an API
        // For now, we'll just set an empty array
        setFiles([]);
        setLoading(false);
      } catch (err) {
        setError("Failed to load files");
        setLoading(false);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // Helper function to format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  // Helper function to format date
  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  // Helper function to get icon based on file type
  const getFileIcon = (type) => {
    if (type.includes('image')) return '🖼️';
    if (type.includes('pdf')) return '📄';
    if (type.includes('spreadsheet') || type.includes('excel')) return '📊';
    if (type.includes('presentation') || type.includes('powerpoint')) return '📑';
    if (type.includes('text')) return '📝';
    return '📁';
  };
  
  // Handle file selection
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };
  
  // Handle form submission
  const handleSubmit = () => {
    // Here you would implement the actual file upload logic
    console.log({
      docTitle,
      docDescription,
      tags: tags.split(',').map(tag => tag.trim()),
      file: selectedFile
    });
    
    // Reset form
    setDocTitle('');
    setDocDescription('');
    setTags('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    
    // You could add a success message or redirect here
  };

  return (
    <div>
      <FileUploadFeatures />
      
      <div className="container mx-auto p-4 md:p-6 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">File Management</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Upload, manage, and organize your files
          </p>
        </div>

        <div className="flex justify-center w-full mb-8">
          <Tabs defaultValue="view" className="w-full max-w-5xl">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="view">View Files/Data</TabsTrigger>
              <TabsTrigger value="add">Add new files & data</TabsTrigger>
            </TabsList>
            
            <TabsContent value="view" className="mt-6">
              <div className="bg-zinc-50 dark:bg-zinc-800/80 rounded-xl p-6">
                <h3 className="text-xl font-medium mb-4">Your Files & Data</h3>
                
                {loading ? (
                  <div className="flex justify-center items-center py-10">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
                  </div>
                ) : error ? (
                  <div className="text-center text-red-500 py-8">{error}</div>
                ) : files.length === 0 ? (
                  <div className="text-center py-16 px-4">
                    <div className="mx-auto w-16 h-16 mb-4 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
                      <FolderIcon className="h-8 w-8 text-primary" />
                    </div>
                    <h4 className="text-lg font-medium mb-2">No files uploaded yet</h4>
                    <p className="text-zinc-500 dark:text-zinc-400 mb-6 max-w-md mx-auto">
                      Upload your first document using the "Add new files & data" tab to get started.
                    </p>
                    <button 
                      onClick={() => document.querySelector('[data-value="add"]').click()}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium transition-colors hover:bg-primary/90">
                      <UploadIcon className="w-4 h-4" />
                      Upload your first file
                    </button>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 shadow">
                    <Table>
                      <TableCaption>List of uploaded files and data</TableCaption>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[50px]">Type</TableHead>
                          <TableHead>File Name</TableHead>
                          <TableHead>Size</TableHead>
                          <TableHead>Upload Date</TableHead>
                          <TableHead>Owner</TableHead>
                          <TableHead>Tags</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {files.map((file) => (
                          <TableRow key={file.id}>
                            <TableCell className="font-medium text-lg">{getFileIcon(file.type)}</TableCell>
                            <TableCell className="font-medium">{file.name}</TableCell>
                            <TableCell>{formatFileSize(file.size)}</TableCell>
                            <TableCell>{formatDate(file.uploadDate)}</TableCell>
                            <TableCell>{file.owner}</TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-1">
                                {file.tags.map((tag, index) => (
                                  <span 
                                    key={index} 
                                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <button className="text-gray-500 hover:text-primary" title="Download">
                                  <DownloadIcon className="h-4 w-4" />
                                </button>
                                <button className="text-gray-500 hover:text-green-600" title="Share">
                                  <Share2Icon className="h-4 w-4" />
                                </button>
                                <button className="text-gray-500 hover:text-red-600" title="Delete">
                                  <TrashIcon className="h-4 w-4" />
                                </button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="add" className="mt-6">
              <div className="bg-zinc-50 dark:bg-zinc-800/80 rounded-xl p-6 mb-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
                  <h3 className="text-xl font-medium">Upload Options</h3>
                  
                  <Dialog>
                    <DialogTrigger asChild>
                      <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium transition-colors hover:bg-primary/90">
                        <FileTextIcon className="w-5 h-5" />
                        Upload docs
                      </button>
                    </DialogTrigger>
                    
                    <DialogContent className="p-0">
                      <DialogHeader className="border-b p-4">
                        <DialogTitle>Upload Documents</DialogTitle>
                        <DialogDescription>
                          Enter document information and select a file to upload
                        </DialogDescription>
                      </DialogHeader>

                      <div className="flex flex-col gap-4 p-4">
                        <div className="flex flex-col">
                          <label className="mb-1.5 text-xs text-muted-foreground">
                            Collection Title*
                          </label>
                          <div className="relative">
                            <input
                              type="text"
                              value={docTitle}
                              onChange={(e) => setDocTitle(e.target.value)}
                              placeholder="Enter document title"
                              className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-800"
                            />
                          </div>
                        </div>
                        
                        <div className="flex flex-col">
                          <label className="mb-1.5 text-xs text-muted-foreground">
                            Description
                          </label>
                          <div className="relative">
                            <textarea
                              value={docDescription}
                              onChange={(e) => setDocDescription(e.target.value)}
                              placeholder="Describe the document (optional)"
                              className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary min-h-[100px] dark:bg-gray-800"
                            />
                          </div>
                        </div>
                        
                        <div className="flex flex-col">
                          <label className="mb-1.5 text-xs text-muted-foreground">
                            Upload File*
                          </label>
                          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-md hover:border-primary transition-colors cursor-pointer"
                              onClick={() => fileInputRef.current?.click()}>
                            <div className="space-y-1 text-center">
                              <div className="mx-auto h-12 w-12 text-gray-400">
                                {selectedFile ? (
                                  <div className="flex items-center justify-center h-full w-full bg-primary/10 dark:bg-primary/20 rounded-full text-primary">
                                    <FileIcon className="h-6 w-6" />
                                  </div>
                                ) : (
                                  <UploadIcon className="h-12 w-12" />
                                )}
                              </div>
                              <div className="flex text-sm text-gray-600 dark:text-gray-400">
                                <label className="relative cursor-pointer rounded-md font-medium text-primary dark:text-primary hover:text-primary/80">
                                  <span>{selectedFile ? selectedFile.name : 'Upload a file'}</span>
                                  <input
                                    id="file-upload"
                                    name="file-upload"
                                    type="file"
                                    className="sr-only"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
                                  />
                                </label>
                                {!selectedFile && <p className="pl-1">or drag and drop</p>}
                              </div>
                              {!selectedFile && (
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX up to 10MB
                                </p>
                              )}
                              {selectedFile && (
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  {formatFileSize(selectedFile.size)}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <DialogFooter className="flex flex-col items-center justify-between space-y-2 border-t px-4 py-2 sm:flex-row sm:space-x-2 sm:space-y-0">
                        <DialogClose asChild>
                          <button className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 dark:text-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 w-full sm:w-auto">
                            Cancel
                          </button>
                        </DialogClose>
                        <button 
                          onClick={handleSubmit}
                          disabled={!docTitle || !selectedFile}
                          className={`px-4 py-2 text-sm font-medium rounded-md text-white w-full sm:w-auto ${
                            !docTitle || !selectedFile 
                              ? 'bg-primary/50 cursor-not-allowed' 
                              : 'bg-primary hover:bg-primary/90'
                          }`}
                        >
                          Upload Document
                        </button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
                
                <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                  <FileUpload />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
} 