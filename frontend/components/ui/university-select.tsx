'use client'

import { useState, useRef, useEffect } from 'react'
import { Command } from 'cmdk'
import { Search, Check, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { UNIVERSITIES } from '@/lib/universities'

interface UniversitySelectProps {
  value: string
  onChange: (value: string) => void
  className?: string
  placeholder?: string
  required?: boolean
}

export function UniversitySelect({
  value,
  onChange,
  className,
  placeholder = 'Type to search...',
}: UniversitySelectProps) {
  const [search, setSearch] = useState(value)
  const [prevValue, setPrevValue] = useState(value)
  const [open, setOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Keep the input text in sync when the controlled value changes from outside.
  if (value !== prevValue) {
    setPrevValue(value)
    setSearch(value)
  }

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filtered = UNIVERSITIES.filter((uni) =>
    uni.toLowerCase().includes(search.toLowerCase())
  )

  const handleSelect = (uni: string) => {
    onChange(uni)
    setSearch(uni)
    setOpen(false)
    inputRef.current?.blur()
  }

  const handleClear = () => {
    onChange('')
    setSearch('')
    inputRef.current?.focus()
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <Command
        shouldFilter={false}
        onKeyDown={(e) => {
          if (!open) return
          if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelectedIndex((prev) =>
              prev < filtered.length - 1 ? prev + 1 : 0
            )
          } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelectedIndex((prev) =>
              prev > 0 ? prev - 1 : filtered.length - 1
            )
          } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault()
            handleSelect(filtered[selectedIndex])
          } else if (e.key === 'Escape') {
            setOpen(false)
            inputRef.current?.blur()
          }
        }}
      >
        <div
          className={cn(
            'flex h-10 w-full items-center gap-2 rounded-lg border border-input bg-background/50 backdrop-blur-sm px-3 text-sm shadow-sm transition-all duration-200',
            'hover:border-accent/30 focus-within:ring-2 focus-within:ring-ring focus-within:border-ring',
          )}
        >
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Command.Input
            ref={inputRef}
            value={search}
            onValueChange={(v) => {
              setSearch(v)
              setOpen(true)
            }}

            placeholder={placeholder}
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60"
          />
          {value && (
            <button
              type="button"
              onClick={handleClear}
              aria-label="Clear university"
              className="shrink-0 rounded p-0.5 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* List stays mounted (hidden when closed) so the input's aria-controls always resolves */}
        <div
          className={cn(
            'absolute z-50 mt-1 w-full rounded-lg border border-border bg-card shadow-lg animate-fade-in overflow-hidden',
            !open && 'hidden',
          )}
        >
            <Command.List className="max-h-60 overflow-y-auto p-1">
              {!search ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  Start typing to search universities...
                </div>
              ) : filtered.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  No universities found.
                </div>
              ) : (
                filtered.map((uni, i) => (
                  <div
                    key={uni}
                    role="option"
                    aria-selected={i === selectedIndex}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      handleSelect(uni)
                    }}
                    onMouseEnter={() => setSelectedIndex(i)}
                    className={cn(
                      'flex items-center gap-2 rounded-md px-3 py-2 text-sm cursor-pointer transition-colors',
                      i === selectedIndex && 'bg-accent text-accent-foreground',
                    )}
                  >
                    <Check
                      className={cn(
                        'h-4 w-4 shrink-0',
                        value === uni ? 'opacity-100 text-primary' : 'opacity-0',
                      )}
                    />
                    <span className="truncate">{uni}</span>
                  </div>
                ))
              )}
            </Command.List>
        </div>
      </Command>
    </div>
  )
}
