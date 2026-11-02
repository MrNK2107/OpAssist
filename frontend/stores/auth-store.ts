import { create } from 'zustand'
import { firebaseConfigured, getFirebaseAuth } from '@/lib/firebase'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  type User,
} from 'firebase/auth'

interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<User>
  signInWithGoogle: () => Promise<User>
  signOut: () => Promise<void>
  initialize: () => void
}

let unsubscribe: (() => void) | null = null

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,

  signIn: async (email, password) => {
    set({ error: null })
    try {
      await signInWithEmailAndPassword(getFirebaseAuth(), email, password)
      document.cookie = 'firebase-auth=true; path=/; max-age=86400; SameSite=Lax'
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sign in'
      set({ error: message })
      throw err
    }
  },

  signUp: async (email, password) => {
    set({ error: null })
    try {
      const { user } = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password)
      document.cookie = 'firebase-auth=true; path=/; max-age=86400; SameSite=Lax'
      return user
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create account'
      set({ error: message })
      throw err
    }
  },

  signInWithGoogle: async () => {
    set({ error: null })
    try {
      const provider = new GoogleAuthProvider()
      const { user } = await signInWithPopup(getFirebaseAuth(), provider)
      document.cookie = 'firebase-auth=true; path=/; max-age=86400; SameSite=Lax'
      return user
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sign in with Google'
      set({ error: message })
      throw err
    }
  },

  signOut: async () => {
    try {
      await firebaseSignOut(getFirebaseAuth())
      set({ user: null, error: null })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to sign out' })
    }
  },

  initialize: () => {
    // Clean up previous listener
    if (unsubscribe) {
      unsubscribe()
    }

    if (!firebaseConfigured) {
      // Public deployment without auth: behave as signed out.
      set({ user: null, loading: false, error: null })
      return
    }

    unsubscribe = onAuthStateChanged(getFirebaseAuth(), (user) => {
      // Set cookie for middleware route protection
      if (user) {
        document.cookie = 'firebase-auth=true; path=/; max-age=86400; SameSite=Lax'
      } else {
        document.cookie = 'firebase-auth=; path=/; max-age=0'
      }
      set({ user, loading: false, error: null })
    }, (err) => {
      set({ loading: false, error: err.message })
    })
  },
}))
