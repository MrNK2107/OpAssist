'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { StatCard } from '@/components/stat-card'
import { OpportunityCard } from '@/components/opportunity-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bookmark, Clock, Trophy, Target, ArrowRight, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate, daysUntil } from '@/lib/utils'
import type { Opportunity } from '@/types/opportunity'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

export default function DashboardPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [stats, setStats] = useState({ bookmarks: 0, applications: 0, inProgress: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [oppData, bookmarkData, appData] = await Promise.all([
          api.get<{ data: Opportunity[] }>('/api/opportunities?limit=4'),
          api.get<{ data: unknown[] }>('/api/bookmarks'),
          api.get<{ data: { status: string }[] }>('/api/applications'),
        ])

        setOpportunities(oppData.data)
        setStats({
          bookmarks: bookmarkData.data.length,
          applications: appData.data.length,
          inProgress: appData.data.filter((a) => ['preparing', 'applied', 'interviewing'].includes(a.status)).length,
        })
      } catch {
        // silent
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const upcomingDeadlines = opportunities
    .filter((o) => o.deadline && daysUntil(o.deadline) >= 0)
    .sort((a, b) => new Date(a.deadline!).getTime() - new Date(b.deadline!).getTime())
    .slice(0, 5)

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted animate-pulse rounded-lg" />
        <div className="h-4 w-64 bg-muted animate-pulse rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  const statCards = [
    { icon: Bookmark, value: stats.bookmarks, label: 'Bookmarks', gradient: 'cyan' as const },
    { icon: Clock, value: stats.inProgress, label: 'In Progress', gradient: 'violet' as const },
    { icon: Trophy, value: stats.applications, label: 'Applications', gradient: 'pink' as const },
    { icon: Target, value: stats.bookmarks + stats.applications, label: 'Tracked', gradient: 'amber' as const },
  ]

  return (
    <motion.div className="space-y-6" variants={container} initial="hidden" animate="show">
      {/* Header */}
      <motion.div variants={item}>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl md:text-3xl font-bold">Welcome back!</h1>
          <Sparkles className="h-5 w-5 text-cyan-400" />
        </div>
        <p className="text-muted-foreground">Here&apos;s what&apos;s happening with your opportunities</p>
      </motion.div>

      {/* Stats */}
      <motion.div variants={item} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <StatCard key={stat.label} icon={stat.icon} value={stat.value} label={stat.label} gradient={stat.gradient} />
        ))}
      </motion.div>

      {/* Recommended */}
      <motion.div variants={item}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recommended for you</h2>
          <Link href="/opportunities">
            <Button variant="outline" size="sm" className="gap-1.5">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
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
      </motion.div>

      {/* Upcoming Deadlines */}
      {upcomingDeadlines.length > 0 && (
        <motion.div variants={item}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Clock className="h-5 w-5 text-cyan-400" />
                Upcoming Deadlines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-border/50">
                {upcomingDeadlines.map((opp) => {
                  const days = daysUntil(opp.deadline!)
                  return (
                    <div key={opp.id} className="py-3 flex items-center justify-between group">
                      <div>
                        <Link href={`/opportunities/${opp.id}`} className="font-medium hover:text-cyan-400 transition-colors">
                          {opp.title}
                        </Link>
                        <p className="text-sm text-muted-foreground">{formatDate(opp.deadline!)}</p>
                      </div>
                      <span
                        className={`text-sm font-medium tabular-nums px-2.5 py-1 rounded-full ${
                          days <= 3
                            ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                            : days <= 7
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {days}d left
                      </span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  )
}
