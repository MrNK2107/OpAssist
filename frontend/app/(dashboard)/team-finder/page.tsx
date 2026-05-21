'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Users, Search, Plus, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/hooks/use-auth'

interface TeamRequest {
  id: string
  user_id: string
  opportunity_id: string
  looking_for: string[]
  description: string
  max_members: number
  status: string
  created_at: string
  members?: string[]
  profiles?: {
    name: string
    university: string
    skills: string[]
  }
}

interface Opportunity {
  id: string
  title: string
  type: string
  deadline: string | null
}

export default function TeamFinderPage() {
  const { user } = useAuth()
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [selectedOpp, setSelectedOpp] = useState('')
  const [lookingFor, setLookingFor] = useState('')
  const [description, setDescription] = useState('')
  const [results, setResults] = useState<TeamRequest[]>([])
  const [searching, setSearching] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Load opportunities for the dropdown
  useEffect(() => {
    const loadOpportunities = async () => {
      try {
        const data = await api.get<{ data: Opportunity[] }>('/api/opportunities?limit=100&type=hackathon')
        setOpportunities(data.data || [])
      } catch {
        // silent
      }
    }
    loadOpportunities()
  }, [])

  const filteredOpportunities = opportunities.filter(opp =>
    opp.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSearch = async () => {
    if (!selectedOpp) return
    setSearching(true)
    setError(null)
    try {
      const data = await api.get<{ teams: TeamRequest[] }>(`/api/communities/team-find/${selectedOpp}`)
      setResults(data.teams || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search for teams')
    } finally {
      setSearching(false)
    }
  }

  const handleCreateRequest = async () => {
    if (!selectedOpp || !lookingFor.trim()) return
    setCreating(true)
    setError(null)
    try {
      await api.post('/api/communities/team-find', {
        opportunity_id: selectedOpp,
        looking_for: lookingFor.split(',').map((s) => s.trim()).filter(Boolean),
        description,
      })
      // Refresh results
      handleSearch()
      setLookingFor('')
      setDescription('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create team request')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteRequest = async (requestId: string) => {
    try {
      await api.delete(`/api/communities/team-find/${requestId}`)
      setResults((prev) => prev.filter((r) => r.id !== requestId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete team request')
    }
  }

  const handleJoinTeam = async (requestId: string) => {
    try {
      await api.post(`/api/communities/team-find/${requestId}/join`, {})
      // Refresh results to show updated membership
      handleSearch()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join team')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Team Finder</h1>
        <p className="text-muted-foreground">Find teammates for hackathons and competitions</p>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4 text-destructive text-sm">{error}</CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Select an Opportunity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Search hackathons</label>
            <Input
              placeholder="Type to filter opportunities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <div className="max-h-40 overflow-y-auto space-y-1 rounded-md border p-2">
              {filteredOpportunities.map((opp) => (
                <button
                  key={opp.id}
                  onClick={() => setSelectedOpp(opp.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selectedOpp === opp.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent'
                  }`}
                >
                  {opp.title}
                  {opp.deadline && (
                    <span className="ml-2 text-xs opacity-70">
                      (deadline: {new Date(opp.deadline).toLocaleDateString()})
                    </span>
                  )}
                </button>
              ))}
              {filteredOpportunities.length === 0 && (
                <p className="text-sm text-muted-foreground p-2">No hackathons found</p>
              )}
            </div>
          </div>

          <Button onClick={handleSearch} disabled={searching || !selectedOpp}>
            <Search className="mr-2 h-4 w-4" />
            {searching ? 'Searching...' : 'Search for Teams'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create Team Request</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Skills you need (comma-separated)</label>
            <Input
              placeholder="e.g. Frontend, ML, Design"
              value={lookingFor}
              onChange={(e) => setLookingFor(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Project description</label>
            <textarea
              className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
              placeholder="Describe what you're building..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <Button onClick={handleCreateRequest} disabled={creating || !selectedOpp || !lookingFor.trim()} variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            {creating ? 'Creating...' : 'Create Team Request'}
          </Button>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Available Teams</h2>
          {results.map((team) => (
            <Card key={team.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{team.description || 'Looking for teammates'}</p>
                    {team.profiles && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Posted by {team.profiles.name}
                        {team.profiles.university && ` from ${team.profiles.university}`}
                      </p>
                    )}
                    {team.looking_for?.length > 0 && (
                      <div className="mt-2">
                        <span className="text-sm text-muted-foreground">Looking for: </span>
                        {team.looking_for.map((s) => (
                          <Badge key={s} className="ml-1">{s}</Badge>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">
                      Max members: {team.max_members} · Posted {new Date(team.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {user?.uid === team.user_id ? (
                      <Button size="sm" variant="destructive" onClick={() => handleDeleteRequest(team.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    ) : team.members?.includes(user?.uid || '') ? (
                      <Button size="sm" variant="outline" disabled>Joined</Button>
                    ) : (
                      <Button size="sm" onClick={() => handleJoinTeam(team.id)}>Join</Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {results.length === 0 && !searching && (
        <Card>
          <CardContent className="p-8 text-center">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Select a hackathon and search for teams looking for members.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
