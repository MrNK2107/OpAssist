import { initializeApp, getApps, type FirebaseApp } from 'firebase/app'
import { getAuth, type Auth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

/**
 * True when the public Firebase web config is present. Without it the app
 * still builds and the public pages (landing, Radar) work; sign-in shows a
 * clear "not configured" message instead of crashing at import time.
 */
export const firebaseConfigured = Boolean(firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId)

export const FIREBASE_NOT_CONFIGURED =
  'Sign-in is not configured on this deployment. Set the NEXT_PUBLIC_FIREBASE_* variables (see frontend/.env.example).'

let cachedAuth: Auth | null = null

export function getFirebaseApp(): FirebaseApp {
  if (!firebaseConfigured) throw new Error(FIREBASE_NOT_CONFIGURED)
  return getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
}

/** Lazily created Auth instance; throws a readable error when not configured. */
export function getFirebaseAuth(): Auth {
  if (!cachedAuth) cachedAuth = getAuth(getFirebaseApp())
  return cachedAuth
}

/** Minimal view used by the API client: the signed-in user, or null. */
export const auth = {
  get currentUser() {
    return firebaseConfigured ? getFirebaseAuth().currentUser : null
  },
}
