import { useQuery } from '@tanstack/react-query'
import { graphService } from '@/services/graph'

export function useGraphData(filters?: Record<string, any>) {
  return useQuery({
    queryKey: ['graph', filters],
    queryFn: () => graphService.getGraphData(filters),
  })
}

export function useNodeDetails(nodeId: string) {
  return useQuery({
    queryKey: ['graph', 'node', nodeId],
    queryFn: () => graphService.getNodeDetails(nodeId),
    enabled: !!nodeId,
  })
}

export function useNodeRelationships(nodeId: string) {
  return useQuery({
    queryKey: ['graph', 'relationships', nodeId],
    queryFn: () => graphService.getNodeRelationships(nodeId),
    enabled: !!nodeId,
  })
}