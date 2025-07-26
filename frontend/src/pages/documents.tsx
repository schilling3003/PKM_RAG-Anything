import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, FileText, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DocumentUpload } from '@/components/documents/document-upload'
import { DocumentList } from '@/components/documents/document-list'
import { DocumentMetadata } from '@/components/documents/document-metadata'
import { ProcessingStatusIndicator } from '@/components/documents/processing-status'
import { documentsService, Document } from '@/services/documents'

export function DocumentsPage() {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [activeTab, setActiveTab] = useState('list')

  const { data: documents, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsService.getDocuments,
  })

  // Ensure we have an array to work with
  const documentsArray = Array.isArray(documents) ? documents : []

  const processingDocuments = documentsArray.filter(doc => 
    doc.processing_status === 'processing' || doc.processing_status === 'queued'
  )

  const handleUploadComplete = (documentId: string) => {
    console.log('Document uploaded:', documentId)
    refetch()
    // Switch to list tab to see the uploaded document
    setActiveTab('list')
  }

  const handleUploadStart = () => {
    refetch()
  }

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document)
  }

  const handleDocumentView = (document: Document) => {
    setSelectedDocument(document)
    // In a real implementation, this might open a PDF viewer or document viewer
    console.log('View document:', document)
  }

  const handleDocumentUpdate = (updatedDocument: Document) => {
    console.log('Document updated:', updatedDocument)
    refetch()
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Documents</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage your documents with AI-powered processing
          </p>
        </div>
        <Button onClick={() => setActiveTab('upload')}>
          <Plus className="w-4 h-4 mr-2" />
          Upload Document
        </Button>
      </div>

      {/* Processing Status Overview */}
      {processingDocuments.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Currently Processing ({processingDocuments.length})
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {processingDocuments.map((document) => (
              <ProcessingStatusIndicator
                key={document.id}
                document={document}
                onRetry={() => refetch()}
              />
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="list" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Document List
              </TabsTrigger>
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Upload
              </TabsTrigger>
            </TabsList>

            <TabsContent value="list" className="mt-6">
              <DocumentList
                onDocumentSelect={handleDocumentSelect}
                onDocumentView={handleDocumentView}
              />
            </TabsContent>

            <TabsContent value="upload" className="mt-6">
              <DocumentUpload
                onUploadComplete={handleUploadComplete}
                onUploadStart={handleUploadStart}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {selectedDocument ? (
            <>
              <DocumentMetadata
                document={selectedDocument}
                onUpdate={handleDocumentUpdate}
              />
              
              {(selectedDocument.processing_status === 'processing' || 
                selectedDocument.processing_status === 'queued' ||
                selectedDocument.processing_status === 'failed') && (
                <ProcessingStatusIndicator
                  document={selectedDocument}
                  onRetry={() => refetch()}
                />
              )}
            </>
          ) : (
            <div className="text-center p-8 text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Select a document to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Statistics */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">{documentsArray.length}</p>
              <p className="text-sm text-muted-foreground">Total Documents</p>
            </div>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-green-500" />
            <div>
              <p className="text-2xl font-bold">
                {documentsArray.filter(d => d.processing_status === 'completed').length}
              </p>
              <p className="text-sm text-muted-foreground">Processed</p>
            </div>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-yellow-500" />
            <div>
              <p className="text-2xl font-bold">
                {documentsArray.filter(d => d.processing_status === 'processing' || d.processing_status === 'queued').length}
              </p>
              <p className="text-sm text-muted-foreground">Processing</p>
            </div>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-red-500" />
            <div>
              <p className="text-2xl font-bold">
                {documentsArray.filter(d => d.processing_status === 'failed').length}
              </p>
              <p className="text-sm text-muted-foreground">Failed</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}