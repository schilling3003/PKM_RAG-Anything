import { useEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // Get theme from localStorage or default to system
    const stored = localStorage.getItem('theme') as Theme
    return stored || 'system'
  })

  useEffect(() => {
    const root = window.document.documentElement

    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'

      root.classList.add(systemTheme)
      return
    }

    root.classList.add(theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem('theme', theme)
  }, [theme])

  return {
    theme,
    setTheme,
  }
}