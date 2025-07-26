import api from './api'

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  processing_status: 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  extracted_text?: string
  metadata?: Record<string, any>
  error_message?: string
}

export interface DocumentUploadResponse {
  document_id: string
  task_id: string
  status: string
  message: string
}

export interface ProcessingStatus {
  status: string
  progress?: number
  current_step?: string
  error_message?: string
}

// Development mode flag - set to true to use mock data
const USE_MOCK_DATA = false

export const documentsService = {
  // Get all documents
  async getDocuments(): Promise<Document[]> {
    if (USE_MOCK_DATA) {
      const { mockDocuments } = await import('./mock-data')
      return new Promise(resolve => setTimeout(() => resolve(mockDocuments), 500))
    }
    const response = await api.get('/documents')
    // Backend returns { documents: Document[], total: number, message: string }
    return response.data.documents || []
  },

  // Get a specific document
  async getDocument(id: string): Promise<Document> {
    if (USE_MOCK_DATA) {
      const { mockDocuments } = await import('./mock-data')
      const document = mockDocuments.find(doc => doc.id === id)
      if (!document) throw new Error('Document not found')
      return new Promise(resolve => setTimeout(() => resolve(document), 300))
    }
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  // Upload a document
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => 
        setTimeout(() => resolve({
          document_id: Math.random().toString(36).substr(2, 9),
          task_id: Math.random().toString(36).substr(2, 9),
          status: 'queued',
          message: `File "${file.name}" uploaded successfully`
        }), 1000)
      )
    }
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Get document processing status
  async getProcessingStatus(documentId: string): Promise<ProcessingStatus> {
    if (USE_MOCK_DATA) {
      const { mockProcessingStatus } = await import('./mock-data')
      return new Promise(resolve => setTimeout(() => resolve({
        ...mockProcessingStatus,
        error_message: mockProcessingStatus.error_message || undefined
      }), 200))
    }
    const response = await api.get(`/documents/${documentId}/status`)
    return response.data
  },

  // Delete a document
  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/documents/${id}`)
  },

  // Get PDF view URL
  getPdfViewUrl(documentId: string): string {
    return `/api/pdf/${documentId}/view`
  },

  // Get PDF metadata
  async getPdfMetadata(documentId: string): Promise<{ pages: number }> {
    const response = await api.get(`/pdf/${documentId}/pages`)
    return response.data
  },
}