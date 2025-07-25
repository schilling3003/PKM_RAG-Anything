import { Routes, Route } from 'react-router-dom'
import { ResponsiveLayout } from './components/layout/responsive-layout'
import { HomePage } from './pages/home'
import { NotesPage } from './pages/notes'
import { DocumentsPage } from './pages/documents'
import { PDFViewerPage } from './pages/pdf-viewer'
import { SearchPage } from './pages/search'
import { GraphPage } from './pages/graph'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ResponsiveLayout />}>
        <Route index element={<HomePage />} />
        <Route path="notes" element={<NotesPage />} />
        <Route path="notes/:noteId" element={<NotesPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:documentId" element={<DocumentsPage />} />
        <Route path="pdf/:documentId" element={<PDFViewerPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="graph" element={<GraphPage />} />
      </Route>
    </Routes>
  )
}