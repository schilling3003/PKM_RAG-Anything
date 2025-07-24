import { Outlet } from 'react-router-dom'

export function MainLayout() {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar will be implemented in task 7.2 */}
      <div className="w-64 border-r bg-card">
        <div className="p-4">
          <h1 className="text-lg font-semibold">AI PKM Tool</h1>
        </div>
      </div>
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Header will be implemented in task 7.2 */}
        <header className="border-b bg-card px-6 py-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-muted-foreground">
              Personal Knowledge Management
            </h2>
          </div>
        </header>
        
        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}