import {
  LayoutDashboard,
  Compass,
  Bookmark,
  Briefcase,
  Calendar,
  Users,
  Trophy,
  Bell,
  Radar,
} from 'lucide-react'

export const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/radar', label: 'Radar', icon: Radar },
  { href: '/opportunities', label: 'Discover', icon: Compass },
  { href: '/bookmarks', label: 'Bookmarks', icon: Bookmark },
  { href: '/applications', label: 'Applications', icon: Briefcase },
  { href: '/calendar', label: 'Calendar', icon: Calendar },
  { href: '/team-finder', label: 'Team Finder', icon: Users },
  { href: '/leaderboard', label: 'Leaderboard', icon: Trophy },
  { href: '/notifications', label: 'Notifications', icon: Bell },
]
