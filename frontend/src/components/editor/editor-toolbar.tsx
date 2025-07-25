import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { 
  Bold, 
  Italic, 
  Strikethrough, 
  Code, 
  Link, 
  List, 
  ListOrdered,
  Quote,
  Heading1,
  Heading2,
  Heading3,
  Eye,
  EyeOff,
  Save
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface EditorToolbarProps {
  onFormat: {
    bold: () => void
    italic: () => void
    strikethrough: () => void
    code: () => void
    link: () => void
    unorderedList: () => void
    orderedList: () => void
    quote: () => void
    heading1: () => void
    heading2: () => void
    heading3: () => void
  }
  onTogglePreview: () => void
  showPreview: boolean
  onSave?: () => void
  className?: string
}

export function EditorToolbar({
  onFormat,
  onTogglePreview,
  showPreview,
  onSave,
  className
}: EditorToolbarProps) {
  const toolbarButtons = [
    // Text formatting
    {
      icon: Bold,
      onClick: onFormat.bold,
      tooltip: 'Bold (Ctrl+B)',
      group: 'format'
    },
    {
      icon: Italic,
      onClick: onFormat.italic,
      tooltip: 'Italic (Ctrl+I)',
      group: 'format'
    },
    {
      icon: Strikethrough,
      onClick: onFormat.strikethrough,
      tooltip: 'Strikethrough',
      group: 'format'
    },
    {
      icon: Code,
      onClick: onFormat.code,
      tooltip: 'Inline Code',
      group: 'format'
    },
    
    // Headings
    {
      icon: Heading1,
      onClick: onFormat.heading1,
      tooltip: 'Heading 1',
      group: 'heading'
    },
    {
      icon: Heading2,
      onClick: onFormat.heading2,
      tooltip: 'Heading 2',
      group: 'heading'
    },
    {
      icon: Heading3,
      onClick: onFormat.heading3,
      tooltip: 'Heading 3',
      group: 'heading'
    },
    
    // Lists and blocks
    {
      icon: List,
      onClick: onFormat.unorderedList,
      tooltip: 'Bullet List',
      group: 'list'
    },
    {
      icon: ListOrdered,
      onClick: onFormat.orderedList,
      tooltip: 'Numbered List',
      group: 'list'
    },
    {
      icon: Quote,
      onClick: onFormat.quote,
      tooltip: 'Quote',
      group: 'list'
    },
    
    // Links and media
    {
      icon: Link,
      onClick: onFormat.link,
      tooltip: 'Link (Ctrl+K)',
      group: 'media'
    }
  ]

  const renderButtonGroup = (groupName: string) => {
    const groupButtons = toolbarButtons.filter(btn => btn.group === groupName)
    
    return (
      <div className="flex items-center">
        {groupButtons.map((button, index) => (
          <Button
            key={index}
            variant="ghost"
            size="sm"
            onClick={button.onClick}
            className="h-8 w-8 p-0"
            title={button.tooltip}
          >
            <button.icon className="h-4 w-4" />
          </Button>
        ))}
      </div>
    )
  }

  return (
    <div className={cn(
      'flex items-center gap-1 px-3 py-2 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
      className
    )}>
      {/* Text Formatting */}
      {renderButtonGroup('format')}
      
      <Separator orientation="vertical" className="h-6 mx-1" />
      
      {/* Headings */}
      {renderButtonGroup('heading')}
      
      <Separator orientation="vertical" className="h-6 mx-1" />
      
      {/* Lists and Blocks */}
      {renderButtonGroup('list')}
      
      <Separator orientation="vertical" className="h-6 mx-1" />
      
      {/* Links and Media */}
      {renderButtonGroup('media')}
      
      <div className="flex-1" />
      
      {/* Right side actions */}
      <div className="flex items-center gap-1">
        {/* Preview Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onTogglePreview}
          className="h-8 w-8 p-0"
          title={showPreview ? 'Hide Preview' : 'Show Preview'}
        >
          {showPreview ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </Button>
        
        {onSave && (
          <>
            <Separator orientation="vertical" className="h-6 mx-1" />
            
            {/* Save Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onSave}
              className="h-8 px-3"
              title="Save (Ctrl+S)"
            >
              <Save className="h-4 w-4 mr-1" />
              Save
            </Button>
          </>
        )}
      </div>
    </div>
  )
}