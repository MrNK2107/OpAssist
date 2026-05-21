import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Compass } from 'lucide-react'

export default function DashboardNotFound() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r bg-card h-screen sticky top-0">
        <div className="p-6 border-b">
          <span className="text-xl font-bold">OpAssist</span>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="h-14 border-b bg-card" />
        <div className="p-6">
          <Card className="max-w-md mx-auto mt-12">
            <CardContent className="p-8 text-center">
              <Compass className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h1 className="text-4xl font-bold mb-2">404</h1>
              <h2 className="text-xl font-semibold mb-2">Page not found</h2>
              <p className="text-muted-foreground mb-6">
                This page doesn&apos;t exist in the dashboard.
              </p>
              <Link href="/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
