import { useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'
import 'katex/dist/katex.min.css'

interface MarkdownPreviewProps {
  content: string
  className?: string
}

export function MarkdownPreview({ content, className }: MarkdownPreviewProps) {
  const { theme } = useTheme()
  
  const processedContent = useMemo(() => {
    // Process wiki-style links [[link]] -> [link](link)
    return content.replace(/\[\[([^\]]+)\]\]/g, '[$1]($1)')
  }, [content])

  const components = useMemo(() => ({
    code({ inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : ''
      
      if (!inline && language) {
        return (
          <SyntaxHighlighter
            style={theme === 'dark' ? oneDark : oneLight}
            language={language}
            PreTag="div"
            className="rounded-md"
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        )
      }
      
      return (
        <code 
          className={cn(
            'relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold',
            className
          )} 
          {...props}
        >
          {children}
        </code>
      )
    },
    
    blockquote({ children, ...props }: any) {
      return (
        <blockquote 
          className="mt-6 border-l-2 border-primary pl-6 italic text-muted-foreground"
          {...props}
        >
          {children}
        </blockquote>
      )
    },
    
    table({ children, ...props }: any) {
      return (
        <div className="my-6 w-full overflow-y-auto">
          <table className="w-full border-collapse border border-border" {...props}>
            {children}
          </table>
        </div>
      )
    },
    
    th({ children, ...props }: any) {
      return (
        <th 
          className="border border-border px-4 py-2 text-left font-bold bg-muted"
          {...props}
        >
          {children}
        </th>
      )
    },
    
    td({ children, ...props }: any) {
      return (
        <td className="border border-border px-4 py-2" {...props}>
          {children}
        </td>
      )
    },
    
    h1({ children, ...props }: any) {
      return (
        <h1 
          className="mt-8 mb-4 text-3xl font-bold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h1>
      )
    },
    
    h2({ children, ...props }: any) {
      return (
        <h2 
          className="mt-6 mb-3 text-2xl font-semibold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h2>
      )
    },
    
    h3({ children, ...props }: any) {
      return (
        <h3 
          className="mt-6 mb-2 text-xl font-semibold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h3>
      )
    },
    
    h4({ children, ...props }: any) {
      return (
        <h4 
          className="mt-4 mb-2 text-lg font-semibold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h4>
      )
    },
    
    h5({ children, ...props }: any) {
      return (
        <h5 
          className="mt-4 mb-2 text-base font-semibold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h5>
      )
    },
    
    h6({ children, ...props }: any) {
      return (
        <h6 
          className="mt-4 mb-2 text-sm font-semibold tracking-tight first:mt-0"
          {...props}
        >
          {children}
        </h6>
      )
    },
    
    p({ children, ...props }: any) {
      return (
        <p className="leading-7 [&:not(:first-child)]:mt-4" {...props}>
          {children}
        </p>
      )
    },
    
    ul({ children, ...props }: any) {
      return (
        <ul className="my-4 ml-6 list-disc [&>li]:mt-2" {...props}>
          {children}
        </ul>
      )
    },
    
    ol({ children, ...props }: any) {
      return (
        <ol className="my-4 ml-6 list-decimal [&>li]:mt-2" {...props}>
          {children}
        </ol>
      )
    },
    
    li({ children, ...props }: any) {
      return (
        <li className="leading-7" {...props}>
          {children}
        </li>
      )
    },
    
    a({ children, href, ...props }: any) {
      const isWikiLink = href && !href.startsWith('http') && !href.startsWith('#')
      
      return (
        <a 
          href={href}
          className={cn(
            'font-medium underline underline-offset-4 hover:no-underline',
            isWikiLink ? 'text-primary' : 'text-blue-600 dark:text-blue-400'
          )}
          target={href?.startsWith('http') ? '_blank' : undefined}
          rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
          {...props}
        >
          {children}
        </a>
      )
    },
    
    hr({ ...props }: any) {
      return <hr className="my-8 border-border" {...props} />
    },
    
    img({ src, alt, ...props }: any) {
      return (
        <img 
          src={src} 
          alt={alt}
          className="max-w-full h-auto rounded-lg border border-border my-4"
          {...props}
        />
      )
    }
  }), [theme])

  if (!content.trim()) {
    return (
      <div className={cn('h-full flex items-center justify-center', className)}>
        <div className="text-center text-muted-foreground">
          <p className="text-lg mb-2">Preview</p>
          <p className="text-sm">Start typing to see your markdown rendered here</p>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className={cn('h-full', className)}>
      <div className="p-6">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={components}
          className="prose prose-sm max-w-none dark:prose-invert"
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    </ScrollArea>
  )
}