import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { 
  File, 
  FileText, 
  Image, 
  Music, 
  Video, 
  Search, 
  Filter,
  SortAsc,
  SortDesc,
  MoreHorizontal,
  Eye,
  Download,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { documentsService, Document } from '@/services/documents'
import { toast } from 'sonner'

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void
  onDocumentView?: (document: Document) => void
}

type SortField = 'filename' | 'created_at' | 'file_size' | 'processing_status'
type SortDirection = 'asc' | 'desc'
type FilterStatus = 'all' | 'queued' | 'processing' | 'completed' | 'failed'

export function DocumentList({ onDocumentSelect, onDocumentView }: DocumentListProps) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')

  const { data: documents = [], isLoading, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsService.getDocuments,
    refetchInterval: 5000, // Refetch every 5 seconds to update processing status
  })

  const filteredAndSortedDocuments = useMemo(() => {
    let filtered = documents

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(doc => 
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(doc => doc.processing_status === filterStatus)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any = a[sortField]
      let bValue: any = b[sortField]

      if (sortField === 'created_at') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }

      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    return filtered
  }, [documents, searchQuery, sortField, sortDirection, filterStatus])

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <Image className="w-4 h-4" />
    if (fileType.startsWith('audio/')) return <Music className="w-4 h-4" />
    if (fileType.startsWith('video/')) return <Video className="w-4 h-4" />
    if (fileType === 'application/pdf') return <FileText className="w-4 h-4" />
    return <File className="w-4 h-4" />
  }

  const getStatusIcon = (status: Document['processing_status']) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: Document['processing_status']) => {
    switch (status) {
      case 'queued': return 'secondary'
      case 'processing': return 'default'
      case 'completed': return 'success'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleDelete = async (document: Document) => {
    try {
      await documentsService.deleteDocument(document.id)
      toast.success(`Document "${document.filename}" deleted successfully`)
      refetch()
    } catch (error) {
      toast.error(`Failed to delete document: ${error}`)
    }
  }

  const handleDownload = (document: Document) => {
    // Create download link
    const link = window.document.createElement('a')
    link.href = `/api/documents/${document.id}/download`
    link.download = document.filename
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
  }

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span>Loading documents...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
        
        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <div className="flex gap-2">
            <Select value={filterStatus} onValueChange={(value: FilterStatus) => setFilterStatus(value)}>
              <SelectTrigger className="w-[140px]">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="queued">Queued</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {filteredAndSortedDocuments.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {documents.length === 0 ? (
              <div>
                <File className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No documents uploaded yet</p>
                <p className="text-sm">Upload your first document to get started</p>
              </div>
            ) : (
              <div>
                <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No documents match your search</p>
                <p className="text-sm">Try adjusting your search or filters</p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 px-4 py-2 text-sm font-medium text-muted-foreground border-b">
              <div className="col-span-5 flex items-center cursor-pointer" onClick={() => toggleSort('filename')}>
                Name
                {sortField === 'filename' && (
                  sortDirection === 'asc' ? <SortAsc className="w-4 h-4 ml-1" /> : <SortDesc className="w-4 h-4 ml-1" />
                )}
              </div>
              <div className="col-span-2 flex items-center cursor-pointer" onClick={() => toggleSort('processing_status')}>
                Status
                {sortField === 'processing_status' && (
                  sortDirection === 'asc' ? <SortAsc className="w-4 h-4 ml-1" /> : <SortDesc className="w-4 h-4 ml-1" />
                )}
              </div>
              <div className="col-span-2 flex items-center cursor-pointer" onClick={() => toggleSort('file_size')}>
                Size
                {sortField === 'file_size' && (
                  sortDirection === 'asc' ? <SortAsc className="w-4 h-4 ml-1" /> : <SortDesc className="w-4 h-4 ml-1" />
                )}
              </div>
              <div className="col-span-2 flex items-center cursor-pointer" onClick={() => toggleSort('created_at')}>
                Created
                {sortField === 'created_at' && (
                  sortDirection === 'asc' ? <SortAsc className="w-4 h-4 ml-1" /> : <SortDesc className="w-4 h-4 ml-1" />
                )}
              </div>
              <div className="col-span-1"></div>
            </div>

            {/* Document Rows */}
            {filteredAndSortedDocuments.map((document) => (
              <div
                key={document.id}
                className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-muted/50 rounded-lg cursor-pointer transition-colors"
                onClick={() => onDocumentSelect?.(document)}
              >
                <div className="col-span-5 flex items-center gap-3 min-w-0">
                  {getFileIcon(document.file_type)}
                  <span className="truncate font-medium">{document.filename}</span>
                </div>
                
                <div className="col-span-2 flex items-center gap-2">
                  {getStatusIcon(document.processing_status)}
                  <Badge variant={getStatusColor(document.processing_status)} className="text-xs">
                    {document.processing_status}
                  </Badge>
                </div>
                
                <div className="col-span-2 flex items-center text-sm text-muted-foreground">
                  {formatFileSize(document.file_size || 0)}
                </div>
                
                <div className="col-span-2 flex items-center text-sm text-muted-foreground">
                  {formatDate(document.created_at)}
                </div>
                
                <div className="col-span-1 flex items-center justify-end">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" onClick={(e) => e.stopPropagation()}>
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        if (document.file_type === 'application/pdf') {
                          navigate(`/pdf/${document.id}`)
                        } else {
                          onDocumentView?.(document)
                        }
                      }}>
                        <Eye className="w-4 h-4 mr-2" />
                        {document.file_type === 'application/pdf' ? 'View PDF' : 'View'}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        handleDownload(document)
                      }}>
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(document)
                        }}
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}