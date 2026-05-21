'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Bell, Search, Menu, Rocket, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'

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
        <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuToggle}>
          <Menu className="h-5 w-5" />
        </Button>

        {/* Mobile logo */}
        <Link href="/" className="flex items-center gap-2 md:hidden">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center">
            <Rocket className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
            OpAssist
          </span>
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
          <Link href="/notifications">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            </Button>
          </Link>

          {/* Sign out */}
          {user && (
            <Button variant="ghost" size="icon" onClick={() => signOut()}>
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
