export interface GraphNode {
  id: string
  label: string
  type: string
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