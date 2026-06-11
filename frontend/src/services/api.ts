import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

function getApiKey(): string {
  return import.meta.env.VITE_SPIA_API_KEY || ''
}

function authHeaders(): Record<string, string> {
  const key = getApiKey()
  return key ? { 'X-API-Key': key } : {}
}

export async function scanPrivacy(query: string, queryType = 'auto') {
  const { data } = await api.post('/scan', { query, query_type: queryType }, { headers: authHeaders() })
  return data
}

export async function healthCheck() {
  const { data } = await api.get('/health')
  return data
}

export interface ConfigStatus {
  apis: Record<string, boolean>
  license: { plan: string; activated: boolean; valid: boolean; expires_at: number | null }
  features: Record<string, boolean>
}

export async function getConfigStatus(): Promise<ConfigStatus> {
  const { data } = await api.get('/settings/status', { headers: authHeaders() })
  return data
}

export async function updateApiConfig(keys: Record<string, string>) {
  const { data } = await api.put('/settings/apis', keys, { headers: authHeaders() })
  return data
}

export async function activateLicense(licenseKey: string) {
  const { data } = await api.post('/settings/license/activate', { license_key: licenseKey }, { headers: authHeaders() })
  return data
}

export async function deactivateLicense() {
  const { data } = await api.post('/settings/license/deactivate', {}, { headers: authHeaders() })
  return data
}
