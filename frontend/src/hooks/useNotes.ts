import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notesService, type CreateNoteRequest, type UpdateNoteRequest } from '@/services/notes'
import { toast } from 'sonner'

export function useNotes() {
  return useQuery({
    queryKey: ['notes'],
    queryFn: notesService.getNotes,
  })
}

export function useNote(id: string) {
  return useQuery({
    queryKey: ['notes', id],
    queryFn: () => notesService.getNote(id),
    enabled: !!id,
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateNoteRequest) => notesService.createNote(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      toast.success('Note created successfully')
    },
    onError: (error) => {
      console.error('Failed to create note:', error)
      toast.error('Failed to create note')
    },
  })
}

export function useUpdateNote() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNoteRequest }) =>
      notesService.updateNote(id, data),
    onSuccess: (updatedNote) => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      queryClient.invalidateQueries({ queryKey: ['notes', updatedNote.id] })
      toast.success('Note updated successfully')
    },
    onError: (error) => {
      console.error('Failed to update note:', error)
      toast.error('Failed to update note')
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => notesService.deleteNote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      toast.success('Note deleted successfully')
    },
    onError: (error) => {
      console.error('Failed to delete note:', error)
      toast.error('Failed to delete note')
    },
  })
}

export function useSearchNotes(query: string) {
  return useQuery({
    queryKey: ['notes', 'search', query],
    queryFn: () => notesService.searchNotes(query),
    enabled: query.length > 0,
  })
}