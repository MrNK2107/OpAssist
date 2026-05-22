'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Bell, AlertTriangle, Info, Clock, CheckCheck } from 'lucide-react'
import { api } from '@/lib/api'

interface Notification {
  id: string
  type: string
  urgency: string
  title: string
  message: string
  opportunity_id?: string
  is_read: boolean
  created_at: string
}

const urgencyConfig: Record<string, { icon: typeof Bell; color: string; bg: string }> = {
  urgent: { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-500/10' },
  warning: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  info: { icon: Info, color: 'text-blue-500', bg: 'bg-blue-500/10' },
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [unreadCount, setUnreadCount] = useState(0)

  const fetchNotifications = async () => {
    try {
      const data = await api.get<{ data: Notification[]; unread_count: number }>('/api/notifications')
      setNotifications(data.data || [])
      setUnreadCount(data.unread_count || 0)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNotifications()
  }, [])

  const handleMarkRead = async (id: string) => {
    try {
      await api.put(`/api/notifications/${id}/read`, {})
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch {
      // silent
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await api.put('/api/notifications/read-all', {})
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // silent
    }
  }

  if (loading) {
    return <div className="h-64 animate-pulse bg-muted rounded-xl" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          <p className="text-muted-foreground">Stay updated on deadlines and activity</p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck className="mr-2 h-4 w-4" />
            Mark all read
          </Button>
        )}
      </div>

      {notifications.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-medium mb-2">No notifications</h3>
            <p className="text-sm text-muted-foreground">
              Bookmark or apply to opportunities to receive deadline reminders.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notif) => {
            const config = urgencyConfig[notif.urgency] || urgencyConfig.info
            const Icon = config.icon
            return (
              <Card key={notif.id} className={notif.is_read ? 'opacity-60' : ''}>
                <CardContent className="p-4 flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${config.bg}`}>
                    <Icon className={`h-4 w-4 ${config.color}`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{notif.title}</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{notif.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(notif.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={notif.urgency === 'urgent' ? 'destructive' : 'secondary'}>
                      {notif.urgency}
                    </Badge>
                    {!notif.is_read && (
                      <Button variant="ghost" size="sm" onClick={() => handleMarkRead(notif.id)}>
                        Mark read
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
