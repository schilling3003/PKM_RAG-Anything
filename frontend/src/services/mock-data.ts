import { Document } from './documents'

export const mockDocuments: Document[] = [
  {
    id: '1',
    filename: 'sample-document.pdf',
    file_type: 'application/pdf',
    file_size: 2048576, // 2MB
    processing_status: 'completed',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:35:00Z',
    extracted_text: 'This is sample extracted text from the PDF document...',
    metadata: {
      title: 'Sample Document',
      description: 'A sample PDF document for testing',
      tags: ['sample', 'test', 'pdf'],
      pages: 10,
      images_count: 3,
      tables_count: 2
    }
  },
  {
    id: '2',
    filename: 'research-paper.pdf',
    file_type: 'application/pdf',
    file_size: 5242880, // 5MB
    processing_status: 'processing',
    created_at: '2024-01-15T11:00:00Z',
    updated_at: '2024-01-15T11:05:00Z',
    metadata: {
      title: 'Research Paper on AI',
      description: 'Academic research paper about artificial intelligence',
      tags: ['research', 'ai', 'academic']
    }
  },
  {
    id: '3',
    filename: 'meeting-notes.docx',
    file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    file_size: 1024000, // 1MB
    processing_status: 'failed',
    created_at: '2024-01-15T09:15:00Z',
    updated_at: '2024-01-15T09:20:00Z',
    error_message: 'Failed to extract text from document',
    metadata: {
      title: 'Weekly Meeting Notes',
      description: 'Notes from the weekly team meeting',
      tags: ['meeting', 'notes', 'team']
    }
  },
  {
    id: '4',
    filename: 'presentation.pptx',
    file_type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    file_size: 8388608, // 8MB
    processing_status: 'queued',
    created_at: '2024-01-15T12:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
    metadata: {
      title: 'Project Presentation',
      description: 'Quarterly project review presentation',
      tags: ['presentation', 'project', 'quarterly']
    }
  },
  {
    id: '5',
    filename: 'image-analysis.png',
    file_type: 'image/png',
    file_size: 3145728, // 3MB
    processing_status: 'completed',
    created_at: '2024-01-15T08:45:00Z',
    updated_at: '2024-01-15T08:50:00Z',
    extracted_text: 'Text extracted from image using OCR...',
    metadata: {
      title: 'Data Visualization Chart',
      description: 'Chart showing quarterly sales data',
      tags: ['chart', 'sales', 'data']
    }
  }
]

export const mockProcessingStatus = {
  status: 'processing',
  progress: 65,
  current_step: 'Generating embeddings',
  error_message: null
}

export const mockNotes = [
  {
    id: '1',
    title: 'Project Planning',
    content: '# Project Planning\n\nThis is a sample note about project planning...',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    tags: ['planning', 'project']
  },
  {
    id: '2',
    title: 'Research Ideas',
    content: '# Research Ideas\n\nCollection of research ideas and references...',
    created_at: '2024-01-15T11:00:00Z',
    updated_at: '2024-01-15T11:15:00Z',
    tags: ['research', 'ideas']
  }
]