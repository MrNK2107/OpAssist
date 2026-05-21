'use client'

import { useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useApplicationsStore } from '@/stores/applications-store'
import { formatDate } from '@/lib/utils'

interface ApplicationOpportunity {
  id: string
  title: string
  type: string
  organizer?: string
  deadline?: string | null
}

const STATUSES = ['saved', 'preparing', 'applied', 'interviewing', 'offered', 'rejected'] as const

const statusColors: Record<string, string> = {
  saved: 'bg-gray-500/10 text-gray-500',
  preparing: 'bg-yellow-500/10 text-yellow-500',
  applied: 'bg-blue-500/10 text-blue-500',
  interviewing: 'bg-purple-500/10 text-purple-500',
  offered: 'bg-green-500/10 text-green-500',
  rejected: 'bg-red-500/10 text-red-500',
}

export default function ApplicationsPage() {
  const { applications, loading, fetchApplications, updateApplication, deleteApplication } = useApplicationsStore()

  useEffect(() => {
    fetchApplications()
  }, [fetchApplications])

  const grouped = STATUSES.reduce((acc, status) => {
    acc[status] = applications.filter((a) => a.status === status)
    return acc
  }, {} as Record<string, typeof applications>)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Applications</h1>
        <p className="text-muted-foreground">Track your application pipeline</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-64 animate-pulse bg-muted rounded-xl" />)}
        </div>
      ) : applications.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No applications yet. Browse opportunities and start applying.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STATUSES.map((status) => {
            const apps = grouped[status]
            if (apps.length === 0) return null
            return (
              <div key={status} className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge className={statusColors[status]}>{status}</Badge>
                  <span className="text-sm text-muted-foreground">({apps.length})</span>
                </div>
                {apps.map((app) => {
                  const opp = app.opportunities as ApplicationOpportunity | undefined
                  return (
                    <Card key={app.id}>
                      <CardContent className="p-4 space-y-2">
                        <h3 className="font-medium text-sm">
                          {opp?.title || 'Unknown Opportunity'}
                        </h3>
                        {opp?.organizer && (
                          <p className="text-xs text-muted-foreground">{opp.organizer}</p>
                        )}
                        {app.applied_at && (
                          <p className="text-xs text-muted-foreground">
                            Applied: {formatDate(app.applied_at)}
                          </p>
                        )}
                        {app.notes && (
                          <p className="text-xs text-muted-foreground italic">{app.notes}</p>
                        )}
                        <div className="flex gap-2 pt-2">
                          {status !== 'offered' && status !== 'rejected' && (
                            <select
                              className="flex h-7 rounded border border-input bg-transparent px-2 text-xs"
                              value={status}
                              onChange={(e) => updateApplication(app.id, e.target.value)}
                            >
                              {STATUSES.map((s) => (
                                <option key={s} value={s}>{s}</option>
                              ))}
                            </select>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-destructive"
                            onClick={() => deleteApplication(app.id)}
                          >
                            Remove
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
