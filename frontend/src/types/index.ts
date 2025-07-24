// Core data types for the application

export interface Note {
  id: string
  title: string
  content: string
  createdAt: string
  updatedAt: string
  tags: string[]
  links: string[]
  metadata: Record<string, any>
}

export interface Document {
  id: string
  filename: string
  fileType: string
  filePath: string
  fileSize: number
  processedAt: string
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  extractedText?: string
  metadata: Record<string, any>
  embeddingsGenerated: boolean
}

export interface SearchResult {
  id: string
  type: 'note' | 'document'
  title: string
  content: string
  relevanceScore: number
  highlights: string[]
  metadata: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: Record<string, any>
}

export interface GraphNode {
  id: string
  label: string
  type: 'note' | 'document' | 'concept' | 'entity'
  properties: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
  weight: number
  properties: Record<string, any>
}

export interface ProcessingStatus {
  documentId: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStep: string
  error?: string
}