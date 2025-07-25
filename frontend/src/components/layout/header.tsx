import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  Search, 
  Settings, 
  Moon, 
  Sun, 
  MoreHorizontal,
  Command,
  Keyboard,
  HelpCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuShortcut
} from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { useTheme } from '@/hooks/useTheme'

interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const { theme, setTheme } = useTheme()

  // Get page title based on current route
  const getPageTitle = () => {
    const path = location.pathname
    if (path === '/') return 'Home'
    if (path === '/search') return 'Search'
    if (path === '/graph') return 'Knowledge Graph'
    if (path.startsWith('/notes')) return 'Notes'
    if (path.startsWith('/documents')) return 'Documents'
    return 'AI PKM Tool'
  }

  const getPageDescription = () => {
    const path = location.pathname
    if (path === '/') return 'Welcome to your personal knowledge management system'
    if (path === '/search') return 'Search across your notes and documents'
    if (path === '/graph') return 'Explore connections in your knowledge base'
    if (path.startsWith('/notes')) return 'Create and manage your markdown notes'
    if (path.startsWith('/documents')) return 'Upload and process multimodal documents'
    return 'Personal Knowledge Management'
  }

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  const handleKeyboardShortcut = (action: string) => {
    switch (action) {
      case 'search':
        navigate('/search')
        break
      case 'new-note':
        navigate('/notes')
        break
      case 'graph':
        navigate('/graph')
        break
      case 'home':
        navigate('/')
        break
    }
  }

  return (
    <header className={`border-b bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50 ${className}`}>
      <div className="flex items-center justify-between px-6 py-3">
        {/* Left side - Page info */}
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-lg font-semibold">{getPageTitle()}</h1>
            <p className="text-sm text-muted-foreground">{getPageDescription()}</p>
          </div>
        </div>

        {/* Center - Global search */}
        <div className="flex-1 max-w-md mx-8">
          <form onSubmit={handleGlobalSearch} className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search everything... (Ctrl+K)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-20"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <Badge variant="secondary" className="text-xs">
                <Command className="w-3 h-3 mr-1" />
                K
              </Badge>
            </div>
          </form>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Quick search button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/search')}
            className="hidden sm:flex"
          >
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>

          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </Button>

          {/* More actions dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onClick={() => handleKeyboardShortcut('new-note')}>
                <span>New Note</span>
                <DropdownMenuShortcut>Ctrl+N</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleKeyboardShortcut('search')}>
                <span>Search</span>
                <DropdownMenuShortcut>Ctrl+K</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleKeyboardShortcut('graph')}>
                <span>Knowledge Graph</span>
                <DropdownMenuShortcut>Ctrl+G</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Keyboard className="w-4 h-4 mr-2" />
                <span>Keyboard Shortcuts</span>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <HelpCircle className="w-4 h-4 mr-2" />
                <span>Help & Support</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Settings className="w-4 h-4 mr-2" />
                <span>Settings</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}