import { useState, useRef, useEffect, ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface ResizablePanelsProps {
  children: [ReactNode, ReactNode]
  defaultSizes?: [number, number]
  minSizes?: [number, number]
  direction?: 'horizontal' | 'vertical'
  className?: string
}

export function ResizablePanels({
  children,
  defaultSizes = [50, 50],
  minSizes = [20, 20],
  direction = 'horizontal',
  className
}: ResizablePanelsProps) {
  const [sizes, setSizes] = useState(defaultSizes)
  const [isResizing, setIsResizing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const resizerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return

      const container = containerRef.current
      const containerRect = container.getBoundingClientRect()
      
      let percentage: number
      
      if (direction === 'horizontal') {
        const x = e.clientX - containerRect.left
        percentage = (x / containerRect.width) * 100
      } else {
        const y = e.clientY - containerRect.top
        percentage = (y / containerRect.height) * 100
      }

      // Clamp to min/max sizes
      const clampedPercentage = Math.max(
        minSizes[0],
        Math.min(100 - minSizes[1], percentage)
      )

      setSizes([clampedPercentage, 100 - clampedPercentage])
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing, direction, minSizes])

  const isHorizontal = direction === 'horizontal'

  return (
    <div
      ref={containerRef}
      className={cn(
        'flex h-full w-full',
        isHorizontal ? 'flex-row' : 'flex-col',
        className
      )}
    >
      {/* First panel */}
      <div
        style={{
          [isHorizontal ? 'width' : 'height']: `${sizes[0]}%`,
        }}
        className="overflow-hidden"
      >
        {children[0]}
      </div>

      {/* Resizer */}
      <div
        ref={resizerRef}
        className={cn(
          'bg-border hover:bg-border/80 transition-colors',
          isHorizontal 
            ? 'w-1 cursor-col-resize hover:w-2' 
            : 'h-1 cursor-row-resize hover:h-2',
          isResizing && 'bg-primary'
        )}
        onMouseDown={handleMouseDown}
      />

      {/* Second panel */}
      <div
        style={{
          [isHorizontal ? 'width' : 'height']: `${sizes[1]}%`,
        }}
        className="overflow-hidden"
      >
        {children[1]}
      </div>
    </div>
  )
}