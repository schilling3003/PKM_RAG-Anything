import { Outlet } from 'react-router-dom'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'

export function MainLayout() {
  // Initialize keyboard shortcuts
  useKeyboardShortcuts()

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar className="w-64 flex-shrink-0" />
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header />
        
        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}