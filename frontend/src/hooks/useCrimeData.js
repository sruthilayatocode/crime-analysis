/**
 * useCrimeData.js
 *
 * Custom hook that fetches the real CrimeSense data from the backend API
 * (crime records + hotspot analysis) and exposes loading/error state so the
 * pages can render them without embedding any mock numbers.
 */
import { useEffect, useState } from 'react'
import { getCrimes, getHotspots } from '../services/crimeService'

export function useCrimeData() {
  const [crimes, setCrimes] = useState([])
  const [hotspots, setHotspots] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')
      try {
        const crimeRecords = await getCrimes()
        if (cancelled) return
        setCrimes(crimeRecords)

        // Hotspots are a separate (optional) endpoint; keep the dashboard
        // resilient if it is temporarily unavailable.
        try {
          const hotspotRecords = await getHotspots()
          if (!cancelled) setHotspots(hotspotRecords)
        } catch {
          // Hotspots are optional; the dashboard still works with crimes only.
          if (!cancelled) setHotspots([])
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Unable to load crime data.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

  return { crimes, hotspots, loading, error }
}