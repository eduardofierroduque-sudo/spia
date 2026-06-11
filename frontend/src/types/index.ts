export interface ExposedDatum {
  category: string
  label: string
  detail: string
  url: string
  risk_level: string
}

export interface PrivacyReport {
  id: string
  query: string
  query_type: string
  privacy_score: number
  total_exposures: number
  exposures: ExposedDatum[]
  images: ExposedDatum[]
  categories: Record<string, number>
  data_sources: string[]
  recommendations: string[]
  analyzed_at: string
}

export interface PrivacyResponse {
  status: string
  report: PrivacyReport | null
  message: string | null
}
