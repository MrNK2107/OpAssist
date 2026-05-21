'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth-store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Rocket, Search, Trophy, Users, Sparkles, ArrowRight } from 'lucide-react'
import { UNIVERSITIES } from '@/lib/universities'

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  )
}

function GetStartedForm() {
  const [step, setStep] = useState<'form' | 'university'>('form')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [university, setUniversity] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get('redirect') || '/dashboard'
  const { signUp, signInWithGoogle } = useAuthStore()

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await signUp(email, password)
      await api.put('/api/profile', { name, university, year: 1 })
      router.push(redirect)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setLoading(true)
    setError('')

    try {
      await signInWithGoogle()
      // Check if user already has a profile
      try {
        await api.get('/api/profile')
        router.push(redirect)
      } catch {
        // No profile yet — ask for university
        setStep('university')
        setLoading(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in with Google')
      setLoading(false)
    }
  }

  const handleUniversitySubmit = async () => {
    if (!university) return
    setLoading(true)
    try {
      await api.put('/api/profile', { name: '', university, year: 1 })
      router.push(redirect)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save university')
      setLoading(false)
    }
  }

  if (step === 'university') {
    return (
      <Card className="w-full max-w-md animate-fade-in-up">
        <div className="h-1 w-full bg-gradient-to-r from-cyan-500 via-violet-500 to-pink-500 rounded-t-xl" />
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">One more thing</CardTitle>
          <CardDescription>Select your university to personalize your experience</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground/80">University</label>
            <select
              className="flex h-10 w-full rounded-lg border border-input bg-background/50 backdrop-blur-sm px-3 py-2 text-sm shadow-sm transition-all duration-200 hover:border-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={university}
              onChange={(e) => setUniversity(e.target.value)}
            >
              <option value="">Select your university</option>
              {UNIVERSITIES.map((uni) => (
                <option key={uni} value={uni}>{uni}</option>
              ))}
            </select>
          </div>
          <Button
            className="w-full h-10 gap-2"
            disabled={!university || loading}
            onClick={handleUniversitySubmit}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Saving...
              </>
            ) : (
              <>
                Continue
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="w-full max-w-4xl grid md:grid-cols-2 gap-8 items-center animate-fade-in-up">
      {/* Left: Branding */}
      <div className="hidden md:block space-y-6">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Rocket className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
            OpAssist
          </span>
        </div>
        <h1 className="text-3xl font-bold">
          Your university career{' '}
          <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
            starts here
          </span>
        </h1>
        <p className="text-muted-foreground leading-relaxed">
          Discover hackathons, internships, scholarships, and open source opportunities — all in one place.
        </p>
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/20">
              <Search className="h-4 w-4 text-cyan-400" />
            </div>
            AI-powered opportunity matching
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/20">
              <Trophy className="h-4 w-4 text-violet-400" />
            </div>
            Track your progress from beginner to pro
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-pink-500/20 to-rose-500/20 border border-pink-500/20">
              <Users className="h-4 w-4 text-pink-400" />
            </div>
            Find teammates and learn from peers
          </div>
        </div>
      </div>

      {/* Right: Auth form */}
      <Card className="w-full max-w-md justify-self-center">
        <div className="h-1 w-full bg-gradient-to-r from-cyan-500 via-violet-500 to-pink-500 rounded-t-xl" />
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2 md:hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center">
              <Rocket className="h-5 w-5 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl">Get started</CardTitle>
          <CardDescription>Create your free account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>
          )}

          <Button
            variant="outline"
            className="w-full gap-2 h-10"
            onClick={handleGoogleSignIn}
            disabled={loading}
          >
            <GoogleIcon />
            Continue with Google
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border/50" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">or continue with email</span>
            </div>
          </div>

          <form onSubmit={handleEmailSignup} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground/80">Full Name</label>
              <Input
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground/80">Email</label>
              <Input
                type="email"
                placeholder="you@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground/80">University</label>
              <select
                className="flex h-10 w-full rounded-lg border border-input bg-background/50 backdrop-blur-sm px-3 py-2 text-sm shadow-sm transition-all duration-200 hover:border-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
                required
              >
                <option value="">Select your university</option>
                {UNIVERSITIES.map((uni) => (
                  <option key={uni} value={uni}>{uni}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground/80">Password</label>
              <Input
                type="password"
                placeholder="Min 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>

            <Button type="submit" className="w-full h-10 gap-2" disabled={loading}>
              {loading ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create Account
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function GetStartedPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-4xl grid md:grid-cols-2 gap-8">
        <div className="hidden md:block h-96 animate-pulse bg-card/50 rounded-xl" />
        <div className="h-[32rem] animate-pulse bg-card/50 rounded-xl" />
      </div>
    }>
      <GetStartedForm />
    </Suspense>
  )
}
