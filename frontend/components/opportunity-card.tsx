'use client'

import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Bookmark, MapPin, Calendar, Trophy, Briefcase, GraduationCap, Code } from 'lucide-react'
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
  hackathon: { gradient: 'from-amber-500/20 to-blue-500/20', border: 'border-amber-500/20', text: 'text-amber-600 dark:text-amber-400' },
  internship: { gradient: 'from-orange-500/20 to-purple-500/20', border: 'border-orange-500/20', text: 'text-teal-700 dark:text-teal-400' },
  scholarship: { gradient: 'from-emerald-500/20 to-teal-500/20', border: 'border-emerald-500/20', text: 'text-emerald-400' },
  oss: { gradient: 'from-amber-500/20 to-orange-500/20', border: 'border-amber-500/20', text: 'text-amber-400' },
  ambassador: { gradient: 'from-pink-500/20 to-rose-500/20', border: 'border-pink-500/20', text: 'text-pink-400' },
  event: { gradient: 'from-sky-500/20 to-indigo-500/20', border: 'border-sky-500/20', text: 'text-sky-400' },
  job: { gradient: 'from-lime-500/20 to-green-500/20', border: 'border-lime-500/20', text: 'text-lime-400' },
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
  const typeIcons: Record<string, typeof Code> = { hackathon: Code, internship: GraduationCap, job: Briefcase }
  const TypeIcon = typeIcons[type]

  return (
    <Card className="group overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-amber-500/5">
      <CardContent className="p-0">
        {/* Top accent bar */}
        <div className={`h-1 w-full bg-gradient-to-r ${typeConfig.gradient}`} />

        <div className="p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <Badge
                  variant="outline"
                  className={`${typeConfig.border} ${typeConfig.text} bg-gradient-to-r ${typeConfig.gradient} border flex items-center gap-1`}
                >
                  {TypeIcon && <TypeIcon className="h-3 w-3" />}
                  {type}
                </Badge>
                {difficulty && (
                  <Badge variant="outline" className={difficultyColors[difficulty] || ''}>
                    {difficulty}
                  </Badge>
                )}
              </div>
              <Link href={`/opportunities/${id}`} className="group/link">
                <h3 className="font-semibold text-base truncate group-hover/link:text-amber-400 transition-colors">
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
                aria-label={isBookmarked ? `Remove bookmark: ${title}` : `Bookmark ${title}`}
                aria-pressed={!!isBookmarked}
                onClick={(e) => {
                  e.preventDefault()
                  onBookmark()
                }}
                className="shrink-0 transition-all duration-200 hover:bg-amber-500/10 hover:text-amber-400"
              >
                <Bookmark
                  className={`h-4 w-4 transition-all ${
                    isBookmarked ? 'fill-amber-400 text-amber-600 dark:text-amber-400' : ''
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
            {prize && type === 'hackathon' && (
              <div className="flex items-center gap-1.5 text-sm text-amber-700 dark:text-amber-300">
                <Trophy className="h-3.5 w-3.5" />
                <span className="truncate font-medium">{prize}</span>
              </div>
            )}
            {prize && type === 'internship' && (
              <div className="flex items-center gap-1.5 text-sm text-teal-700 dark:text-teal-300">
                <GraduationCap className="h-3.5 w-3.5" />
                <span className="truncate font-medium">Stipend: {prize}</span>
              </div>
            )}
            {prize && type === 'job' && (
              <div className="flex items-center gap-1.5 text-sm text-lime-300">
                <Briefcase className="h-3.5 w-3.5" />
                <span className="truncate font-medium">Salary: {prize}</span>
              </div>
            )}
            {prize && !['hackathon', 'internship', 'job'].includes(type) && (
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
