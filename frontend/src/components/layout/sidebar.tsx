import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  FileText, 
  Search, 
  Upload, 
  Network, 
  Plus, 
  Home,
  ChevronDown,
  ChevronRight,
  File
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useNotes } from '@/hooks/useNotes'
import { useDocuments } from '@/hooks/useDocuments'
import { cn } from '@/lib/utils'

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')
  const [notesExpanded, setNotesExpanded] = useState(true)
  const [documentsExpanded, setDocumentsExpanded] = useState(true)
  
  const { data: notes, isError: notesError, isLoading: notesLoading } = useNotes()
  const { data: documents, isError: documentsError, isLoading: documentsLoading } = useDocuments()

  const navigationItems = [
    {
      title: 'Home',
      href: '/',
      icon: Home,
    },
    {
      title: 'Search',
      href: '/search',
      icon: Search,
    },
    {
      title: 'Knowledge Graph',
      href: '/graph',
      icon: Network,
    },
  ]

  // Ensure we have arrays to work with, even if data is undefined
  const notesArray = Array.isArray(notes) ? notes : []
  const documentsArray = Array.isArray(documents) ? documents : []

  const filteredNotes = notesArray.filter(note =>
    note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    note.content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredDocuments = documentsArray.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className={cn('flex flex-col h-full bg-card border-r', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">AI PKM Tool</h1>
            <p className="text-xs text-muted-foreground">Knowledge Management</p>
          </div>
        </div>
        
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search notes and documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4">
        <nav className="space-y-1">
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link key={item.href} to={item.href}>
                <Button
                  variant={isActive ? 'secondary' : 'ghost'}
                  className="w-full justify-start"
                  size="sm"
                >
                  <item.icon className="w-4 h-4 mr-2" />
                  {item.title}
                </Button>
              </Link>
            )
          })}
        </nav>
      </div>

      <Separator />

      {/* Content Sections */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Notes Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Button
                variant="ghost"
                size="sm"
                className="p-0 h-auto font-medium"
                onClick={() => setNotesExpanded(!notesExpanded)}
              >
                {notesExpanded ? (
                  <ChevronDown className="w-4 h-4 mr-1" />
                ) : (
                  <ChevronRight className="w-4 h-4 mr-1" />
                )}
                Notes
                <Badge variant="secondary" className="ml-2">
                  {filteredNotes.length}
                </Badge>
              </Button>
              <Link to="/notes">
                <Button variant="ghost" size="sm" className="p-1 h-auto">
                  <Plus className="w-3 h-3" />
                </Button>
              </Link>
            </div>
            
            {notesExpanded && (
              <div className="space-y-1 ml-2">
                {notesLoading ? (
                  <p className="text-xs text-muted-foreground py-2">Loading notes...</p>
                ) : notesError ? (
                  <p className="text-xs text-red-500 py-2">Failed to load notes</p>
                ) : filteredNotes.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">
                    {searchQuery ? 'No notes found' : 'No notes yet'}
                  </p>
                ) : (
                  filteredNotes.slice(0, 10).map((note) => (
                    <Link key={note.id} to={`/notes/${note.id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-left h-auto py-1 px-2"
                      >
                        <FileText className="w-3 h-3 mr-2 flex-shrink-0" />
                        <span className="truncate text-xs">{note.title}</span>
                      </Button>
                    </Link>
                  ))
                )}
                {filteredNotes.length > 10 && (
                  <Link to="/notes">
                    <Button variant="ghost" size="sm" className="w-full text-xs">
                      View all {filteredNotes.length} notes
                    </Button>
                  </Link>
                )}
              </div>
            )}
          </div>

          {/* Documents Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Button
                variant="ghost"
                size="sm"
                className="p-0 h-auto font-medium"
                onClick={() => setDocumentsExpanded(!documentsExpanded)}
              >
                {documentsExpanded ? (
                  <ChevronDown className="w-4 h-4 mr-1" />
                ) : (
                  <ChevronRight className="w-4 h-4 mr-1" />
                )}
                Documents
                <Badge variant="secondary" className="ml-2">
                  {filteredDocuments.length}
                </Badge>
              </Button>
              <Link to="/documents">
                <Button variant="ghost" size="sm" className="p-1 h-auto">
                  <Upload className="w-3 h-3" />
                </Button>
              </Link>
            </div>
            
            {documentsExpanded && (
              <div className="space-y-1 ml-2">
                {documentsLoading ? (
                  <p className="text-xs text-muted-foreground py-2">Loading documents...</p>
                ) : documentsError ? (
                  <p className="text-xs text-red-500 py-2">Failed to load documents</p>
                ) : filteredDocuments.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">
                    {searchQuery ? 'No documents found' : 'No documents yet'}
                  </p>
                ) : (
                  filteredDocuments.slice(0, 10).map((doc) => (
                    <Link key={doc.id} to={`/documents/${doc.id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-left h-auto py-1 px-2"
                      >
                        <File className="w-3 h-3 mr-2 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <span className="truncate text-xs block">{doc.filename}</span>
                          <div className="flex items-center gap-1 mt-0.5">
                            <Badge 
                              variant={doc.processing_status === 'completed' ? 'default' : 'secondary'}
                              className="text-xs px-1 py-0"
                            >
                              {doc.processing_status}
                            </Badge>
                          </div>
                        </div>
                      </Button>
                    </Link>
                  ))
                )}
                {filteredDocuments.length > 10 && (
                  <Link to="/documents">
                    <Button variant="ghost" size="sm" className="w-full text-xs">
                      View all {filteredDocuments.length} documents
                    </Button>
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>

      {/* Footer Actions */}
      <div className="p-4 border-t space-y-2">
        <Link to="/notes">
          <Button className="w-full" size="sm">
            <Plus className="w-4 h-4 mr-2" />
            New Note
          </Button>
        </Link>
        <Link to="/documents">
          <Button variant="outline" className="w-full" size="sm">
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Button>
        </Link>
      </div>
    </div>
  )
}