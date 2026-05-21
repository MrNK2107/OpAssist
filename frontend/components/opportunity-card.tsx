'use client'

import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Bookmark, MapPin, Calendar, Trophy } from 'lucide-react'
import { formatDate, daysUntil, getDeadlineStatus } from '@/lib/utils'

interface OpportunityCardProps {
  id: string
  title: string
  type: string
  organizer?: string
  deadline?: string | null
  location?: string
  prize?: string
  tags?: string[]
  difficulty?: string
  isBookmarked?: boolean
  onBookmark?: () => void
}

const typeColors: Record<string, { gradient: string; border: string; text: string }> = {
  hackathon: { gradient: 'from-cyan-500/20 to-blue-500/20', border: 'border-cyan-500/20', text: 'text-cyan-400' },
  internship: { gradient: 'from-violet-500/20 to-purple-500/20', border: 'border-violet-500/20', text: 'text-violet-400' },
  scholarship: { gradient: 'from-emerald-500/20 to-teal-500/20', border: 'border-emerald-500/20', text: 'text-emerald-400' },
  oss: { gradient: 'from-amber-500/20 to-orange-500/20', border: 'border-amber-500/20', text: 'text-amber-400' },
  ambassador: { gradient: 'from-pink-500/20 to-rose-500/20', border: 'border-pink-500/20', text: 'text-pink-400' },
  event: { gradient: 'from-sky-500/20 to-indigo-500/20', border: 'border-sky-500/20', text: 'text-sky-400' },
}

const difficultyColors: Record<string, string> = {
  beginner: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  intermediate: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  advanced: 'bg-red-500/10 text-red-400 border-red-500/20',
}

export function OpportunityCard({
  id,
  title,
  type,
  organizer,
  deadline,
  location,
  prize,
  tags = [],
  difficulty,
  isBookmarked,
  onBookmark,
}: OpportunityCardProps) {
  const deadlineStatus = deadline ? getDeadlineStatus(deadline) : null
  const daysLeft = deadline ? daysUntil(deadline) : null
  const typeConfig = typeColors[type] || typeColors.hackathon

  return (
    <Card className="group overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-cyan-500/5">
      <CardContent className="p-0">
        {/* Top accent bar */}
        <div className={`h-1 w-full bg-gradient-to-r ${typeConfig.gradient}`} />

        <div className="p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge
                  variant="outline"
                  className={`${typeConfig.border} ${typeConfig.text} bg-gradient-to-r ${typeConfig.gradient} border`}
                >
                  {type}
                </Badge>
                {difficulty && (
                  <Badge variant="outline" className={difficultyColors[difficulty] || ''}>
                    {difficulty}
                  </Badge>
                )}
              </div>
              <Link href={`/opportunities/${id}`} className="group/link">
                <h3 className="font-semibold text-base truncate group-hover/link:text-cyan-400 transition-colors">
                  {title}
                </h3>
              </Link>
              {organizer && (
                <p className="text-sm text-muted-foreground mt-0.5">{organizer}</p>
              )}
            </div>
            {onBookmark && (
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.preventDefault()
                  onBookmark()
                }}
                className="shrink-0 transition-all duration-200 hover:bg-cyan-500/10 hover:text-cyan-400"
              >
                <Bookmark
                  className={`h-4 w-4 transition-all ${
                    isBookmarked ? 'fill-cyan-400 text-cyan-400' : ''
                  }`}
                />
              </Button>
            )}
          </div>

          <div className="mt-3 space-y-1.5">
            {deadline && (
              <div className="flex items-center gap-1.5 text-sm">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                <span
                  className={
                    deadlineStatus === 'urgent'
                      ? 'text-red-400 font-medium'
                      : deadlineStatus === 'soon'
                      ? 'text-amber-400'
                      : 'text-muted-foreground'
                  }
                >
                  {formatDate(deadline)}
                  {daysLeft !== null && daysLeft >= 0 && (
                    <span className="ml-1">({daysLeft}d left)</span>
                  )}
                </span>
              </div>
            )}
            {location && (
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <MapPin className="h-3.5 w-3.5" />
                <span className="truncate">{location}</span>
              </div>
            )}
            {prize && (
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Trophy className="h-3.5 w-3.5" />
                <span className="truncate">{prize}</span>
              </div>
            )}
          </div>

          {tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {tags.slice(0, 4).map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {tags.length > 4 && (
                <Badge variant="secondary" className="text-xs">
                  +{tags.length - 4}
                </Badge>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
