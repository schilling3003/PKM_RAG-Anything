import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MarkdownEditor } from './markdown-editor'

// Mock the hooks
vi.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: string) => value,
}))

vi.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'light' }),
}))

describe('MarkdownEditor', () => {
  it('renders with placeholder text', () => {
    const mockOnChange = vi.fn()
    
    render(
      <MarkdownEditor
        content=""
        onChange={mockOnChange}
        placeholder="Test placeholder"
      />
    )
    
    expect(screen.getByPlaceholderText('Test placeholder')).toBeInTheDocument()
  })

  it('calls onChange when content is typed', () => {
    const mockOnChange = vi.fn()
    
    render(
      <MarkdownEditor
        content=""
        onChange={mockOnChange}
        placeholder="Test placeholder"
      />
    )
    
    const textarea = screen.getByPlaceholderText('Test placeholder')
    fireEvent.change(textarea, { target: { value: 'Hello world' } })
    
    expect(mockOnChange).toHaveBeenCalledWith('Hello world')
  })

  it('displays content correctly', () => {
    const mockOnChange = vi.fn()
    
    render(
      <MarkdownEditor
        content="# Hello World"
        onChange={mockOnChange}
      />
    )
    
    const textarea = screen.getByDisplayValue('# Hello World')
    expect(textarea).toBeInTheDocument()
  })

  it('shows status bar with markdown indicator', () => {
    const mockOnChange = vi.fn()
    
    render(
      <MarkdownEditor
        content="Hello world test"
        onChange={mockOnChange}
      />
    )
    
    expect(screen.getByText('Markdown')).toBeInTheDocument()
  })

  it('calls onSave when save button is clicked', () => {
    const mockOnChange = vi.fn()
    const mockOnSave = vi.fn()
    
    render(
      <MarkdownEditor
        content="Test content"
        onChange={mockOnChange}
        onSave={mockOnSave}
      />
    )
    
    const saveButton = screen.getByTitle('Save (Ctrl+S)')
    fireEvent.click(saveButton)
    
    expect(mockOnSave).toHaveBeenCalled()
  })
})