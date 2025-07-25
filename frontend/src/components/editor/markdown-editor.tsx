import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { ResizablePanels } from '@/components/layout/resizable-panels'
import { MarkdownPreview } from './markdown-preview'
import { EditorToolbar } from './editor-toolbar'
import { useDebounce } from '@/hooks/useDebounce'
import { cn } from '@/lib/utils'

interface MarkdownEditorProps {
  content: string
  onChange: (content: string) => void
  onSave?: () => void
  placeholder?: string
  className?: string
  autoSave?: boolean
  autoSaveDelay?: number
}

export function MarkdownEditor({
  content,
  onChange,
  onSave,
  placeholder = "Start writing your note...",
  className,
  autoSave = true,
  autoSaveDelay = 2000
}: MarkdownEditorProps) {
  const [showPreview, setShowPreview] = useState(true)
  const [isEditorFocused, setIsEditorFocused] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // Debounced content for auto-save
  const debouncedContent = useDebounce(content, autoSaveDelay)
  
  // Auto-save effect
  useEffect(() => {
    if (autoSave && debouncedContent && onSave) {
      onSave()
    }
  }, [debouncedContent, autoSave, onSave])

  const insertText = useCallback((before: string, after: string = '', placeholder: string = '') => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = content.substring(start, end)
    const textToInsert = selectedText || placeholder
    
    const newContent = 
      content.substring(0, start) + 
      before + textToInsert + after + 
      content.substring(end)
    
    onChange(newContent)
    
    // Set cursor position after insertion
    setTimeout(() => {
      const newCursorPos = start + before.length + textToInsert.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
      textarea.focus()
    }, 0)
  }, [content, onChange])

  const insertAtLineStart = useCallback((prefix: string) => {
    const textarea = textareaRef.current
    if (!textarea) return

    const start = textarea.selectionStart
    const lines = content.split('\n')
    let currentPos = 0
    let lineIndex = 0
    
    // Find which line the cursor is on
    for (let i = 0; i < lines.length; i++) {
      if (currentPos + lines[i].length >= start) {
        lineIndex = i
        break
      }
      currentPos += lines[i].length + 1 // +1 for newline
    }
    
    // Insert prefix at the beginning of the line
    lines[lineIndex] = prefix + lines[lineIndex]
    const newContent = lines.join('\n')
    onChange(newContent)
    
    // Update cursor position
    setTimeout(() => {
      const newCursorPos = start + prefix.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
      textarea.focus()
    }, 0)
  }, [content, onChange])

  const formatActions = useMemo(() => ({
    bold: () => insertText('**', '**', 'bold text'),
    italic: () => insertText('*', '*', 'italic text'),
    strikethrough: () => insertText('~~', '~~', 'strikethrough text'),
    code: () => insertText('`', '`', 'code'),
    link: () => insertText('[', '](url)', 'link text'),
    unorderedList: () => insertAtLineStart('- '),
    orderedList: () => insertAtLineStart('1. '),
    quote: () => insertAtLineStart('> '),
    heading1: () => insertAtLineStart('# '),
    heading2: () => insertAtLineStart('## '),
    heading3: () => insertAtLineStart('### '),
  }), [insertText, insertAtLineStart])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Handle keyboard shortcuts
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'b':
          e.preventDefault()
          formatActions.bold()
          break
        case 'i':
          e.preventDefault()
          formatActions.italic()
          break
        case 'k':
          e.preventDefault()
          formatActions.link()
          break
        case 's':
          e.preventDefault()
          onSave?.()
          break
      }
    }
    
    // Handle tab for indentation
    if (e.key === 'Tab') {
      e.preventDefault()
      insertText('  ')
    }
  }, [formatActions, onSave, insertText])

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Toolbar */}
      <EditorToolbar
        onFormat={formatActions}
        onTogglePreview={() => setShowPreview(!showPreview)}
        showPreview={showPreview}
        onSave={onSave}
      />
      
      {/* Editor Content */}
      <div className="flex-1 min-h-0">
        {showPreview ? (
          <ResizablePanels defaultSizes={[50, 50]} minSizes={[30, 30]}>
            {/* Editor Pane */}
            <div className="flex flex-col h-full">
              <div className="flex-1 relative">
                <Textarea
                  ref={textareaRef}
                  value={content}
                  onChange={(e) => onChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => setIsEditorFocused(true)}
                  onBlur={() => setIsEditorFocused(false)}
                  placeholder={placeholder}
                  className={cn(
                    'h-full resize-none border-0 focus:ring-0 font-mono text-sm',
                    'scrollbar-thin scrollbar-thumb-muted-foreground/30 scrollbar-track-transparent',
                    isEditorFocused && 'ring-2 ring-ring ring-offset-2'
                  )}
                  style={{ minHeight: '100%' }}
                />
              </div>
            </div>
            
            {/* Preview Pane */}
            <div className="h-full border-l">
              <MarkdownPreview content={content} />
            </div>
          </ResizablePanels>
        ) : (
          /* Editor Only */
          <div className="h-full">
            <Textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsEditorFocused(true)}
              onBlur={() => setIsEditorFocused(false)}
              placeholder={placeholder}
              className={cn(
                'h-full resize-none border-0 focus:ring-0 font-mono text-sm',
                'scrollbar-thin scrollbar-thumb-muted-foreground/30 scrollbar-track-transparent',
                isEditorFocused && 'ring-2 ring-ring ring-offset-2'
              )}
            />
          </div>
        )}
      </div>
      
      {/* Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/50 text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>{content.length} characters</span>
          <span>{content.split('\n').length} lines</span>
          <span>{content.split(/\s+/).filter(word => word.length > 0).length} words</span>
        </div>
        <div className="flex items-center gap-2">
          {autoSave && (
            <span className="text-green-600">Auto-save enabled</span>
          )}
          <span>Markdown</span>
        </div>
      </div>
    </div>
  )
}