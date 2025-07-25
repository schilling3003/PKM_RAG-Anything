export interface Document {
  id: string
  filename: string
  file_type: string
  file_path: string
  processing_status: 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
}

export interface DocumentUploadResponse {
  document_id: string
  task_id: string
  status: string
  message: string
}