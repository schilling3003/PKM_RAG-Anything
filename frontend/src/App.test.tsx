import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Routes: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Route: ({ element }: { element: React.ReactNode }) => <div>{element}</div>,
  Outlet: () => <div>Outlet</div>,
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('AI PKM Tool')).toBeInTheDocument()
  })

  it('has proper structure with layout', () => {
    render(<App />)
    expect(screen.getByText('Personal Knowledge Management')).toBeInTheDocument()
  })
})