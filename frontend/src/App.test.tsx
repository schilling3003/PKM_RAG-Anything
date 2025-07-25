import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App'

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Routes: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Route: ({ element }: { element: React.ReactNode }) => <div>{element}</div>,
  Outlet: () => <div>Outlet</div>,
  useNavigate: () => vi.fn(),
  useLocation: () => ({ pathname: '/' }),
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
}))

// Mock TanStack Query hooks
vi.mock('@/hooks/useNotes', () => ({
  useNotes: () => ({ data: [] }),
}))

vi.mock('@/hooks/useDocuments', () => ({
  useDocuments: () => ({ data: [] }),
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('AI PKM Tool')).toBeInTheDocument()
  })

  it('has proper structure with layout', () => {
    render(<App />)
    expect(screen.getByText('Knowledge Management')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Search notes and documents...')).toBeInTheDocument()
  })
})