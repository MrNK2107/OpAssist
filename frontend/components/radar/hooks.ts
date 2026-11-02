'use client'

import { useEffect, useSyncExternalStore } from 'react'
import { useRadarStore } from '@/stores/radar-store'
import { todayIST } from '@/lib/radar/deadline'
import { SNAPSHOT_DATE } from '@/lib/radar/seed'

const noop = () => () => {}

/** Today's IST date on the client; the snapshot date during server render. */
export function useToday(): string {
  return useSyncExternalStore(noop, () => todayIST(), () => SNAPSHOT_DATE)
}

function subscribeHydration(cb: () => void) {
  return useRadarStore.persist.onFinishHydration(cb)
}

/** Rehydrates the persisted Radar store once and reports when it is ready. */
export function useRadarHydration(): boolean {
  useEffect(() => {
    if (!useRadarStore.persist.hasHydrated()) void useRadarStore.persist.rehydrate()
  }, [])
  return useSyncExternalStore(
    subscribeHydration,
    () => useRadarStore.persist.hasHydrated(),
    () => false,
  )
}
