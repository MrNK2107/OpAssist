import { Card, CardContent } from '@/components/ui/card'
import { type LucideIcon } from 'lucide-react'

interface StatCardProps {
  icon: LucideIcon
  value: string | number
  label: string
  gradient?: 'cyan' | 'violet' | 'pink' | 'amber'
}

const gradientMap = {
  cyan: 'from-cyan-500/20 to-cyan-500/5 text-cyan-400 border-cyan-500/20',
  violet: 'from-violet-500/20 to-violet-500/5 text-violet-400 border-violet-500/20',
  pink: 'from-pink-500/20 to-pink-500/5 text-pink-400 border-pink-500/20',
  amber: 'from-amber-500/20 to-amber-500/5 text-amber-400 border-amber-500/20',
}

export function StatCard({ icon: Icon, value, label, gradient = 'cyan' }: StatCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl bg-gradient-to-br ${gradientMap[gradient]} border`}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-2xl font-bold tabular-nums">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
