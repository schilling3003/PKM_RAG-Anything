import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PDFViewer } from '@/components/documents/pdf-viewer'
import { documentsService } from '@/services/documents'

export function PDFViewerPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const navigate = useNavigate()

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => documentsService.getDocument(documentId!),
    enabled: !!documentId,
  })

  const handleClose = () => {
    navigate('/documents')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading document...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-destructive mb-4">Failed to load document</p>
          <Button onClick={handleClose}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Documents
          </Button>
        </div>
      </div>
    )
  }

  if (document.file_type !== 'application/pdf') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">This document is not a PDF file</p>
          <Button onClick={handleClose}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Documents
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen">
      <PDFViewer
        documentId={document.id}
        filename={document.filename}
        onClose={handleClose}
      />
    </div>
  )
}