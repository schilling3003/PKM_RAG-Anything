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

export const documentsService = {
  // Get all documents
  async getDocuments(): Promise<Document[]> {
    const response = await api.get('/documents')
    return response.data
  },

  // Get a specific document
  async getDocument(id: string): Promise<Document> {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  // Upload a document
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
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