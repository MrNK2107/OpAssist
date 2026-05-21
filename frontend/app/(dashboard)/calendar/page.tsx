'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface Opportunity {
  id: string
  title: string
  type: string
  deadline: string
}

export default function CalendarPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [currentDate, setCurrentDate] = useState(new Date())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<{ data: Opportunity[] }>('/api/opportunities?limit=100')
      .then((data) => setOpportunities(data.data.filter((o) => o.deadline)))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()

  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDay = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const prev = () => setCurrentDate(new Date(year, month - 1, 1))
  const next = () => setCurrentDate(new Date(year, month + 1, 1))

  // Map deadlines to days
  const deadlinesByDay: Record<number, Opportunity[]> = {}
  opportunities.forEach((opp) => {
    const d = new Date(opp.deadline)
    if (d.getFullYear() === year && d.getMonth() === month) {
      const day = d.getDate()
      if (!deadlinesByDay[day]) deadlinesByDay[day] = []
      deadlinesByDay[day].push(opp)
    }
  })

  const escapeIcs = (text: string) =>
    text.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n')

  const exportIcs = () => {
    const now = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    const lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'PRODID:-//OpAssist//EN',
    ]
    opportunities.forEach((opp) => {
      const d = new Date(opp.deadline)
      const dateStr = d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
      // End date is next day for all-day events
      const endDate = new Date(d.getTime() + 24 * 60 * 60 * 1000)
      const endDateStr = endDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
      lines.push(
        'BEGIN:VEVENT',
        `DTSTAMP:${now}`,
        `DTSTART:${dateStr}`,
        `DTEND:${endDateStr}`,
        `SUMMARY:${escapeIcs(opp.title)}`,
        `DESCRIPTION:Type: ${escapeIcs(opp.type)}`,
        `UID:${opp.id}@OpAssist`,
        'END:VEVENT'
      )
    })
    lines.push('END:VCALENDAR')

    const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'OpAssist-deadlines.ics'
    a.click()
    URL.revokeObjectURL(url)
  }

  const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Calendar</h1>
          <p className="text-muted-foreground">View upcoming deadlines</p>
        </div>
        <Button variant="outline" size="sm" onClick={exportIcs}>
          <Download className="mr-2 h-4 w-4" />
          Export .ics
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={prev}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <CardTitle>{monthName}</CardTitle>
            <Button variant="ghost" size="icon" onClick={next}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Day headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {days.map((d) => (
              <div key={d} className="text-center text-xs font-medium text-muted-foreground py-2">
                {d}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: startDay }).map((_, i) => (
              <div key={`empty-${i}`} className="h-24" />
            ))}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1
              const deadlines = deadlinesByDay[day] || []
              const isToday =
                new Date().getDate() === day &&
                new Date().getMonth() === month &&
                new Date().getFullYear() === year

              return (
                <div
                  key={day}
                  className={`h-24 border rounded p-1 overflow-hidden ${
                    isToday ? 'border-primary bg-primary/5' : 'border-border'
                  }`}
                >
                  <div className={`text-xs font-medium ${isToday ? 'text-primary' : ''}`}>
                    {day}
                  </div>
                  <div className="mt-0.5 space-y-0.5">
                    {deadlines.slice(0, 2).map((opp) => (
                      <Link key={opp.id} href={`/opportunities/${opp.id}`}>
                        <div className="text-[10px] truncate bg-primary/10 text-primary rounded px-1 py-0.5 hover:bg-primary/20">
                          {opp.title}
                        </div>
                      </Link>
                    ))}
                    {deadlines.length > 2 && (
                      <div className="text-[10px] text-muted-foreground">
                        +{deadlines.length - 2} more
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
