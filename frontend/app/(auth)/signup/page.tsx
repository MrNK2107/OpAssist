'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth-store'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'
import { UniversitySelect } from '@/components/ui/university-select'
import { RadarMark } from '@/components/brand/radar-mark'

function SignupForm() {
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

  const handleGoogleSignIn = async () => {
    setLoading(true)
    setError('')
    try {
      await signInWithGoogle()
      try {
        await api.get('/api/profile')
      } catch {
        await api.put('/api/profile', { name: '', university, year: 1 })
      }
      router.push(redirect)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in with Google')
      setLoading(false)
    }
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await signUp(email, password)

      // Create profile via backend API
      await api.put('/api/profile', {
        name,
        university,
        year: 1,
      })

      router.push(redirect)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md animate-fade-in-up">
      {/* Gradient top bar */}
      <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-orange-500 to-pink-500 rounded-t-xl" />

      <CardHeader className="text-center">
        <div className="flex justify-center mb-3">
          <RadarMark className="w-12 h-12" />
        </div>
        <CardTitle as="h1" className="text-2xl">Join OpAssist</CardTitle>
        <CardDescription>Create your account to discover opportunities</CardDescription>
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
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
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

        <form onSubmit={handleSignup} className="space-y-4">

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
            <label className="text-sm font-medium text-foreground/80">University Email</label>
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
            <UniversitySelect
              value={university}
              onChange={setUniversity}
              placeholder="Select your university"
              required
            />
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

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-amber-600 dark:text-amber-400 hover:text-amber-300 transition-colors font-medium">
              Sign in
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  )
}

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-md">
        <div className="h-[32rem] animate-pulse bg-card/50 rounded-xl border border-border/50" />
      </div>
    }>
      <SignupForm />
    </Suspense>
  )
}
