import { useState, useCallback } from 'react'
import { scanPrivacy } from '../services/api'
import type { PrivacyReport } from '../types'

export function usePrivacyScan() {
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<PrivacyReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  const scan = useCallback(async (query: string, queryType = 'auto') => {
    setLoading(true)
    setError(null)
    try {
      const res = await scanPrivacy(query, queryType)
      if (res.report) {
        setReport(res.report)
      }
      return res
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Scan error'
      setError(message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { loading, report, error, scan }
}
