// Re-export all types from services
export type { Note, CreateNoteRequest, UpdateNoteRequest } from '@/services/notes'
export type { Document, DocumentUploadResponse, ProcessingStatus } from '@/services/documents'
export type { SearchResult, RAGResponse, SearchSuggestion } from '@/services/search'
export type { GraphNode, GraphEdge, GraphData, RelatedContent } from '@/services/graph'
export type { WebSocketMessage, DocumentProcessingUpdate, GraphUpdate } from '@/services/websocket'

// Common UI types
export interface SelectOption {
  value: string
  label: string
}

export interface TabItem {
  id: string
  label: string
  content: React.ReactNode
}

// Application state types
export interface AppState {
  currentNote?: string
  currentDocument?: string
  sidebarCollapsed: boolean
  theme: 'light' | 'dark' | 'system'
}

// Error types
export interface ApiError {
  message: string
  status?: number
  code?: string
}

// File upload types
export interface FileUploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}