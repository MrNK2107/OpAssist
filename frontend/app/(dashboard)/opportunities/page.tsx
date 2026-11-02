'use client'

import { useEffect, useState, useSyncExternalStore } from 'react'
import { OpportunityCard } from '@/components/opportunity-card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight, Code, GraduationCap, Briefcase, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'
import type { Opportunity } from '@/types/opportunity'

const CORE_TYPES = ['hackathon', 'internship', 'job'] as const
const ALL_TYPES = ['hackathon', 'internship', 'job', 'scholarship', 'oss', 'ambassador', 'event']
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced']

const noopSubscribe = () => () => {}
function getUrlTypeParam(): string | null {
  const typeParam = new URLSearchParams(window.location.search).get('type')
  return typeParam && ALL_TYPES.includes(typeParam) ? typeParam : null
}

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  // Initial type filter comes from ?type=; once the user picks a filter it overrides the URL.
  const urlType = useSyncExternalStore(noopSubscribe, getUrlTypeParam, () => null)
  const [typeOverride, setTypeFilter] = useState<string | null | undefined>(undefined)
  const typeFilter = typeOverride === undefined ? urlType : typeOverride
  const [difficultyFilter, setDifficultyFilter] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const limit = 20

  useEffect(() => {
    const fetchOpps = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (search) params.set('search', search)
        if (typeFilter) params.set('type', typeFilter)
        if (difficultyFilter) params.set('difficulty', difficultyFilter)
        params.set('limit', String(limit))
        params.set('offset', String((page - 1) * limit))

        const data = await api.get<{ data: Opportunity[]; total: number }>(
          `/api/opportunities?${params.toString()}`
        )
        setOpportunities(data.data)
        setTotal(data.total)
      } catch {
        // silent
      } finally {
        setLoading(false)
      }
    }

    const debounce = setTimeout(fetchOpps, 300)
    return () => clearTimeout(debounce)
  }, [search, typeFilter, difficultyFilter, page])

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Discover Opportunities</h1>
        <p className="text-muted-foreground">Browse hackathons, internships, scholarships, and more</p>
      </div>

      {/* Search & Filters */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search opportunities..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="pl-9"
          />
        </div>

        {/* Core vertical quick-filter tabs */}
        <div className="flex flex-wrap gap-2 pb-2 border-b border-border/30">
          <div className="flex items-center gap-1 mr-2">
            <Sparkles className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium">Jump to:</span>
          </div>
          {CORE_TYPES.map((t) => {
            const icons = { hackathon: Code, internship: GraduationCap, job: Briefcase }
            const Icon = icons[t]
            const colors = { hackathon: 'text-amber-600 dark:text-amber-400 border-amber-500/30 hover:bg-amber-500/10', internship: 'text-teal-700 dark:text-teal-400 border-orange-500/30 hover:bg-orange-500/10', job: 'text-lime-400 border-lime-500/30 hover:bg-lime-500/10' }
            return (
              <Badge
                key={t}
                variant={typeFilter === t ? 'default' : 'outline'}
                className={`cursor-pointer capitalize gap-1.5 px-3 py-1.5 text-sm ${typeFilter !== t ? colors[t] : ''}`}
                onClick={() => { setTypeFilter(typeFilter === t ? null : t); setPage(1) }}
              >
                <Icon className="h-3.5 w-3.5" />
                {t}
              </Badge>
            )
          })}
          {typeFilter && (
            <Badge
              variant="outline"
              className="cursor-pointer text-muted-foreground hover:text-foreground"
              onClick={() => { setTypeFilter(null); setPage(1) }}
            >
              Clear
            </Badge>
          )}
        </div>

        {/* All type filters */}
        <div className="flex flex-wrap gap-1.5">
          <div className="flex items-center gap-1 mr-1">
            <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">All types:</span>
          </div>
          {ALL_TYPES.map((t) => (
            <Badge
              key={t}
              variant={typeFilter === t ? 'secondary' : 'ghost'}
              className={`cursor-pointer text-xs ${typeFilter === t ? '' : 'text-muted-foreground hover:text-foreground'}`}
              onClick={() => { setTypeFilter(typeFilter === t ? null : t); setPage(1) }}
            >
              {t}
            </Badge>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-muted-foreground">Difficulty:</span>
          {DIFFICULTIES.map((d) => (
            <Badge
              key={d}
              variant={difficultyFilter === d ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => { setDifficultyFilter(difficultyFilter === d ? null : d); setPage(1) }}
            >
              {d}
            </Badge>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 animate-pulse bg-muted rounded-xl" />
          ))}
        </div>
      ) : opportunities.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No opportunities found. Try adjusting your filters.
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{total} opportunities found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((opp) => (
              <OpportunityCard
                key={opp.id}
                id={opp.id}
                title={opp.title}
                type={opp.type}
                organizer={opp.organizer}
                deadline={opp.deadline}
                location={opp.location}
                prize={opp.prize}
                tags={opp.tags}
                difficulty={opp.difficulty}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
