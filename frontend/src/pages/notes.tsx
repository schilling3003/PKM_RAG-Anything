import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { MarkdownEditor } from '@/components/editor'
import { useNotes, useNote, useCreateNote, useUpdateNote } from '@/hooks/useNotes'
import { Plus, Search, FileText } from 'lucide-react'
import { toast } from 'sonner'

export function NotesPage() {
  const { noteId } = useParams()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(noteId || null)
  const [editorContent, setEditorContent] = useState('')
  const [noteTitle, setNoteTitle] = useState('')
  const [isCreatingNew, setIsCreatingNew] = useState(false)

  // Hooks
  const { data: notes } = useNotes()
  const { data: selectedNote } = useNote(selectedNoteId || '')
  const createNoteMutation = useCreateNote()
  const updateNoteMutation = useUpdateNote()

  // Ensure we have an array to work with
  const notesArray = Array.isArray(notes) ? notes : []

  // Filter notes based on search
  const filteredNotes = notesArray.filter(note =>
    note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    note.content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Update editor when selected note changes
  useEffect(() => {
    if (selectedNote) {
      setEditorContent(selectedNote.content)
      setNoteTitle(selectedNote.title)
      setIsCreatingNew(false)
    } else if (selectedNoteId) {
      // Note not found, redirect to notes list
      setSelectedNoteId(null)
      navigate('/notes')
    }
  }, [selectedNote, selectedNoteId, navigate])

  // Handle note selection
  const handleNoteSelect = (noteId: string) => {
    setSelectedNoteId(noteId)
    navigate(`/notes/${noteId}`)
  }

  // Handle creating new note
  const handleCreateNew = () => {
    setSelectedNoteId(null)
    setEditorContent('')
    setNoteTitle('Untitled Note')
    setIsCreatingNew(true)
    navigate('/notes')
  }

  // Handle saving note
  const handleSave = useCallback(async () => {
    if (!noteTitle.trim()) {
      toast.error('Please enter a note title')
      return
    }

    try {
      if (isCreatingNew) {
        const result = await createNoteMutation.mutateAsync({
          title: noteTitle,
          content: editorContent,
        })
        setSelectedNoteId(result.id)
        setIsCreatingNew(false)
        navigate(`/notes/${result.id}`)
        toast.success('Note created successfully')
      } else if (selectedNoteId) {
        await updateNoteMutation.mutateAsync({
          id: selectedNoteId,
          data: {
            title: noteTitle,
            content: editorContent,
          }
        })
        toast.success('Note saved successfully')
      }
    } catch (error) {
      toast.error('Failed to save note')
      console.error('Save error:', error)
    }
  }, [noteTitle, isCreatingNew, editorContent, createNoteMutation, selectedNoteId, updateNoteMutation, navigate])

  return (
    <div className="flex h-full">
      {/* Notes List Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Notes</h2>
            <Button size="sm" onClick={handleCreateNew}>
              <Plus className="w-4 h-4 mr-1" />
              New
            </Button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Notes List */}
        <div className="flex-1 overflow-y-auto">
          {filteredNotes.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              {searchQuery ? 'No notes found' : 'No notes yet'}
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filteredNotes.map((note) => (
                <Card
                  key={note.id}
                  className={`cursor-pointer transition-colors hover:bg-accent ${
                    selectedNoteId === note.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleNoteSelect(note.id)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium text-sm truncate">{note.title}</h3>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {note.content || 'No content'}
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {new Date(note.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex flex-col">
        {selectedNoteId || isCreatingNew ? (
          <>
            {/* Note Header */}
            <div className="p-4 border-b bg-card">
              <Input
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                placeholder="Note title..."
                className="text-lg font-semibold border-0 focus:ring-0 px-0"
              />
            </div>

            {/* Markdown Editor */}
            <div className="flex-1">
              <MarkdownEditor
                content={editorContent}
                onChange={setEditorContent}
                onSave={handleSave}
                placeholder="Start writing your note..."
                autoSave={true}
                autoSaveDelay={2000}
              />
            </div>
          </>
        ) : (
          /* Welcome State */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Welcome to Notes</h3>
              <p className="text-muted-foreground mb-4">
                Select a note from the sidebar or create a new one to get started
              </p>
              <Button onClick={handleCreateNew}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Note
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}