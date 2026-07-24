'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { UniversitySelect } from '@/components/ui/university-select'
import { api } from '@/lib/api'
import {
  ArrowLeft,
  Save,
  X,
  Plus,
  User,
  GraduationCap,
  BookOpen,
  Wrench,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'

interface ProfileData {
  name: string
  university: string
  year: number
  bio: string
  skills: string[]
  interests: string[]
}

const YEAR_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8]

const SUGGESTED_SKILLS = [
  'Python', 'JavaScript', 'TypeScript', 'React', 'Next.js', 'Node.js',
  'Java', 'C++', 'Go', 'Rust', 'SQL', 'MongoDB',
  'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
  'Machine Learning', 'Deep Learning', 'AI', 'Data Science',
  'Flutter', 'React Native', 'Swift', 'Kotlin',
  'Solidity', 'Blockchain', 'Web3',
  'UI/UX Design', 'Figma', 'Product Management',
  'DevOps', 'CI/CD', 'Git', 'Linux',
]

const SUGGESTED_INTERESTS = [
  'Open Source', 'Hackathons', 'Competitive Programming',
  'AI/ML', 'Web Development', 'Mobile Development',
  'Cloud Computing', 'Cybersecurity', 'Blockchain',
  'UI/UX Design', 'Data Science', 'DevOps',
  'IoT', 'AR/VR', 'Game Development',
  'Tech Blogging', 'Community Building', 'Teaching',
  'Research', 'Entrepreneurship', 'Freelancing',
  'Robotics', 'Embedded Systems', 'Quantum Computing',
]

export default function EditProfilePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [dirty, setDirty] = useState(false)

  const [name, setName] = useState('')
  const [university, setUniversity] = useState('')
  const [year, setYear] = useState(1)
  const [bio, setBio] = useState('')
  const [skills, setSkills] = useState<string[]>([])
  const [interests, setInterests] = useState<string[]>([])

  const [skillInput, setSkillInput] = useState('')
  const [interestInput, setInterestInput] = useState('')

  const skillInputRef = useRef<HTMLInputElement>(null)
  const interestInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.get<ProfileData>('/api/profile')
      .then((p) => {
        setName(p.name || '')
        setUniversity(p.university || '')
        setYear(p.year || 1)
        setBio(p.bio || '')
        setSkills(p.skills || [])
        setInterests(p.interests || [])
      })
      .catch(() => setError('Failed to load profile'))
      .finally(() => setLoading(false))
  }, [])

  const markDirty = () => setDirty(true)

  const addSkill = (s: string) => {
    const trimmed = s.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
      setSkillInput('')
      markDirty()
    }
  }

  const removeSkill = (s: string) => {
    setSkills(skills.filter((x) => x !== s))
    markDirty()
  }

  const addInterest = (i: string) => {
    const trimmed = i.trim()
    if (trimmed && !interests.includes(trimmed)) {
      setInterests([...interests, trimmed])
      setInterestInput('')
      markDirty()
    }
  }

  const removeInterest = (i: string) => {
    setInterests(interests.filter((x) => x !== i))
    markDirty()
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      await api.put('/api/profile', { name, university, year, bio, skills, interests })
      setSuccess('Profile saved successfully')
      setDirty(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const hasChanges = dirty

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        <div className="h-48 bg-muted/50 rounded-xl" />
        <div className="h-32 bg-muted/50 rounded-xl" />
        <div className="h-32 bg-muted/50 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/profile')}
            className="shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl font-bold">Edit Profile</h1>
            <p className="text-sm text-muted-foreground">
              Update your information and preferences
            </p>
          </div>
        </div>
        {hasChanges && (
          <span className="text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded-full border border-amber-500/20">
            Unsaved changes
          </span>
        )}
      </div>

      {/* Notification banners */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-success bg-success/10 p-3 rounded-lg border border-success/20">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Basic Info */}
      <Card className="overflow-hidden">
        <div className="h-1 w-full bg-gradient-to-r from-cyan-500 via-violet-500 to-pink-500" />
        <CardContent className="p-6 space-y-6">
          {/* Avatar + Name row */}
          <div className="flex items-center gap-4">
            <div className="relative shrink-0">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-border flex items-center justify-center">
                <User className="h-8 w-8 text-muted-foreground" />
              </div>
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-foreground/80">Full Name</label>
              <Input
                value={name}
                onChange={(e) => { setName(e.target.value); markDirty() }}
                placeholder="Your name"
                className="h-10"
              />
            </div>
          </div>

          {/* University */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground/80 flex items-center gap-1.5">
              <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
              University
            </label>
            <UniversitySelect
              value={university}
              onChange={(v) => { setUniversity(v); markDirty() }}
            />
          </div>

          {/* Year + Bio row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground/80">Year of Study</label>
              <select
                value={year}
                onChange={(e) => { setYear(Number(e.target.value)); markDirty() }}
                className="flex h-10 w-full rounded-lg border border-input bg-background/50 backdrop-blur-sm px-3 py-2 text-sm shadow-sm transition-all duration-200 hover:border-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {YEAR_OPTIONS.map((y) => (
                  <option key={y} value={y}>
                    {y === 1 ? `${y}st` : y === 2 ? `${y}nd` : y === 3 ? `${y}rd` : `${y}th`} Year
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bio */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-1.5">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            Bio
          </CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            value={bio}
            onChange={(e) => { setBio(e.target.value); markDirty() }}
            placeholder="Tell us about yourself — your background, what you're building, what you're looking for..."
            className="flex min-h-[120px] w-full rounded-lg border border-input bg-background/50 backdrop-blur-sm px-4 py-3 text-sm shadow-sm transition-all duration-200 hover:border-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring placeholder:text-muted-foreground/60 resize-y"
          />
          <p className="mt-1.5 text-xs text-muted-foreground/60 text-right">
            {bio.length}/2000
          </p>
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-1.5">
            <Wrench className="h-4 w-4 text-muted-foreground" />
            Skills
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                ref={skillInputRef}
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addSkill(skillInput)
                  }
                }}
                placeholder="Type a skill and press Enter..."
                className="h-10 pr-8"
              />
              {skillInput && (
                <button
                  onClick={() => addSkill(skillInput)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 rounded-md bg-primary/10 flex items-center justify-center hover:bg-primary/20 transition-colors"
                >
                  <Plus className="h-3.5 w-3.5 text-primary" />
                </button>
              )}
            </div>
          </div>

          {/* Selected skills */}
          {skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {skills.map((s) => (
                <Badge key={s} variant="secondary" className="gap-1.5 py-1 pl-2.5 pr-1.5 text-xs">
                  {s}
                  <button
                    onClick={() => removeSkill(s)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-foreground/10 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {/* Suggested skills */}
          <div>
            <p className="text-xs text-muted-foreground/60 mb-2">Suggestions</p>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTED_SKILLS.filter((s) => !skills.includes(s)).slice(0, 12).map((s) => (
                <button
                  key={s}
                  onClick={() => addSkill(s)}
                  className="inline-flex items-center gap-1 rounded-full border border-border/50 px-2.5 py-1 text-xs text-muted-foreground hover:border-accent/50 hover:text-accent hover:bg-accent/5 transition-all duration-200"
                >
                  <Plus className="h-3 w-3" />
                  {s}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Interests */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-1.5">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            Interests
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                ref={interestInputRef}
                value={interestInput}
                onChange={(e) => setInterestInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addInterest(interestInput)
                  }
                }}
                placeholder="Type an interest and press Enter..."
                className="h-10 pr-8"
              />
              {interestInput && (
                <button
                  onClick={() => addInterest(interestInput)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 rounded-md bg-primary/10 flex items-center justify-center hover:bg-primary/20 transition-colors"
                >
                  <Plus className="h-3.5 w-3.5 text-primary" />
                </button>
              )}
            </div>
          </div>

          {interests.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {interests.map((i) => (
                <Badge key={i} className="gap-1.5 py-1 pl-2.5 pr-1.5 text-xs bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-cyan-400 border-transparent">
                  {i}
                  <button
                    onClick={() => removeInterest(i)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-foreground/10 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          <div>
            <p className="text-xs text-muted-foreground/60 mb-2">Suggestions</p>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTED_INTERESTS.filter((i) => !interests.includes(i)).slice(0, 12).map((i) => (
                <button
                  key={i}
                  onClick={() => addInterest(i)}
                  className="inline-flex items-center gap-1 rounded-full border border-border/50 px-2.5 py-1 text-xs text-muted-foreground hover:border-accent/50 hover:text-accent hover:bg-accent/5 transition-all duration-200"
                >
                  <Plus className="h-3 w-3" />
                  {i}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-2 border-t border-border/50">
        <Button
          onClick={handleSave}
          disabled={saving}
          size="lg"
          className="gap-2 min-w-[140px]"
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => router.push('/profile')}
        >
          Cancel
        </Button>
      </div>
    </div>
  )
}
