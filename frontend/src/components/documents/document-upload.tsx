import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { documentsService } from '@/services/documents'
import { toast } from 'sonner'

interface UploadFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress: number
  error?: string
}

interface DocumentUploadProps {
  onUploadComplete?: (documentId: string) => void
  onUploadStart?: () => void
}

export function DocumentUpload({ onUploadComplete, onUploadStart }: DocumentUploadProps) {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])

  const handleFileUpload = useCallback(async (uploadFile: UploadFile) => {
    try {
      onUploadStart?.()
      
      // Update status to uploading
      setUploadFiles(prev => 
        prev.map(f => f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 10 } : f)
      )

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadFiles(prev => 
          prev.map(f => {
            if (f.id === uploadFile.id && f.progress < 90) {
              return { ...f, progress: f.progress + 10 }
            }
            return f
          })
        )
      }, 200)

      // Upload the file
      const response = await documentsService.uploadDocument(uploadFile.file)
      
      clearInterval(progressInterval)
      
      // Update status to completed
      setUploadFiles(prev => 
        prev.map(f => f.id === uploadFile.id ? { ...f, status: 'completed', progress: 100 } : f)
      )

      toast.success(`File "${uploadFile.file.name}" uploaded successfully`)
      onUploadComplete?.(response.document_id)

      // Remove completed file after 3 seconds
      setTimeout(() => {
        setUploadFiles(prev => prev.filter(f => f.id !== uploadFile.id))
      }, 3000)

    } catch (error) {
      setUploadFiles(prev => 
        prev.map(f => f.id === uploadFile.id ? { 
          ...f, 
          status: 'error', 
          progress: 0,
          error: error instanceof Error ? error.message : 'Upload failed'
        } : f)
      )
      
      toast.error(`Failed to upload "${uploadFile.file.name}"`)
    }
  }, [onUploadStart, onUploadComplete])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substring(2, 9),
      status: 'pending',
      progress: 0
    }))
    
    setUploadFiles(prev => [...prev, ...newFiles])
    
    // Start uploading files
    newFiles.forEach(uploadFile => {
      handleFileUpload(uploadFile)
    })
  }, [handleFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg'],
      'video/*': ['.mp4', '.avi', '.mov', '.wmv']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true
  })

  const removeFile = (fileId: string) => {
    setUploadFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return 'secondary'
      case 'uploading': return 'default'
      case 'completed': return 'success'
      case 'error': return 'destructive'
      default: return 'secondary'
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop files here...</p>
            ) : (
              <div>
                <p className="text-lg font-medium mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  Supports PDF, Word, text, images, audio, and video files (max 100MB)
                </p>
                <Button variant="outline">
                  <File className="w-4 h-4 mr-2" />
                  Choose Files
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {uploadFiles.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium mb-3">Upload Progress</h3>
            <div className="space-y-3">
              {uploadFiles.map((uploadFile) => (
                <div key={uploadFile.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <File className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium truncate">
                        {uploadFile.file.name}
                      </p>
                      <Badge variant={getStatusColor(uploadFile.status) as any}>
                        {uploadFile.status}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{formatFileSize(uploadFile.file.size)}</span>
                      {uploadFile.status === 'uploading' && (
                        <>
                          <span>•</span>
                          <span>{uploadFile.progress}%</span>
                        </>
                      )}
                    </div>
                    
                    {uploadFile.status === 'uploading' && (
                      <Progress value={uploadFile.progress} className="mt-2 h-1" />
                    )}
                    
                    {uploadFile.error && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-destructive">
                        <AlertCircle className="w-3 h-3" />
                        <span>{uploadFile.error}</span>
                      </div>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(uploadFile.id)}
                    className="flex-shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}