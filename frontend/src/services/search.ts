import api from './api'

export interface SearchResult {
  id: string
  title: string
  content: string
  type: 'note' | 'document'
  relevance_score: number
  snippet: string
  source_file?: string
}

export interface RAGResponse {
  answer: string
  sources: Array<{
    id: string
    title: string
    snippet: string
    relevance_score: number
  }>
  query_mode: string
}

export interface SearchSuggestion {
  text: string
  type: 'recent' | 'popular' | 'related'
}

export const searchService = {
  // Perform semantic search
  async semanticSearch(query: string, limit: number = 10): Promise<SearchResult[]> {
    const response = await api.get('/search', {
      params: { q: query, limit }
    })
    return response.data
  },

  // Perform RAG-based question answering
  async ragQuery(question: string, mode: string = 'hybrid'): Promise<RAGResponse> {
    const response = await api.post('/search/rag', {
      question,
      mode
    })
    return response.data
  },

  // Get search suggestions
  async getSearchSuggestions(query: string): Promise<SearchSuggestion[]> {
    const response = await api.get('/search/suggestions', {
      params: { q: query }
    })
    return response.data
  },
}