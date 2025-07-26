import api from './api'

export interface Note {
  id: string
  title: string
  content: string
  created_at: string
  updated_at: string
  tags?: string[]
  links?: string[]
  backlinks?: string[]
}

export interface CreateNoteRequest {
  title: string
  content: string
  tags?: string[]
}

export interface UpdateNoteRequest {
  title?: string
  content?: string
  tags?: string[]
}

// Development mode flag - set to true to use mock data
const USE_MOCK_DATA = false

export const notesService = {
  // Get all notes
  async getNotes(): Promise<Note[]> {
    if (USE_MOCK_DATA) {
      const { mockNotes } = await import('./mock-data')
      return new Promise(resolve => setTimeout(() => resolve(mockNotes), 400))
    }
    const response = await api.get('/notes')
    // Backend returns { notes: Note[], total: number, message: string }
    return response.data.notes || []
  },

  // Get a specific note
  async getNote(id: string): Promise<Note> {
    const response = await api.get(`/notes/${id}`)
    return response.data
  },

  // Create a new note
  async createNote(data: CreateNoteRequest): Promise<Note> {
    const response = await api.post('/notes', data)
    return response.data
  },

  // Update a note
  async updateNote(id: string, data: UpdateNoteRequest): Promise<Note> {
    const response = await api.put(`/notes/${id}`, data)
    return response.data
  },

  // Delete a note
  async deleteNote(id: string): Promise<void> {
    await api.delete(`/notes/${id}`)
  },

  // Search notes
  async searchNotes(query: string): Promise<Note[]> {
    const response = await api.get('/notes', {
      params: { search: query }
    })
    return response.data
  },
}