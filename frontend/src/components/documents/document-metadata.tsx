import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  File, 
  Calendar, 
  HardDrive, 
  Clock, 
  Edit3, 
  Save, 
  X,
  Tag,
  FileText,
  Image,
  Music,
  Video
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { documentsService, Document } from '@/services/documents'
import { toast } from 'sonner'

interface DocumentMetadataProps {
  document: Document
  onUpdate?: (document: Document) => void
}

interface EditableMetadata {
  title?: string
  description?: string
  tags?: string[]
}

export function DocumentMetadata({ document, onUpdate }: DocumentMetadataProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editableData, setEditableData] = useState<EditableMetadata>({
    title: document.metadata?.title || document.filename,
    description: document.metadata?.description || '',
    tags: document.metadata?.tags || []
  })
  const [newTag, setNewTag] = useState('')

  const { data: processingStatus } = useQuery({
    queryKey: ['document-status', document.id],
    queryFn: () => documentsService.getProcessingStatus(document.id),
    enabled: document.processing_status === 'processing',
    refetchInterval: 2000,
  })

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <Image className="w-5 h-5 text-blue-500" />
    if (fileType.startsWith('audio/')) return <Music className="w-5 h-5 text-purple-500" />
    if (fileType.startsWith('video/')) return <Video className="w-5 h-5 text-red-500" />
    if (fileType === 'application/pdf') return <FileText className="w-5 h-5 text-red-600" />
    return <File className="w-5 h-5 text-gray-500" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleSave = async () => {
    try {
      // In a real implementation, you would call an API to update the document metadata
      // For now, we'll just simulate the update
      const updatedDocument = {
        ...document,
        metadata: {
          ...document.metadata,
          ...editableData
        }
      }
      
      toast.success('Document metadata updated successfully')
      onUpdate?.(updatedDocument)
      setIsEditing(false)
    } catch (error) {
      toast.error('Failed to update document metadata')
    }
  }

  const handleCancel = () => {
    setEditableData({
      title: document.metadata?.title || document.filename,
      description: document.metadata?.description || '',
      tags: document.metadata?.tags || []
    })
    setIsEditing(false)
  }

  const addTag = () => {
    if (newTag.trim() && !editableData.tags?.includes(newTag.trim())) {
      setEditableData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), newTag.trim()]
      }))
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setEditableData(prev => ({
      ...prev,
      tags: prev.tags?.filter(tag => tag !== tagToRemove) || []
    }))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      addTag()
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {getFileIcon(document.file_type)}
            Document Details
          </CardTitle>
          {!isEditing ? (
            <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
              <Edit3 className="w-4 h-4 mr-2" />
              Edit
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                Save
              </Button>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Title</label>
            {isEditing ? (
              <Input
                value={editableData.title}
                onChange={(e) => setEditableData(prev => ({ ...prev, title: e.target.value }))}
                className="mt-1"
              />
            ) : (
              <p className="mt-1 font-medium">{editableData.title}</p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">Description</label>
            {isEditing ? (
              <Textarea
                value={editableData.description}
                onChange={(e) => setEditableData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Add a description..."
                className="mt-1"
                rows={3}
              />
            ) : (
              <p className="mt-1 text-sm">
                {editableData.description || (
                  <span className="text-muted-foreground italic">No description</span>
                )}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">Tags</label>
            <div className="mt-2 space-y-2">
              <div className="flex flex-wrap gap-2">
                {editableData.tags?.map((tag) => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    {tag}
                    {isEditing && (
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </Badge>
                ))}
                {(!editableData.tags || editableData.tags.length === 0) && !isEditing && (
                  <span className="text-sm text-muted-foreground italic">No tags</span>
                )}
              </div>
              
              {isEditing && (
                <div className="flex gap-2">
                  <Input
                    placeholder="Add a tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1"
                  />
                  <Button variant="outline" size="sm" onClick={addTag}>
                    Add
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        <Separator />

        {/* File Information */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <File className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Filename:</span>
            <span className="font-medium">{document.filename}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Size:</span>
            <span className="font-medium">{formatFileSize(document.file_size || 0)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Created:</span>
            <span className="font-medium">{formatDate(document.created_at)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Modified:</span>
            <span className="font-medium">{formatDate(document.updated_at)}</span>
          </div>
        </div>

        <Separator />

        {/* Processing Status */}
        <div className="space-y-3">
          <h4 className="font-medium">Processing Status</h4>
          
          <div className="flex items-center gap-2">
            <Badge 
              variant={
                document.processing_status === 'completed' ? 'success' :
                document.processing_status === 'failed' ? 'destructive' :
                document.processing_status === 'processing' ? 'default' : 'secondary'
              }
            >
              {document.processing_status}
            </Badge>
            
            {document.processing_status === 'processing' && processingStatus?.progress && (
              <span className="text-sm text-muted-foreground">
                {processingStatus.progress}%
              </span>
            )}
          </div>

          {document.processing_status === 'processing' && processingStatus?.current_step && (
            <p className="text-sm text-muted-foreground">
              Current step: {processingStatus.current_step}
            </p>
          )}

          {document.processing_status === 'failed' && document.error_message && (
            <p className="text-sm text-destructive">
              Error: {document.error_message}
            </p>
          )}

          {document.processing_status === 'completed' && document.extracted_text && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Extracted {document.extracted_text.length} characters of text
              </p>
              {document.metadata?.images_count && (
                <p className="text-sm text-muted-foreground">
                  Found {document.metadata.images_count} images
                </p>
              )}
              {document.metadata?.tables_count && (
                <p className="text-sm text-muted-foreground">
                  Found {document.metadata.tables_count} tables
                </p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}