'use client'

import { useEffect } from 'react'
import { OpportunityCard } from '@/components/opportunity-card'
import { useBookmarksStore } from '@/stores/bookmarks-store'

interface BookmarkOpportunity {
  id: string
  title: string
  type: string
  organizer?: string
  deadline?: string | null
  location?: string
  prize?: string
  tags?: string[]
  difficulty?: string
}

export default function BookmarksPage() {
  const { bookmarks, loading, fetchBookmarks, removeBookmark } = useBookmarksStore()

  useEffect(() => {
    fetchBookmarks()
  }, [fetchBookmarks])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bookmarks</h1>
        <p className="text-muted-foreground">Your saved opportunities</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-48 animate-pulse bg-muted rounded-xl" />)}
        </div>
      ) : bookmarks.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No bookmarks yet. Browse opportunities and save the ones you like.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bookmarks.map((bm) => {
            const opp = bm.opportunities as BookmarkOpportunity | undefined
            if (!opp) return null
            return (
              <OpportunityCard
                key={bm.id}
                id={opp.id}
                title={opp.title}
                type={opp.type}
                organizer={opp.organizer}
                deadline={opp.deadline}
                location={opp.location}
                prize={opp.prize}
                tags={opp.tags}
                difficulty={opp.difficulty}
                isBookmarked
                onBookmark={() => removeBookmark(bm.id)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
