# PDF Viewer Documentation

The AI PKM Tool includes a comprehensive PDF viewer with advanced features for document navigation, search, and annotation.

## Features

### Navigation
- **Page Navigation**: Navigate through pages using arrow buttons or direct page input
- **Zoom Controls**: Zoom in/out with preset levels (50% to 300%)
- **Rotation**: Rotate pages in 90-degree increments
- **Fullscreen Mode**: Toggle fullscreen viewing for distraction-free reading

### Search Functionality
- **Text Search**: Search for text within the PDF document
- **Search Navigation**: Navigate between search results with previous/next buttons
- **Search Highlighting**: Visual highlighting of search results (planned)
- **Result Counter**: Shows current result position and total matches

### Annotation System
- **Note Annotations**: Add sticky note annotations to specific locations
- **Text Annotations**: Add text-based annotations
- **Highlight Annotations**: Highlight text sections with customizable colors
- **Annotation Management**: View, edit, and delete annotations in sidebar
- **Persistent Storage**: Annotations are saved and persist across sessions

### User Interface
- **Responsive Design**: Adapts to different screen sizes
- **Tool Selection**: Switch between selection, note, highlight, and text tools
- **Sidebar**: Collapsible annotations sidebar showing all document annotations
- **Progress Indicators**: Loading states and error handling
- **Keyboard Shortcuts**: Support for common navigation shortcuts

## Usage

### Opening PDFs
1. Navigate to the Documents page
2. Click on a PDF document in the document list
3. Select "View PDF" from the dropdown menu
4. The PDF viewer opens in a new page

### Navigation
- Use the arrow buttons or page input field to navigate
- Scroll through pages in the main viewing area
- Use zoom controls to adjust viewing size
- Click the fullscreen button for immersive viewing

### Searching
1. Enter search terms in the search bar at the top
2. Press Enter or click the Search button
3. Use the navigation arrows to move between results
4. Results counter shows current position

### Adding Annotations
1. Select an annotation tool from the toolbar (note, highlight, or text)
2. Click on the desired location in the PDF
3. Enter annotation content in the dialog
4. Click Save to create the annotation

### Managing Annotations
- View all annotations in the right sidebar
- Click on annotations to navigate to their location
- Delete annotations using the X button
- Annotations are automatically saved

## Technical Implementation

### Dependencies
- **react-pdf**: Core PDF rendering functionality
- **PDF.js**: Underlying PDF processing engine
- **React**: Component framework
- **TypeScript**: Type safety and development experience

### Components
- `PDFViewerPage`: Main page component with routing and error handling
- `PDFViewer`: Core viewer component with all functionality
- Integration with document management system

### API Integration
- Fetches PDF documents via `/api/documents/{id}/pdf` endpoint
- Retrieves document metadata for display
- Saves annotations to backend (planned)

### Performance Considerations
- Lazy loading of PDF pages
- Efficient rendering with react-pdf
- Optimized annotation overlay rendering
- Memory management for large documents

## Configuration

### PDF.js Worker
The viewer uses PDF.js with a CDN-hosted worker for optimal performance:
```javascript
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`
```

### Supported Features
- All standard PDF features supported by PDF.js
- Text extraction for search functionality
- Page rendering with zoom and rotation
- Annotation overlay system

## Future Enhancements

### Planned Features
- **Text Selection**: Select and copy text from PDFs
- **Advanced Search**: Regular expressions and case-sensitive search
- **Annotation Collaboration**: Share annotations with other users
- **Export Annotations**: Export annotations to various formats
- **Thumbnail Navigation**: Page thumbnail sidebar for quick navigation
- **Bookmark Support**: PDF bookmark navigation
- **Form Support**: Interactive PDF form filling

### Performance Improvements
- **Virtualization**: Render only visible pages for large documents
- **Caching**: Cache rendered pages for faster navigation
- **Progressive Loading**: Load pages as needed
- **Background Processing**: Pre-render adjacent pages

## Troubleshooting

### Common Issues

**PDF Not Loading**
- Check if the document exists and is accessible
- Verify PDF file is not corrupted
- Check browser console for error messages

**Search Not Working**
- Ensure PDF contains searchable text (not scanned images)
- Try different search terms
- Check if PDF has text extraction enabled

**Annotations Not Saving**
- Check browser console for API errors
- Verify backend annotation endpoints are working
- Ensure proper authentication if required

**Performance Issues**
- Large PDFs may load slowly
- Consider reducing zoom level for better performance
- Close other browser tabs to free memory

### Browser Compatibility
- Modern browsers with ES6+ support required
- Chrome, Firefox, Safari, and Edge supported
- Mobile browsers supported with responsive design

## API Reference

### Endpoints Used
- `GET /api/documents/{id}` - Get document metadata
- `GET /api/documents/{id}/pdf` - Get PDF file content
- `POST /api/documents/{id}/annotations` - Save annotation (planned)
- `GET /api/documents/{id}/annotations` - Get annotations (planned)
- `DELETE /api/annotations/{id}` - Delete annotation (planned)

### Data Models
```typescript
interface Annotation {
  id: string
  page: number
  x: number
  y: number
  width: number
  height: number
  type: 'note' | 'highlight' | 'text'
  content: string
  color: string
  created_at: string
}

interface SearchResult {
  page: number
  text: string
  position: { x: number; y: number }
}
```