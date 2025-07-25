import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'

export function ResponsiveLayout() {
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Initialize keyboard shortcuts
  useKeyboardShortcuts()

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)

    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  if (isMobile) {
    return (
      <div className="flex h-screen bg-background flex-col">
        {/* Mobile Header with Menu Button */}
        <div className="flex items-center justify-between p-4 border-b bg-card">
          <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm">
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-64">
              <Sidebar />
            </SheetContent>
          </Sheet>
          
          <h1 className="text-lg font-semibold">AI PKM Tool</h1>
          
          <div className="w-10" /> {/* Spacer for centering */}
        </div>

        {/* Mobile Content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    )
  }

  // Desktop layout
  return (
    <div className="flex h-screen bg-background">
      {/* Desktop Sidebar */}
      <Sidebar className="w-64 flex-shrink-0" />
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Desktop Header */}
        <Header />
        
        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}