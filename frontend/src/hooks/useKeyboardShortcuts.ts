import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  action: () => void
  description: string
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate()

  const shortcuts: KeyboardShortcut[] = useMemo(() => [
    {
      key: 'k',
      ctrlKey: true,
      action: () => navigate('/search'),
      description: 'Open search'
    },
    {
      key: 'n',
      ctrlKey: true,
      action: () => navigate('/notes'),
      description: 'Create new note'
    },
    {
      key: 'g',
      ctrlKey: true,
      action: () => navigate('/graph'),
      description: 'Open knowledge graph'
    },
    {
      key: 'h',
      ctrlKey: true,
      action: () => navigate('/'),
      description: 'Go to home'
    },
    {
      key: 'd',
      ctrlKey: true,
      action: () => navigate('/documents'),
      description: 'Open documents'
    },
    {
      key: '/',
      action: () => {
        const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement
        if (searchInput) {
          searchInput.focus()
        }
      },
      description: 'Focus search input'
    }
  ], [navigate])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs or textareas
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true'
      ) {
        // Allow Ctrl+K even in inputs for global search
        if (!(event.ctrlKey && event.key === 'k')) {
          return
        }
      }

      const shortcut = shortcuts.find(s => 
        s.key === event.key.toLowerCase() &&
        !!s.ctrlKey === event.ctrlKey &&
        !!s.shiftKey === event.shiftKey &&
        !!s.altKey === event.altKey
      )

      if (shortcut) {
        event.preventDefault()
        shortcut.action()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])

  return { shortcuts }
}