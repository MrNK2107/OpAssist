'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/stores/auth-store'

export function useAuth() {
  const { user, loading, error, signOut, initialize } = useAuthStore()

  useEffect(() => {
    initialize()
  }, [initialize])

  return {
    user,
    loading,
    error,
    signOut,
    isAuthenticated: !!user,
  }
}
