'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { GraduationCap, Users, ArrowLeft, Trophy, Bookmark } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface University {
  name: string
  domain: string
  academic_calendar_json: Record<string, unknown>
}

interface Opportunity {
  id: string
  title: string
  type: string
  organizer: string
  deadline: string | null
  location: string
  prize: string
  tags: string[]
  difficulty: string
}

interface Activity {
  id: string
  user_id: string
  opportunity_id: string
  action: string
  created_at: string
}

export default function UniversityPage() {
  const params = useParams()
  const [university, setUniversity] = useState<University | null>(null)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [activity, setActivity] = useState<Activity[]>([])
  const [studentCount, setStudentCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.get<{
          university: University | null
          opportunities: Opportunity[]
          activity: Activity[]
          student_count: number
        }>(`/api/communities/university/${params.slug}`)

        setUniversity(data.university)
        setOpportunities(data.opportunities || [])
        setActivity(data.activity || [])
        setStudentCount(data.student_count || 0)
      } catch {
        // silent
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [params.slug])

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  const uniName = university?.name || (params.slug as string).replace(/-/g, ' ')

  return (
    <div className="space-y-6">
      <Link href="/leaderboard" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to leaderboard
      </Link>

      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-lg bg-primary/10">
          <GraduationCap className="h-8 w-8 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">{uniName}</h1>
          <p className="text-muted-foreground">
            {studentCount} {studentCount === 1 ? 'student' : 'students'} on OpAssist
          </p>
        </div>
      </div>

      {/* Opportunities */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Opportunities from {uniName}</h2>
        {opportunities.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Bookmark className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                No opportunities tracked by students from this university yet.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((opp) => (
              <Link key={opp.id} href={`/opportunities/${opp.id}`}>
                <Card className="h-full hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge>{opp.type}</Badge>
                      {opp.difficulty && <Badge variant="outline">{opp.difficulty}</Badge>}
                    </div>
                    <h3 className="font-medium mb-1">{opp.title}</h3>
                    {opp.organizer && (
                      <p className="text-sm text-muted-foreground">{opp.organizer}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      {opp.deadline && <span>Deadline: {formatDate(opp.deadline)}</span>}
                      {opp.location && <span>{opp.location}</span>}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Peer Activity */}
      {activity.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <Card>
            <CardContent className="divide-y">
              {activity.map((act) => (
                <div key={act.id} className="py-3 flex items-center gap-3">
                  <div className="p-1.5 rounded-full bg-muted">
                    {act.action === 'won' ? (
                      <Trophy className="h-4 w-4 text-yellow-500" />
                    ) : act.action === 'applied' ? (
                      <Users className="h-4 w-4 text-blue-500" />
                    ) : (
                      <Bookmark className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm">
                      A student {act.action} an opportunity
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(act.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
