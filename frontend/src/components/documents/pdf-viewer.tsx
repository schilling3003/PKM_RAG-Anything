import { useState, useCallback, useRef, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { 
  ChevronLeft, 
  ChevronRight, 
  ZoomIn, 
  ZoomOut, 
  RotateCw,
  Search,
  Download,
  Maximize,
  Minimize,
  BookOpen,
  StickyNote,
  Highlighter,
  Type,
  X,

} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface PDFViewerProps {
  documentId: string
  filename: string
  onClose?: () => void
}

interface Annotation {
  id: string
  page: number
  x: number
  y: number
  width: number
  height: number
  type: 'note' | 'highlight' | 'text'
  content: string
  color: string
  created_at: string
}

interface SearchResult {
  page: number
  text: string
  position: { x: number; y: number }
}

export function PDFViewer({ documentId, filename, onClose }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [rotation, setRotation] = useState<number>(0)
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [currentSearchIndex, setCurrentSearchIndex] = useState<number>(0)
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [selectedTool, setSelectedTool] = useState<'select' | 'note' | 'highlight' | 'text'>('select')
  // const [isAnnotating, setIsAnnotating] = useState<boolean>(false)
  const [newAnnotation, setNewAnnotation] = useState<Partial<Annotation> | null>(null)
  const [showAnnotationDialog, setShowAnnotationDialog] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const containerRef = useRef<HTMLDivElement>(null)
  const pageRefs = useRef<{ [key: number]: HTMLDivElement }>({})

  const pdfUrl = `/api/documents/${documentId}/pdf`

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setLoading(false)
    setError(null)
  }, [])

  const onDocumentLoadError = useCallback((error: Error) => {
    setError(`Failed to load PDF: ${error.message}`)
    setLoading(false)
  }, [])

  const goToPage = (page: number) => {
    if (page >= 1 && page <= numPages) {
      setCurrentPage(page)
      // Scroll to page
      const pageElement = pageRefs.current[page]
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }

  const nextPage = () => goToPage(currentPage + 1)
  const prevPage = () => goToPage(currentPage - 1)

  const zoomIn = () => setScale(prev => Math.min(prev + 0.25, 3.0))
  const zoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.5))
  const resetZoom = () => setScale(1.0)

  const rotate = () => setRotation(prev => (prev + 90) % 360)

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    // Simulate search functionality
    // In a real implementation, you would use PDF.js text extraction
    const mockResults: SearchResult[] = [
      { page: 1, text: searchQuery, position: { x: 100, y: 200 } },
      { page: 3, text: searchQuery, position: { x: 150, y: 300 } },
    ]
    
    setSearchResults(mockResults)
    setCurrentSearchIndex(0)
    
    if (mockResults.length > 0) {
      goToPage(mockResults[0].page)
      toast.success(`Found ${mockResults.length} results`)
    } else {
      toast.info('No results found')
    }
  }

  const nextSearchResult = () => {
    if (searchResults.length > 0) {
      const nextIndex = (currentSearchIndex + 1) % searchResults.length
      setCurrentSearchIndex(nextIndex)
      goToPage(searchResults[nextIndex].page)
    }
  }

  const prevSearchResult = () => {
    if (searchResults.length > 0) {
      const prevIndex = currentSearchIndex === 0 ? searchResults.length - 1 : currentSearchIndex - 1
      setCurrentSearchIndex(prevIndex)
      goToPage(searchResults[prevIndex].page)
    }
  }

  const handlePageClick = (event: React.MouseEvent, pageNumber: number) => {
    if (selectedTool === 'select') return

    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    const annotation: Partial<Annotation> = {
      id: Math.random().toString(36).substr(2, 9),
      page: pageNumber,
      x: x / scale,
      y: y / scale,
      width: selectedTool === 'highlight' ? 100 : 20,
      height: selectedTool === 'highlight' ? 20 : 20,
      type: selectedTool === 'note' ? 'note' : selectedTool === 'highlight' ? 'highlight' : 'text',
      content: '',
      color: selectedTool === 'highlight' ? '#ffff00' : '#ff6b6b',
      created_at: new Date().toISOString()
    }

    setNewAnnotation(annotation)
    setShowAnnotationDialog(true)
  }

  const saveAnnotation = (content: string) => {
    if (newAnnotation) {
      const annotation: Annotation = {
        ...newAnnotation,
        content
      } as Annotation

      setAnnotations(prev => [...prev, annotation])
      setNewAnnotation(null)
      setShowAnnotationDialog(false)
      toast.success('Annotation saved')
    }
  }

  const deleteAnnotation = (annotationId: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== annotationId))
    toast.success('Annotation deleted')
  }

  const downloadPDF = () => {
    const link = window.document.createElement('a')
    link.href = pdfUrl
    link.download = filename
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  if (loading) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <BookOpen className="w-12 h-12 mx-auto mb-4 animate-pulse" />
            <p>Loading PDF...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-destructive">
            <X className="w-12 h-12 mx-auto mb-4" />
            <p>{error}</p>
            <Button variant="outline" onClick={() => window.location.reload()} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div 
      ref={containerRef}
      className={`flex flex-col h-full bg-background ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center gap-2">
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          )}
          <h3 className="font-medium truncate max-w-xs">{filename}</h3>
        </div>

        <div className="flex items-center gap-2">
          {/* Navigation */}
          <div className="flex items-center gap-1">
            <Button variant="outline" size="sm" onClick={prevPage} disabled={currentPage <= 1}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="flex items-center gap-2 px-2">
              <Input
                type="number"
                value={currentPage}
                onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
                className="w-16 text-center"
                min={1}
                max={numPages}
              />
              <span className="text-sm text-muted-foreground">of {numPages}</span>
            </div>
            <Button variant="outline" size="sm" onClick={nextPage} disabled={currentPage >= numPages}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Zoom Controls */}
          <div className="flex items-center gap-1">
            <Button variant="outline" size="sm" onClick={zoomOut} disabled={scale <= 0.5}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={resetZoom}>
              {Math.round(scale * 100)}%
            </Button>
            <Button variant="outline" size="sm" onClick={zoomIn} disabled={scale >= 3.0}>
              <ZoomIn className="w-4 h-4" />
            </Button>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Tools */}
          <div className="flex items-center gap-1">
            <Button 
              variant={selectedTool === 'note' ? 'default' : 'outline'} 
              size="sm" 
              onClick={() => setSelectedTool('note')}
            >
              <StickyNote className="w-4 h-4" />
            </Button>
            <Button 
              variant={selectedTool === 'highlight' ? 'default' : 'outline'} 
              size="sm" 
              onClick={() => setSelectedTool('highlight')}
            >
              <Highlighter className="w-4 h-4" />
            </Button>
            <Button 
              variant={selectedTool === 'text' ? 'default' : 'outline'} 
              size="sm" 
              onClick={() => setSelectedTool('text')}
            >
              <Type className="w-4 h-4" />
            </Button>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Additional Controls */}
          <Button variant="outline" size="sm" onClick={rotate}>
            <RotateCw className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={downloadPDF}>
            <Download className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={toggleFullscreen}>
            {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-2 p-4 border-b bg-muted/50">
        <div className="flex-1 flex items-center gap-2">
          <Search className="w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search in document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button size="sm" onClick={handleSearch}>
            Search
          </Button>
        </div>
        
        {searchResults.length > 0 && (
          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              {currentSearchIndex + 1} of {searchResults.length}
            </Badge>
            <Button variant="outline" size="sm" onClick={prevSearchResult}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={nextSearchResult}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* PDF Content */}
      <div className="flex-1 flex">
        {/* Main PDF View */}
        <ScrollArea className="flex-1">
          <div className="p-4">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={<div>Loading PDF...</div>}
            >
              {Array.from(new Array(numPages), (_, index) => (
                <div
                  key={`page_${index + 1}`}
                  ref={(el) => {
                    if (el) pageRefs.current[index + 1] = el
                  }}
                  className="relative mb-4 border rounded-lg overflow-hidden bg-white shadow-sm"
                  onClick={(e) => handlePageClick(e, index + 1)}
                  style={{ cursor: selectedTool !== 'select' ? 'crosshair' : 'default' }}
                >
                  <Page
                    pageNumber={index + 1}
                    scale={scale}
                    rotate={rotation}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                  />
                  
                  {/* Annotations Overlay */}
                  {annotations
                    .filter(annotation => annotation.page === index + 1)
                    .map(annotation => (
                      <div
                        key={annotation.id}
                        className="absolute cursor-pointer group"
                        style={{
                          left: annotation.x * scale,
                          top: annotation.y * scale,
                          width: annotation.width * scale,
                          height: annotation.height * scale,
                          backgroundColor: annotation.type === 'highlight' ? annotation.color : 'transparent',
                          border: annotation.type !== 'highlight' ? `2px solid ${annotation.color}` : 'none',
                          opacity: annotation.type === 'highlight' ? 0.3 : 1,
                        }}
                        title={annotation.content}
                      >
                        {annotation.type === 'note' && (
                          <StickyNote className="w-4 h-4" style={{ color: annotation.color }} />
                        )}
                        {annotation.type === 'text' && (
                          <Type className="w-4 h-4" style={{ color: annotation.color }} />
                        )}
                        
                        {/* Delete button on hover */}
                        <Button
                          variant="destructive"
                          size="sm"
                          className="absolute -top-2 -right-2 w-6 h-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteAnnotation(annotation.id)
                          }}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  
                  {/* Page number indicator */}
                  <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded text-xs">
                    {index + 1}
                  </div>
                </div>
              ))}
            </Document>
          </div>
        </ScrollArea>

        {/* Annotations Sidebar */}
        {annotations.length > 0 && (
          <div className="w-80 border-l bg-card">
            <div className="p-4">
              <h3 className="font-medium mb-4">Annotations ({annotations.length})</h3>
              <ScrollArea className="h-96">
                <div className="space-y-3">
                  {annotations.map(annotation => (
                    <Card key={annotation.id} className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <Badge variant="outline" className="text-xs">
                          Page {annotation.page}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteAnnotation(annotation.id)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                      <p className="text-sm">{annotation.content}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(annotation.created_at).toLocaleDateString()}
                      </p>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        )}
      </div>

      {/* Annotation Dialog */}
      <Dialog open={showAnnotationDialog} onOpenChange={setShowAnnotationDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Annotation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Content</label>
              <Textarea
                placeholder="Enter your annotation..."
                className="mt-1"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.ctrlKey) {
                    const content = e.currentTarget.value
                    if (content.trim()) {
                      saveAnnotation(content)
                    }
                  }
                }}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAnnotationDialog(false)}>
                Cancel
              </Button>
              <Button onClick={() => {
                const textarea = document.querySelector('textarea') as HTMLTextAreaElement
                const content = textarea?.value || ''
                if (content.trim()) {
                  saveAnnotation(content)
                }
              }}>
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}