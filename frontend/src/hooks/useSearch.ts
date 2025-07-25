import { useQuery, useMutation } from '@tanstack/react-query'
import { searchService } from '@/services/search'

export function useSemanticSearch(query: string, limit: number = 10) {
  return useQuery({
    queryKey: ['search', 'semantic', query, limit],
    queryFn: () => searchService.semanticSearch(query, limit),
    enabled: query.length > 0,
  })
}

export function useRAGQuery() {
  return useMutation({
    mutationFn: ({ question, mode }: { question: string; mode?: string }) =>
      searchService.ragQuery(question, mode),
  })
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ['search', 'suggestions', query],
    queryFn: () => searchService.getSearchSuggestions(query),
    enabled: query.length > 2,
  })
}