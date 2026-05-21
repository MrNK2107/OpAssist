'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { X, Rocket } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { navItems } from '@/lib/nav-config'

interface MobileNavProps {
  open: boolean
  onClose: () => void
}

export function MobileNav({ open, onClose }: MobileNavProps) {
  const pathname = usePathname()

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 md:hidden animate-fade-in">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Sidebar */}
      <div className="absolute left-0 top-0 h-full w-64 bg-card/80 backdrop-blur-2xl border-r border-border/50 shadow-2xl animate-slide-in-left">
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <Link href="/" className="flex items-center gap-2" onClick={onClose}>
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center">
              <Rocket className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              OpAssist
            </span>
          </Link>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/15 to-violet-500/15 text-cyan-400 border border-cyan-500/20'
                    : 'text-muted-foreground hover:bg-accent/5 hover:text-foreground'
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
