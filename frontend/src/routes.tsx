import { Routes, Route } from 'react-router-dom'
import { MainLayout } from './components/layout/main-layout'
import { HomePage } from './pages/home'
import { NotesPage } from './pages/notes'
import { DocumentsPage } from './pages/documents'
import { SearchPage } from './pages/search'
import { GraphPage } from './pages/graph'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<HomePage />} />
        <Route path="notes" element={<NotesPage />} />
        <Route path="notes/:noteId" element={<NotesPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:documentId" element={<DocumentsPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="graph" element={<GraphPage />} />
      </Route>
    </Routes>
  )
}