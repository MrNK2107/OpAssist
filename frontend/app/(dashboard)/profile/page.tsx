'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { User, GraduationCap, Edit } from 'lucide-react'
import { api } from '@/lib/api'

interface Profile {
  id: string
  name: string
  university: string
  year: number
  bio: string
  avatar_url: string
  skills: string[]
  interests: string[]
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Profile>('/api/profile')
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  if (!profile) {
    return <div className="text-center py-12 text-muted-foreground">Profile not found.</div>
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Profile</h1>
        <Link href="/profile/edit">
          <Button variant="outline" size="sm">
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        </Link>
      </div>

      {/* Info */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">{profile.name || 'Unnamed'}</h2>
              <div className="flex items-center gap-2 text-muted-foreground mt-1">
                <GraduationCap className="h-4 w-4" />
                <span>{profile.university || 'No university set'} {profile.year ? `• Year ${profile.year}` : ''}</span>
              </div>
              {profile.bio && <p className="mt-3 text-muted-foreground">{profile.bio}</p>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <CardTitle>Skills</CardTitle>
        </CardHeader>
        <CardContent>
          {profile.skills.length === 0 ? (
            <p className="text-sm text-muted-foreground">No skills added yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <Badge key={skill} variant="secondary">{skill}</Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Interests */}
      <Card>
        <CardHeader>
          <CardTitle>Interests</CardTitle>
        </CardHeader>
        <CardContent>
          {profile.interests.length === 0 ? (
            <p className="text-sm text-muted-foreground">No interests added yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {profile.interests.map((interest) => (
                <Badge key={interest}>{interest}</Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
