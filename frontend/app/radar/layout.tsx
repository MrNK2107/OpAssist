import type { Metadata } from 'next'
import { RadarShell } from '@/components/radar/radar-shell'

export const metadata: Metadata = {
  title: 'Radar · OpAssist',
  description: 'Hackathons and internships ranked for your skills, year and city, with a deadline radar and an application board. No sign-up needed.',
}

export default function RadarLayout({ children }: { children: React.ReactNode }) {
  return <RadarShell>{children}</RadarShell>
}
