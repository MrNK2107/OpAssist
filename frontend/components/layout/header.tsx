'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button, buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Bell, Search, Menu, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { RadarMark, Wordmark } from '@/components/brand/radar-mark'

interface HeaderProps {
  onMenuToggle?: () => void
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, signOut } = useAuth()
  const router = useRouter()
  const [searchValue, setSearchValue] = useState('')

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && searchValue.trim()) {
      router.push(`/opportunities?search=${encodeURIComponent(searchValue.trim())}`)
    }
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border/50 bg-background/60 backdrop-blur-xl">
      <div className="flex items-center gap-4 px-4 h-14">
        {/* Mobile menu */}
        <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuToggle} aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </Button>

        {/* Mobile logo */}
        <Link href="/" className="flex items-center gap-2 md:hidden">
          <RadarMark className="w-7 h-7" />
          <Wordmark className="font-bold" />
        </Link>

        {/* Search */}
        <div className="flex-1 max-w-md hidden sm:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60" />
            <Input
              placeholder="Search opportunities..."
              className="pl-9 h-9 bg-background/40"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
          </div>
        </div>

        <div className="flex items-center gap-1 ml-auto">
          {/* Notifications */}
          <Link
            href="/notifications"
            aria-label="Notifications"
            className={cn(buttonVariants({ variant: 'ghost', size: 'icon' }), 'relative')}
          >
            <Bell className="h-4 w-4" aria-hidden="true" />
            <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" aria-hidden="true" />
          </Link>

          {/* Sign out */}
          {user && (
            <Button variant="ghost" size="icon" onClick={() => signOut()} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
