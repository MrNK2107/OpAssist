'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import {
  Rocket, Trophy, Users, Calendar, Search, Bell, GraduationCap,
  Sparkles, ArrowRight, ChevronDown, Code, Zap, Globe, Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'

function useIntersection(ref: React.RefObject<HTMLElement | null>, options?: IntersectionObserverInit) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.unobserve(el)
        }
      },
      { threshold: 0.1, ...options }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [ref, options])

  return isVisible
}

function AnimatedSection({ children, className = '', id }: { children: React.ReactNode; className?: string; id?: string }) {
  const ref = useRef<HTMLElement>(null)
  const isVisible = useIntersection(ref)

  return (
    <section
      ref={ref}
      id={id}
      className={`transition-all duration-1000 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
      } ${className}`}
    >
      {children}
    </section>
  )
}

function FloatingElement({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <div
      className={`animate-float ${className}`}
      style={{ animationDelay: `${delay}s` }}
    >
      {children}
    </div>
  )
}

export default function Home() {
  const heroRef = useRef<HTMLDivElement>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 20,
        y: (e.clientY / window.innerHeight - 0.5) * 20,
      })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_hsl(240_10%_5%),_hsl(240_10%_3.9%))] overflow-hidden">
      {/* Animated background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-cyan-500/20 to-violet-500/20 rounded-full blur-3xl animate-pulse-glow"
          style={{ transform: `translate(${mousePos.x * 0.5}px, ${mousePos.y * 0.5}px)` }}
        />
        <div
          className="absolute top-1/3 -left-40 w-80 h-80 bg-gradient-to-br from-violet-500/15 to-pink-500/15 rounded-full blur-3xl animate-pulse-glow"
          style={{ animationDelay: '2s', transform: `translate(${-mousePos.x * 0.3}px, ${-mousePos.y * 0.3}px)` }}
        />
        <div
          className="absolute -bottom-40 right-1/4 w-72 h-72 bg-gradient-to-br from-amber-500/10 to-rose-500/10 rounded-full blur-3xl animate-pulse-glow"
          style={{ animationDelay: '4s' }}
        />
      </div>

      {/* Header */}
      <header className="relative z-50 border-b border-white/5 bg-black/20 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <Rocket className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                OpAssist
              </span>
            </div>
            <nav className="hidden md:flex items-center gap-8">
              <Link href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</Link>
              <Link href="#opportunities" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Opportunities</Link>
              <Link href="#stats" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Stats</Link>
            </nav>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm text-muted-foreground hover:text-foreground font-medium transition-colors"
              >
                Sign In
              </Link>
              <Link href="/get-started">
                <Button size="sm">
                  Get Started
                  <Sparkles className="ml-1.5 h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="relative px-4 pt-20 pb-16 md:pt-32 md:pb-24">
        <div className="max-w-5xl mx-auto text-center relative">
          {/* Floating badges */}
          <FloatingElement delay={0} className="absolute -top-4 -left-4 md:-top-8 md:-left-8">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-500/10 to-rose-500/10 border border-amber-500/20 text-amber-400 text-xs">
              <Zap className="h-3 w-3" />
              AI-Powered
            </div>
          </FloatingElement>
          <FloatingElement delay={2} className="absolute top-12 -right-4 md:top-20 md:-right-8">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20 text-cyan-400 text-xs">
              <Star className="h-3 w-3" />
              500+ Hackathons
            </div>
          </FloatingElement>

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-8 animate-fade-in-up">
            <Sparkles className="h-4 w-4" />
            The ultimate student opportunity platform
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold leading-tight mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <span className="bg-gradient-to-r from-cyan-400 via-violet-400 to-pink-400 bg-clip-text text-transparent">
              Discover
            </span>
            <br />
            <span className="text-foreground">Your Future</span>
          </h1>

          {/* Description */}
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up leading-relaxed" style={{ animationDelay: '0.2s' }}>
            All hackathons, jobs, internships, open source projects, and scholarships in one feed.
            Smart AI matching. Track your journey from beginner to professional.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
            <Link href="/get-started">
              <Button size="lg" className="gap-2 shadow-xl shadow-violet-500/20">
                Start Discovering
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <Link href="/opportunities">
              <Button variant="outline" size="lg" className="gap-2">
                Browse Opportunities
                <Search className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Hero visual */}
          <div className="mt-16 md:mt-24 relative animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <div className="max-w-3xl mx-auto">
              <div className="relative rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-6 md:p-8 shadow-2xl">
                {/* Feature grid preview */}
                <div className="grid grid-cols-3 gap-3 md:gap-4">
                  {[
                    { label: 'Hackathons', value: '500+', color: 'from-cyan-500 to-blue-500' },
                    { label: 'Internships', value: '200+', color: 'from-violet-500 to-purple-500' },
                    { label: 'Scholarships', value: '50+', color: 'from-pink-500 to-rose-500' },
                  ].map((item) => (
                    <div key={item.label} className="p-3 md:p-4 rounded-xl bg-white/5 border border-white/10">
                      <div className={`h-1.5 w-8 rounded-full bg-gradient-to-r ${item.color} mb-2`} />
                      <div className="text-xl md:text-2xl font-bold">{item.value}</div>
                      <div className="text-xs md:text-sm text-muted-foreground">{item.label}</div>
                    </div>
                  ))}
                </div>
                {/* Animated scanning line */}
                <div className="absolute inset-x-8 h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent animate-pulse-glow" style={{ top: '30%' }} />
              </div>
            </div>

            {/* Decorative dots */}
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-gradient-to-br from-violet-500/20 to-pink-500/20 rounded-full blur-xl" />
            <div className="absolute -top-4 -left-4 w-20 h-20 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-full blur-xl" />
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="flex justify-center mt-16 animate-bounce">
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        </div>
      </section>

      {/* Stats Section */}
      <AnimatedSection id="stats" className="py-16 md:py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-border/50 rounded-2xl overflow-hidden border border-border/50">
            {[
              { value: '500+', label: 'Hackathons', icon: '🏆' },
              { value: '200+', label: 'Internships', icon: '💼' },
              { value: '50+', label: 'Scholarships', icon: '🎓' },
              { value: '10K+', label: 'Students', icon: '👥' },
            ].map((stat) => (
              <div key={stat.label} className="bg-card/40 backdrop-blur-sm p-6 md:p-8 text-center group hover:bg-card/60 transition-colors">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </AnimatedSection>

      {/* Features */}
      <AnimatedSection id="features" className="py-16 md:py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                Everything
              </span>{' '}
              You Need to Succeed
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              AI-powered tools to discover, track, and win opportunities that match your goals.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {[
              {
                icon: Search,
                title: 'Smart Discovery',
                desc: 'AI-powered matching finds opportunities that fit your skills, interests, and academic calendar.',
                gradient: 'from-cyan-500 to-blue-500',
                gradientBg: 'from-cyan-500/10 to-blue-500/10',
                borderColor: 'border-cyan-500/20',
              },
              {
                icon: Trophy,
                title: 'Track Your Progress',
                desc: 'From your first hackathon to open source contributions - track your journey and get recommendations.',
                gradient: 'from-violet-500 to-purple-500',
                gradientBg: 'from-violet-500/10 to-purple-500/10',
                borderColor: 'border-violet-500/20',
              },
              {
                icon: Users,
                title: 'Community Power',
                desc: 'See what your peers are applying to, find teammates, and learn from success stories.',
                gradient: 'from-pink-500 to-rose-500',
                gradientBg: 'from-pink-500/10 to-rose-500/10',
                borderColor: 'border-pink-500/20',
              },
              {
                icon: Calendar,
                title: 'Calendar Integration',
                desc: 'Never miss a deadline with smart reminders and calendar sync for all your opportunities.',
                gradient: 'from-amber-500 to-orange-500',
                gradientBg: 'from-amber-500/10 to-orange-500/10',
                borderColor: 'border-amber-500/20',
              },
              {
                icon: Bell,
                title: 'Smart Alerts',
                desc: 'Get notified about opportunities matching your profile before they close.',
                gradient: 'from-emerald-500 to-teal-500',
                gradientBg: 'from-emerald-500/10 to-teal-500/10',
                borderColor: 'border-emerald-500/20',
              },
              {
                icon: GraduationCap,
                title: 'University Aware',
                desc: 'Filter by your college, track campus ambassador programs, and sync with academic calendar.',
                gradient: 'from-sky-500 to-indigo-500',
                gradientBg: 'from-sky-500/10 to-indigo-500/10',
                borderColor: 'border-sky-500/20',
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className={`group relative rounded-xl border ${feature.borderColor} bg-card/40 backdrop-blur-sm p-6 transition-all duration-300 hover:bg-card/60 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5`}
              >
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${feature.gradientBg} border ${feature.borderColor} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-foreground">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </AnimatedSection>

      {/* Opportunity Types */}
      <AnimatedSection id="opportunities" className="py-16 md:py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              All Opportunities in{' '}
              <span className="bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
                One Place
              </span>
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              From hackathons to jobs to scholarships — everything you need to launch your career.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4">
            {[
              { name: 'Hackathons', count: '500+', icon: '🏆', gradient: 'from-cyan-500/20 to-blue-500/20', border: 'border-cyan-500/20' },
              { name: 'Internships', count: '200+', icon: '💼', gradient: 'from-violet-500/20 to-purple-500/20', border: 'border-violet-500/20' },
              { name: 'Jobs', count: '1000+', icon: '👔', gradient: 'from-lime-500/20 to-green-500/20', border: 'border-lime-500/20' },
              { name: 'Scholarships', count: '50+', icon: '🎓', gradient: 'from-pink-500/20 to-rose-500/20', border: 'border-pink-500/20' },
              { name: 'Open Source', count: '100+', icon: '💻', gradient: 'from-amber-500/20 to-orange-500/20', border: 'border-amber-500/20' },
              { name: 'Ambassador', count: '30+', icon: '🌟', gradient: 'from-emerald-500/20 to-teal-500/20', border: 'border-emerald-500/20' },
            ].map((type, i) => (
              <Link
                key={type.name}
                href={`/opportunities?type=${type.name.toLowerCase()}`}
                className={`p-5 md:p-6 rounded-xl bg-gradient-to-br ${type.gradient} ${type.border} border text-center hover:scale-[1.02] transition-all duration-300 group`}
              >
                <div className="text-3xl mb-2 group-hover:scale-110 transition-transform inline-block">{type.icon}</div>
                <div className="font-semibold text-sm md:text-base">{type.name}</div>
                <div className="text-xs text-muted-foreground mt-1">{type.count} opportunities</div>
              </Link>
            ))}
          </div>
        </div>
      </AnimatedSection>

      {/* CTA */}
      <AnimatedSection className="py-16 md:py-24 px-4">
        <div className="max-w-3xl mx-auto text-center relative">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-violet-500/5 to-pink-500/5 rounded-3xl blur-3xl" />
          <div className="relative">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-6">
              <Sparkles className="h-4 w-4" />
              Free for students
            </div>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Ready to{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-violet-400 to-pink-400 bg-clip-text text-transparent">
                Launch
              </span>{' '}
              Your Career?
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-lg mx-auto">
              Join thousands of students discovering opportunities and building their future.
            </p>
            <Link href="/get-started">
              <Button size="lg" className="gap-2 shadow-xl shadow-violet-500/20">
                Get Started Free
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </AnimatedSection>

      {/* Footer */}
      <footer className="border-t border-border/50 bg-black/20 backdrop-blur-xl py-12 md:py-16 px-4">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center">
                <Rocket className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                OpAssist
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Your all-in-one opportunity discovery platform for university students.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-4">Platform</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/opportunities" className="text-muted-foreground hover:text-foreground transition-colors">Browse</Link></li>
              <li><Link href="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">Dashboard</Link></li>
              <li><Link href="/leaderboard" className="text-muted-foreground hover:text-foreground transition-colors">Leaderboard</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/opportunities" className="text-muted-foreground hover:text-foreground transition-colors">Browse Opportunities</Link></li>
              <li><Link href="/leaderboard" className="text-muted-foreground hover:text-foreground transition-colors">Leaderboard</Link></li>
              <li><Link href="/team-finder" className="text-muted-foreground hover:text-foreground transition-colors">Team Finder</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-4">Account</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/login" className="text-muted-foreground hover:text-foreground transition-colors">Sign In</Link></li>
              <li><Link href="/get-started" className="text-muted-foreground hover:text-foreground transition-colors">Sign Up</Link></li>
              <li><Link href="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">Dashboard</Link></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-10 pt-8 border-t border-border/50 text-sm text-center text-muted-foreground">
          <p>© 2026 OpAssist. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
