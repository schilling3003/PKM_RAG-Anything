import api from './api'

export interface GraphNode {
  id: string
  label: string
  type: 'note' | 'document' | 'concept'
  properties: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface RelatedContent {
  node_id: string
  relationship: string
  weight: number
}

export const graphService = {
  // Get knowledge graph data
  async getGraphData(filters?: Record<string, any>): Promise<GraphData> {
    const response = await api.get('/graph', {
      params: filters
    })
    return response.data
  },

  // Get specific node details
  async getNodeDetails(nodeId: string): Promise<GraphNode> {
    const response = await api.get(`/graph/node/${nodeId}`)
    return response.data
  },

  // Get relationship data
  async getRelationships(): Promise<GraphEdge[]> {
    const response = await api.get('/graph/relationships')
    return response.data
  },

  // Find related content for a node
  async findRelatedContent(nodeId: string): Promise<RelatedContent[]> {
    const response = await api.get(`/graph/node/${nodeId}/related`)
    return response.data
  },

  // Get node relationships (alias for findRelatedContent for consistency)
  async getNodeRelationships(nodeId: string): Promise<RelatedContent[]> {
    return this.findRelatedContent(nodeId)
  },
}