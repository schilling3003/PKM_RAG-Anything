import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsService } from '@/services/documents'
import { toast } from 'sonner'

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: documentsService.getDocuments,
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsService.getDocument(id),
    enabled: !!id,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => documentsService.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document uploaded and queued for processing')
    },
    onError: (error) => {
      console.error('Failed to upload document:', error)
      toast.error('Failed to upload document')
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => documentsService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document deleted successfully')
    },
    onError: (error) => {
      console.error('Failed to delete document:', error)
      toast.error('Failed to delete document')
    },
  })
}

export function useProcessingStatus(documentId: string) {
  return useQuery({
    queryKey: ['documents', documentId, 'status'],
    queryFn: () => documentsService.getProcessingStatus(documentId),
    enabled: !!documentId,
    refetchInterval: (query) => {
      // Refetch every 2 seconds if still processing
      const data = query.state.data
      return data?.status === 'processing' || data?.status === 'queued' ? 2000 : false
    },
  })
}