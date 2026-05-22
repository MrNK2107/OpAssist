'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { UNIVERSITIES } from '@/lib/universities'

export default function EditProfilePage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [university, setUniversity] = useState('')
  const [year, setYear] = useState(1)
  const [bio, setBio] = useState('')
  const [skills, setSkills] = useState<string[]>([])
  const [interests, setInterests] = useState<string[]>([])
  const [newSkill, setNewSkill] = useState('')
  const [newInterest, setNewInterest] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get<{
      name: string; university: string; year: number; bio: string; skills: string[]; interests: string[]
    }>('/api/profile').then((p) => {
      setName(p.name || '')
      setUniversity(p.university || '')
      setYear(p.year || 1)
      setBio(p.bio || '')
      setSkills(p.skills || [])
      setInterests(p.interests || [])
    })
  }, [])

  const handleSave = async () => {
    setSaving(true)
    await api.put('/api/profile', { name, university, year, bio, skills, interests })
    router.push('/profile')
  }

  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()])
      setNewSkill('')
    }
  }

  const removeSkill = (s: string) => setSkills(skills.filter((x) => x !== s))

  const addInterest = () => {
    if (newInterest.trim() && !interests.includes(newInterest.trim())) {
      setInterests([...interests, newInterest.trim()])
      setNewInterest('')
    }
  }

  const removeInterest = (i: string) => setInterests(interests.filter((x) => x !== i))

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Edit Profile</h1>

      <Card>
        <CardHeader><CardTitle>Basic Info</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">University</label>
            <select
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
              value={university}
              onChange={(e) => setUniversity(e.target.value)}
            >
              <option value="">Select</option>
              {UNIVERSITIES.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Year</label>
            <Input type="number" min={1} max={6} value={year} onChange={(e) => setYear(Number(e.target.value))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Bio</label>
            <textarea
              className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about yourself..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Skills</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              placeholder="Add a skill..."
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
            />
            <Button onClick={addSkill} size="sm">Add</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <span key={s} className="inline-flex items-center gap-1 bg-secondary text-secondary-foreground px-2 py-1 rounded text-sm">
                {s}
                <button onClick={() => removeSkill(s)} className="text-muted-foreground hover:text-foreground">&times;</button>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Interests</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={newInterest}
              onChange={(e) => setNewInterest(e.target.value)}
              placeholder="Add an interest..."
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
            />
            <Button onClick={addInterest} size="sm">Add</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {interests.map((i) => (
              <span key={i} className="inline-flex items-center gap-1 bg-primary/10 text-primary px-2 py-1 rounded text-sm">
                {i}
                <button onClick={() => removeInterest(i)} className="text-muted-foreground hover:text-foreground">&times;</button>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Profile'}
        </Button>
        <Button variant="outline" onClick={() => router.push('/profile')}>Cancel</Button>
      </div>
    </div>
  )
}
