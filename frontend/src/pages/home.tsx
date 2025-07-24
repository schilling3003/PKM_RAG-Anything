import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function HomePage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Welcome to AI PKM Tool</h1>
        <p className="text-muted-foreground">
          Your AI-powered Personal Knowledge Management system
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Create and manage your markdown notes with wiki-style linking
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Upload and process multimodal documents with AI
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Knowledge Graph</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Visualize connections between your notes and documents
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}