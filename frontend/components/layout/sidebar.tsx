'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { navItems } from '@/lib/nav-config'
import { ThemeToggle } from '@/components/theme-toggle'
import { RadarMark, Wordmark } from '@/components/brand/radar-mark'

interface SidebarProps {
  user?: { name: string; university: string; avatar_url?: string } | null
}

export function Sidebar({ user }: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-border/50 bg-card/40 backdrop-blur-xl h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-border/50">
        <Link href="/" className="flex items-center gap-2.5 group">
          <RadarMark className="w-9 h-9" />
          <Wordmark className="text-lg font-bold" />
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group',
                isActive
                  ? 'bg-gradient-to-r from-amber-500/15 to-orange-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20 shadow-sm'
                  : 'text-muted-foreground hover:bg-accent/5 hover:text-foreground hover:border hover:border-border/50'
              )}
            >
              <div
                className={cn(
                  'transition-colors duration-200',
                  isActive ? 'text-amber-600 dark:text-amber-400' : 'text-muted-foreground group-hover:text-foreground'
                )}
              >
                <item.icon className="h-4 w-4" />
              </div>
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Theme toggle */}
      <div className="px-3 py-2 border-t border-border/50">
        <ThemeToggle />
      </div>

      {/* User section */}
      <div className="p-3 border-t border-border/50">
        <Link
          href="/profile"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-accent/5 transition-all duration-200 group border border-transparent hover:border-border/50"
        >
          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center border border-amber-500/20">
            <User className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate text-foreground/90">
              {user?.name || 'Student'}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {user?.university || 'University'}
            </p>
          </div>
        </Link>
      </div>
    </aside>
  )
}
