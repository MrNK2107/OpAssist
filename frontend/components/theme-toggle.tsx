'use client'

import { useEffect, useSyncExternalStore } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Theme = 'light' | 'dark'

const listeners = new Set<() => void>()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function getThemeSnapshot(): Theme {
  const stored = localStorage.getItem('theme')
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  return (stored || preferred || 'dark') as Theme
}

function getServerThemeSnapshot(): Theme {
  return 'dark'
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getThemeSnapshot, getServerThemeSnapshot)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
    listeners.forEach((l) => l())
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label="Toggle theme"
      className="relative overflow-hidden"
    >
      <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-amber-500/10 to-orange-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
      {theme === 'dark' ? (
        <Sun className="h-4 w-4 relative z-10 text-amber-400" />
      ) : (
        <Moon className="h-4 w-4 relative z-10 text-slate-700" />
      )}
    </Button>
  )
}
