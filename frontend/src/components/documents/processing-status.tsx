import { } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Clock, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  FileText,
  Image,
  Music,
  Video,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { documentsService, Document } from '@/services/documents'
import { toast } from 'sonner'

interface ProcessingStatusProps {
  document: Document
  onRetry?: () => void
}

const PROCESSING_STEPS = [
  { key: 'upload', label: 'File Upload', icon: FileText },
  { key: 'parsing', label: 'Document Parsing', icon: FileText },
  { key: 'extraction', label: 'Content Extraction', icon: Zap },
  { key: 'multimodal', label: 'Multimodal Processing', icon: Image },
  { key: 'embeddings', label: 'Generating Embeddings', icon: Zap },
  { key: 'graph', label: 'Knowledge Graph Update', icon: Zap },
  { key: 'complete', label: 'Processing Complete', icon: CheckCircle }
]

export function ProcessingStatusIndicator({ document, onRetry }: ProcessingStatusProps) {
  const { data: status } = useQuery({
    queryKey: ['processing-status', document.id],
    queryFn: () => documentsService.getProcessingStatus(document.id),
    enabled: document.processing_status === 'processing' || document.processing_status === 'queued',
    refetchInterval: 1000, // Poll every second for real-time updates
  })



  const getStatusColor = (processingStatus: Document['processing_status']) => {
    switch (processingStatus) {
      case 'queued': return 'secondary'
      case 'processing': return 'default'
      case 'completed': return 'success'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const getCurrentStepIndex = (currentStep?: string) => {
    if (!currentStep) return 0
    const stepIndex = PROCESSING_STEPS.findIndex(step => 
      currentStep.toLowerCase().includes(step.key)
    )
    return stepIndex >= 0 ? stepIndex : 0
  }

  const getFileTypeIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <Image className="w-4 h-4" />
    if (fileType.startsWith('audio/')) return <Music className="w-4 h-4" />
    if (fileType.startsWith('video/')) return <Video className="w-4 h-4" />
    return <FileText className="w-4 h-4" />
  }

  const handleRetry = async () => {
    try {
      // In a real implementation, you would call an API to retry processing
      toast.success('Processing retry initiated')
      onRetry?.()
    } catch (error) {
      toast.error('Failed to retry processing')
    }
  }

  if (document.processing_status === 'completed') {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <div className="flex-1">
              <p className="font-medium text-green-800">Processing Complete</p>
              <p className="text-sm text-green-600">
                Document "{document.filename}" has been successfully processed
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (document.processing_status === 'failed') {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <XCircle className="w-5 h-5 text-red-500" />
            <div className="flex-1">
              <p className="font-medium text-red-800">Processing Failed</p>
              <p className="text-sm text-red-600">
                {document.error_message || 'An error occurred during processing'}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {getFileTypeIcon(document.file_type)}
          Processing Status
          <Badge variant={getStatusColor(document.processing_status) as any}>
            {document.processing_status}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{document.filename}</span>
            <span className="text-muted-foreground">
              {status?.progress || 0}%
            </span>
          </div>
          <Progress value={status?.progress || 0} className="h-2" />
        </div>

        {/* Current Step */}
        {status?.current_step && (
          <div className="flex items-center gap-2 text-sm">
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            <span className="text-muted-foreground">Current step:</span>
            <span className="font-medium">{status.current_step}</span>
          </div>
        )}

        {/* Processing Steps */}
        {document.processing_status === 'processing' && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Processing Steps</h4>
            <div className="space-y-1">
              {PROCESSING_STEPS.map((step, index) => {
                const currentStepIndex = getCurrentStepIndex(status?.current_step)
                const isCompleted = index < currentStepIndex
                const isCurrent = index === currentStepIndex
                // const isPending = index > currentStepIndex

                const StepIcon = step.icon

                return (
                  <div
                    key={step.key}
                    className={`flex items-center gap-2 text-sm p-2 rounded ${
                      isCompleted ? 'text-green-600 bg-green-50' :
                      isCurrent ? 'text-blue-600 bg-blue-50' :
                      'text-muted-foreground'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    ) : (
                      <StepIcon className="w-4 h-4" />
                    )}
                    <span>{step.label}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Queued Status */}
        {document.processing_status === 'queued' && (
          <div className="flex items-center gap-2 p-3 bg-yellow-50 rounded-lg">
            <Clock className="w-5 h-5 text-yellow-500" />
            <div>
              <p className="font-medium text-yellow-800">Queued for Processing</p>
              <p className="text-sm text-yellow-600">
                Your document is in the processing queue and will be handled shortly
              </p>
            </div>
          </div>
        )}

        {/* Processing Time Estimate */}
        {(document.processing_status === 'processing' || document.processing_status === 'queued') && (
          <div className="text-xs text-muted-foreground p-2 bg-muted/50 rounded">
            <div className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              <span>
                Processing time varies based on document size and complexity. 
                Large documents may take several minutes.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}