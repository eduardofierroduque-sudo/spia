import { useState, useEffect } from 'react'
import {
  getConfigStatus, updateApiConfig, activateLicense, deactivateLicense,
  type ConfigStatus,
} from '../services/api'

const API_FIELDS = [
  { key: 'serpapi_key', label: 'SerpAPI Key', hint: 'serpapi.com — enables real Google search results', link: 'https://serpapi.com/manage-api-key' },
  { key: 'google_api_key', label: 'Google API Key', hint: 'console.cloud.google.com — Custom Search JSON API', link: 'https://console.cloud.google.com/apis/credentials' },
  { key: 'google_cse_id', label: 'Google CSE ID', hint: 'programmablesearchengine.google.com — search engine ID', link: 'https://programmablesearchengine.google.com/' },
  { key: 'hibp_api_key', label: 'HIBP API Key', hint: 'haveibeenpwned.com/API/Key — breach database access', link: 'https://haveibeenpwned.com/API/Key' },
  { key: 'dehashed_api_key', label: 'Dehashed API Key', hint: 'dehashed.com — deep breach search', link: 'https://dehashed.com/profile/api' },
  { key: 'dehashed_email', label: 'Dehashed Email', hint: 'Email registered with dehashed.com', link: '' },
  { key: 'intelx_key', label: 'IntelX API Key', hint: 'intelx.io — dark web + intel search', link: 'https://intelx.io/account' },
  { key: 'twitter_bearer_token', label: 'Twitter Bearer Token', hint: 'developer.twitter.com — social profile scan', link: 'https://developer.twitter.com/en/portal/dashboard' },
]

export function SettingsPage() {
  const [status, setStatus] = useState<ConfigStatus | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [licenseInput, setLicenseInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getConfigStatus().then(setStatus).catch(() => {})
  }, [])

  const handleSaveApi = async (key: string, value: string) => {
    setSaving(true)
    try {
      await updateApiConfig({ [key]: value || '' })
      const s = await getConfigStatus()
      setStatus(s)
      setMessage(`Saved ${API_FIELDS.find(f => f.key === key)?.label}`)
      setTimeout(() => setMessage(''), 2000)
    } catch {
      setMessage('Error saving')
    }
    setSaving(false)
  }

  const handleActivateLicense = async () => {
    if (!licenseInput.trim()) return
    setSaving(true)
    try {
      const res = await activateLicense(licenseInput.trim())
      setMessage(res.message)
      const s = await getConfigStatus()
      setStatus(s)
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Invalid license')
    }
    setSaving(false)
  }

  const handleDeactivateLicense = async () => {
    await deactivateLicense()
    const s = await getConfigStatus()
    setStatus(s)
    setMessage('License deactivated')
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up px-4">
      {/* License Section */}
      <section className="glass-card space-y-4">
        <div className="flex items-center gap-3">
          <span className="text-xl">&#x1F512;</span>
          <div>
            <h3 className="text-sm font-heading font-semibold text-gray-200">License</h3>
            <p className="text-[11px] text-gray-500 font-mono">
              {status?.license.valid
                ? `${status.license.plan.toUpperCase()} plan — Active`
                : 'No license — trial mode (DuckDuckGo only)'}
            </p>
          </div>
        </div>

        {status?.license.valid ? (
          <button onClick={handleDeactivateLicense} className="text-[11px] font-mono text-danger-400 hover:text-danger-300 transition-colors">
            Deactivate license
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              type="text"
              value={licenseInput}
              onChange={e => setLicenseInput(e.target.value)}
              placeholder="SPIA-PRO-xxxxxxxxxxxx"
              className="flex-1 input-primary text-xs"
              spellCheck={false}
            />
            <button onClick={handleActivateLicense} disabled={saving}
                    className="btn-primary text-xs px-4 py-2">
              Activate
            </button>
          </div>
        )}
      </section>

      {/* API Keys Section */}
      <section className="glass-card space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xl">&#x1F517;</span>
          <div>
            <h3 className="text-sm font-heading font-semibold text-gray-200">API Keys</h3>
            <p className="text-[11px] text-gray-500 font-mono">Bring your own keys — unlock full scan power</p>
          </div>
        </div>

        <div className="space-y-3">
          {API_FIELDS.map(field => (
            <div key={field.key} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-gray-400 flex items-center gap-2">
                  {field.label}
                  {status?.apis[field.key.replace('_key', '').replace('_id', '').replace('_email', '').replace('_token', '')] && (
                    <span className="w-1.5 h-1.5 rounded-full bg-success-400" title="Configured" />
                  )}
                </span>
                {field.link && (
                  <a href={field.link} target="_blank" rel="noopener noreferrer"
                     className="text-[10px] font-mono text-gray-600 hover:text-primary-400 transition-colors">
                    Get key &#x2197;
                  </a>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={form[field.key] ?? ''}
                  onChange={e => setForm(prev => ({ ...prev, [field.key]: e.target.value }))}
                  placeholder={field.hint}
                  className="flex-1 input-primary text-[11px] py-2"
                  spellCheck={false}
                  autoComplete="off"
                />
                <button
                  onClick={() => handleSaveApi(field.key, form[field.key] || '')}
                  disabled={saving}
                  className="text-[10px] font-mono text-primary-400 hover:text-primary-300
                             px-2 py-1 rounded border border-white/5 hover:border-primary-500/20
                             transition-colors disabled:opacity-30"
                >
                  Save
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Feature Status */}
      <section className="glass-card">
        <h3 className="text-sm font-heading font-semibold text-gray-200 mb-3">Feature Status</h3>
        <div className="grid grid-cols-2 gap-2">
          {status && [
            { label: 'Deep Web Search', on: status.features.deep_web_search, desc: 'SerpAPI or Google CSE' },
            { label: 'Breach API', on: status.features.breach_api, desc: 'HIBP or Dehashed' },
            { label: 'Dark Web Intel', on: status.features.dark_web_intelx, desc: 'IntelX API' },
            { label: 'Social Scan', on: status.features.social_scan, desc: 'Twitter API' },
          ].map(f => (
            <div key={f.label} className="flex items-center gap-2 text-[11px] font-mono">
              <span className={`w-1.5 h-1.5 rounded-full ${f.on ? 'bg-success-400' : 'bg-gray-700'}`} />
              <span className={f.on ? 'text-gray-300' : 'text-gray-600'}>
                {f.label}
              </span>
              <span className="text-gray-700 hidden sm:inline">{f.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {message && (
        <div className="text-center text-[11px] font-mono text-primary-400 animate-scale-in">
          {message}
        </div>
      )}
    </div>
  )
}
