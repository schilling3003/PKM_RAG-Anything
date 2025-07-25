export interface SearchResult {
  id: string
  title: string
  content: string
  type: 'note' | 'document'
  score: number
  highlights?: string[]
}

export interface RAGResponse {
  answer: string
  sources: Array<{
    id: string
    title: string
    content: string
    score: number
  }>
  mode: string
}

export interface SearchQuery {
  query: string
  type: 'semantic' | 'rag'
  mode?: string
  limit?: number
}