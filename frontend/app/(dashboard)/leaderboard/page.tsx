'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Trophy, Medal } from 'lucide-react'
import { api } from '@/lib/api'

interface LeaderboardEntry {
  rank: number
  user_name: string
  points: number
  wins: number
  applications: number
}

const medalColors = ['text-yellow-500', 'text-gray-400', 'text-orange-600']

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<{ leaderboard: LeaderboardEntry[] }>('/api/communities/leaderboard')
      .then((data) => setLeaderboard(data.leaderboard))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Leaderboard</h1>
        <p className="text-muted-foreground">Campus rankings based on activity and achievements</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-primary" />
            Top Students
          </CardTitle>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No rankings data yet. Start applying to climb the leaderboard!
            </p>
          ) : (
            <div className="divide-y">
              {leaderboard.map((entry) => (
                <div key={entry.rank} className="py-4 flex items-center gap-4">
                  <div className="w-8 text-center">
                    {entry.rank <= 3 ? (
                      <Medal className={`h-6 w-6 mx-auto ${medalColors[entry.rank - 1]}`} />
                    ) : (
                      <span className="text-lg font-bold text-muted-foreground">
                        {entry.rank}
                      </span>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{entry.user_name}</p>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="font-bold">{entry.points}</p>
                      <p className="text-muted-foreground">Points</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold">{entry.wins}</p>
                      <p className="text-muted-foreground">Wins</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold">{entry.applications}</p>
                      <p className="text-muted-foreground">Applied</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
