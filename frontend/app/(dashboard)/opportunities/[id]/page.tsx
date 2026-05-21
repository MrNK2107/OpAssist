'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ArrowLeft, Bookmark, Calendar, MapPin, Trophy, ExternalLink, Briefcase, Plus, Sparkles, AlertCircle
} from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate, daysUntil } from '@/lib/utils'
import type { Opportunity } from '@/types/opportunity'

interface MatchResult {
  score: number
  match_reasons: string[]
  concerns: string[]
  missing_skills: string[]
  preparation_suggestions: string[]
}

export default function OpportunityDetailPage() {
  const params = useParams()
  const [opp, setOpp] = useState<Opportunity | null>(null)
  const [loading, setLoading] = useState(true)
  const [isBookmarked, setIsBookmarked] = useState(false)
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null)
  const [matchLoading, setMatchLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.get<Opportunity>(`/api/opportunities/${params.id}`)
        setOpp(data)

        const bm = await api.get<{ is_bookmarked: boolean }>(`/api/bookmarks/check/${params.id}`)
        setIsBookmarked(bm.is_bookmarked)
      } catch {
        // silent
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [params.id])

  const handleBookmark = async () => {
    if (isBookmarked) {
      await api.delete(`/api/bookmarks/${params.id}`)
    } else {
      await api.post('/api/bookmarks', { opportunity_id: params.id })
    }
    setIsBookmarked(!isBookmarked)
  }

  const handleApply = async () => {
    await api.post('/api/applications', { opportunity_id: params.id, status: 'saved' })
  }

  const handleGetMatch = async () => {
    setMatchLoading(true)
    try {
      const result = await api.post<MatchResult>(`/api/opportunities/${params.id}/match`, {})
      setMatchResult(result)
    } catch {
      // silent
    } finally {
      setMatchLoading(false)
    }
  }

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  if (!opp) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Opportunity not found.</p>
        <Link href="/opportunities">
          <Button variant="link">Back to browse</Button>
        </Link>
      </div>
    )
  }

  const daysLeft = opp.deadline ? daysUntil(opp.deadline) : null

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <Link href="/opportunities" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to browse
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge>{opp.type}</Badge>
            {opp.difficulty && <Badge variant="outline">{opp.difficulty}</Badge>}
            {opp.is_closed && <Badge variant="destructive">Closed</Badge>}
          </div>
          <h1 className="text-3xl font-bold">{opp.title}</h1>
          {opp.organizer && <p className="text-lg text-muted-foreground mt-1">{opp.organizer}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant={isBookmarked ? 'default' : 'outline'} size="icon" onClick={handleBookmark}>
            <Bookmark className={`h-4 w-4 ${isBookmarked ? 'fill-current' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {opp.deadline && (
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Deadline</p>
                <p className={`font-medium ${daysLeft !== null && daysLeft <= 3 ? 'text-red-500' : ''}`}>
                  {formatDate(opp.deadline)}
                  {daysLeft !== null && daysLeft >= 0 && <span className="text-xs ml-1">({daysLeft}d)</span>}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
        {opp.location && (
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <MapPin className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Location</p>
                <p className="font-medium">{opp.location}</p>
              </div>
            </CardContent>
          </Card>
        )}
        {opp.prize && (
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <Trophy className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Prize</p>
                <p className="font-medium">{opp.prize}</p>
              </div>
            </CardContent>
          </Card>
        )}
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Source</p>
              <p className="font-medium capitalize">{opp.source}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {opp.url && (
          <a href={opp.url} target="_blank" rel="noopener noreferrer">
            <Button>
              <ExternalLink className="mr-2 h-4 w-4" />
              Apply / Visit
            </Button>
          </a>
        )}
        <Button variant="outline" onClick={handleApply}>
          <Plus className="mr-2 h-4 w-4" />
          Add to Applications
        </Button>
        <Button variant="outline" onClick={handleGetMatch} disabled={matchLoading}>
          <Sparkles className="mr-2 h-4 w-4" />
          {matchLoading ? 'Analyzing...' : 'Get Match Score'}
        </Button>
      </div>

      {/* Match Score */}
      {matchResult && (
        <Card className={matchResult.score >= 70 ? 'border-green-500/50' : matchResult.score >= 40 ? 'border-yellow-500/50' : 'border-red-500/50'}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI Match Score: {matchResult.score}/100
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {matchResult.match_reasons.length > 0 && (
              <div>
                <p className="text-sm font-medium text-green-600 mb-1">Why this is a good match:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {matchResult.match_reasons.map((r, i) => <li key={i}>• {r}</li>)}
                </ul>
              </div>
            )}
            {matchResult.concerns.length > 0 && (
              <div>
                <p className="text-sm font-medium text-yellow-600 mb-1">Potential concerns:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {matchResult.concerns.map((c, i) => <li key={i}>• {c}</li>)}
                </ul>
              </div>
            )}
            {matchResult.missing_skills.length > 0 && (
              <div>
                <p className="text-sm font-medium text-red-600 mb-1">Skills to develop:</p>
                <div className="flex flex-wrap gap-1">
                  {matchResult.missing_skills.map((s, i) => <Badge key={i} variant="destructive">{s}</Badge>)}
                </div>
              </div>
            )}
            {matchResult.preparation_suggestions.length > 0 && (
              <div>
                <p className="text-sm font-medium text-blue-600 mb-1">How to prepare:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {matchResult.preparation_suggestions.map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Description */}
      {opp.description && (
        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-muted-foreground">{opp.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {opp.tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Tags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {opp.tags.map((tag) => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
