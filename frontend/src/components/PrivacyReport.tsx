import type { PrivacyReport } from '../types'

interface Props { report: PrivacyReport }

const CATEGORY_META: Record<string, { emoji: string; label: string; color: string; bar: string }> = {
  social:    { emoji: '\uD83C\uDF10', label: 'Social Media',    color: 'text-primary-400', bar: '#06b6d4' },
  databroker:{ emoji: '\uD83C\uDFE2', label: 'Data Brokers',      color: 'text-warning-400', bar: '#f59e0b' },
  breach:    { emoji: '\uD83D\uDD13', label: 'Breaches',          color: 'text-danger-400',  bar: '#ef4444' },
  leak:      { emoji: '\uD83D\uDCA7', label: 'Leaks / Pastes',    color: 'text-danger-400',  bar: '#ef4444' },
  darkweb:   { emoji: '\uD83C\uDF19', label: 'Dark Web',          color: 'text-purple-400', bar: '#a855f7' },
  forum:     { emoji: '\uD83D\uDCAC', label: 'Forums',            color: 'text-blue-400',   bar: '#60a5fa' },
  web:       { emoji: '\uD83C\uDF10', label: 'General Web',       color: 'text-gray-400',   bar: '#6b7280' },
  exposure:  { emoji: '\uD83D\uDC41', label: 'Exposure',          color: 'text-warning-400', bar: '#f59e0b' },
}

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'
  const label = score >= 70 ? 'Secure' : score >= 40 ? 'Caution' : 'Exposed'
  const ratio = (score / 100)

  return (
    <div className="flex flex-col items-center flex-shrink-0">
      <div className="relative w-[100px] h-[100px] sm:w-[120px] sm:h-[120px]">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx={60} cy={60} r={46} fill="none" stroke="#1f2937" strokeWidth="7" />
          <circle
            cx={60} cy={60} r={46} fill="none"
            stroke={color} strokeWidth="7" strokeLinecap="round"
            strokeDasharray={`${ratio * 289} 289`}
            style={{
              transition: 'stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: `drop-shadow(0 0 8px ${color}40)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl sm:text-3xl font-bold font-mono tracking-tight"
                style={{ color, textShadow: `0 0 12px ${color}30` }}>
            {score}
          </span>
          <span className="text-[9px] sm:text-[10px] font-heading font-semibold tracking-widest mt-0.5"
                style={{ color }}>
            {label}
          </span>
        </div>
      </div>
    </div>
  )
}

export function PrivacyReportView({ report }: Props) {
  const categoryEntries = Object.entries(report.categories).sort(([, a], [, b]) => b - a)
  const hasResults = report.total_exposures > 0

  return (
    <div className="space-y-3 sm:space-y-4 animate-scale-in">
      <div className="glass-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-6">
        <div className="min-w-0 flex-1">
          <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
              Scan result
            </span>
          <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-100 mt-1 truncate">
            {report.query}
          </h2>
          <p className="text-[11px] text-gray-500 mt-1 font-mono flex flex-wrap gap-x-3 gap-y-0.5">
            <span>{report.query_type === 'email' ? 'Email' : report.query_type === 'phone' ? 'Phone' :
                    report.query_type === 'username' ? 'Username' : 'Name'}</span>
            <span className="hidden sm:inline">&middot;</span>
            <span>{report.total_exposures} exposures</span>
            <span className="hidden sm:inline">&middot;</span>
            <span className="text-gray-600">
              {new Date(report.analyzed_at).toLocaleString('es-MX', {
                day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
              })}
            </span>
          </p>
        </div>
        <ScoreGauge score={report.privacy_score} />
      </div>

      {!hasResults && (
        <div className="glass-card text-center py-8 sm:py-10">
          <div className="text-3xl sm:text-4xl mb-3">&#x1F510;</div>
            <h3 className="text-sm sm:text-base font-heading font-semibold text-gray-300 mb-2">
              No exposures detected
            </h3>
            <p className="text-xs sm:text-sm text-gray-500 max-w-md mx-auto leading-relaxed px-4">
              No public data was found for{' '}
            <span className="text-primary-400 font-mono break-all">{report.query}</span>.
          </p>
          <ul className="text-[11px] sm:text-xs text-gray-500 mt-3 space-y-1 max-w-sm mx-auto text-left list-disc list-inside px-4">
            <li>The search engine may be temporarily limited (retry in 1-2 min)</li>
            <li>Your information has low public exposure &#x2705;</li>
            <li>Your data does not appear in social media or data broker indexes</li>
          </ul>
          <p className="text-[10px] sm:text-[11px] text-gray-600 mt-4 font-mono">
            SPIA scans: 50+ platforms &middot; 20+ data brokers &middot; HIBP &middot; Dark Web &middot; DuckDuckGo
          </p>
        </div>
      )}

      {hasResults && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
          <div className="lg:col-span-2 space-y-3">
            <h3 className="text-sm font-heading font-semibold text-gray-300 flex items-center gap-2">
              <span>&#x1F50D;</span>
              Exposures ({report.total_exposures})
            </h3>
            <div className="grid grid-cols-1 gap-2 max-h-[70vh] overflow-y-auto scrollbar-thin pr-1">
              {report.exposures.map((exp, i) => {
                const meta = CATEGORY_META[exp.category] || CATEGORY_META.web
                const riskBorder = exp.risk_level === 'high' ? 'border-l-danger-500 shadow-glow-danger' :
                                   exp.risk_level === 'medium' ? 'border-l-warning-500 shadow-glow-warning' :
                                   'border-l-white/10'
                return (
                  <a
                    key={i}
                    href={exp.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`glass-card !p-3 sm:!p-4 border-l-[3px] ${riskBorder}
                                hover:border-primary-500/30 transition-all duration-200 block
                                animate-slide-right`}
                    style={{ animationDelay: `${i * 0.04}s` }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="text-xs sm:text-sm font-mono text-gray-200 truncate">
                            {exp.label}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] sm:text-[10px] font-mono
                                           bg-white/5 border border-white/5 ${meta.color}`}>
                            {meta.emoji} {meta.label}
                          </span>
                          {exp.risk_level === 'high' && (
                            <span className="text-[9px] sm:text-[10px] font-mono text-danger-400 uppercase font-bold">
                              &#x26A0; High risk
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] sm:text-xs text-gray-500 leading-relaxed break-words">
                          {exp.detail}
                        </p>
                      </div>
                      <span className="text-gray-600 mt-1 flex-shrink-0 text-sm sm:text-base">
                        &#x2197;
                      </span>
                    </div>
                  </a>
                )
              })}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-heading font-semibold text-gray-300">
              Categories
            </h3>
            <div className="glass-card space-y-3">
              {categoryEntries.map(([cat, count]) => {
                const meta = CATEGORY_META[cat] || CATEGORY_META.web
                const pct = Math.round((count / report.total_exposures) * 100)
                return (
                  <div key={cat} className="space-y-1">
                    <div className="flex justify-between text-[11px] sm:text-xs">
                      <span className="font-mono text-gray-400 flex items-center gap-1">
                        <span className="text-xs">{meta.emoji}</span> {meta.label}
                      </span>
                      <span className="font-mono text-gray-300 tabular-nums">{count}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-1000 ease-out"
                           style={{ width: `${Math.max(pct, 4)}%`, backgroundColor: meta.bar }} />
                    </div>
                  </div>
                )
              })}
            </div>

            {report.data_sources.length > 0 && (
              <div className="glass-card">
                <h4 className="text-[10px] font-mono text-gray-500 uppercase tracking-wider mb-2">
                  Sources ({report.data_sources.length})
                </h4>
                <div className="flex flex-wrap gap-1">
                  {report.data_sources.slice(0, 10).map((s) => (
                    <span key={s} className="px-1.5 py-0.5 text-[10px] font-mono text-gray-400 glass rounded">
                      {s}
                    </span>
                  ))}
                  {report.data_sources.length > 10 && (
                    <span className="text-[10px] font-mono text-gray-600 self-center">
                      +{report.data_sources.length - 10}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {report.images.length > 0 && (
        <div className="glass-card animate-slide-up">
          <h3 className="text-sm font-heading font-semibold text-gray-200 mb-3 flex items-center gap-2">
            <span className="text-base">&#x1F5BC;</span>
            Related images ({report.images.length})
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {report.images.map((img, i) => (
              <a
                key={i}
                href={img.url}
                target="_blank"
                rel="noopener noreferrer"
                className="glass rounded-xl overflow-hidden group hover:border-primary-500/30
                           transition-all duration-200 hover:scale-[1.02]"
                style={{ animationDelay: `${i * 0.03}s` }}
              >
                <div className="aspect-square bg-base-900 flex items-center justify-center relative overflow-hidden">
                  <img
                    src={`/api/v1/image-proxy?url=${encodeURIComponent(img.url)}`}
                    alt={img.detail}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      const t = e.target as HTMLImageElement
                      const parent = t.parentElement
                      if (parent) {
                        parent.innerHTML =
                          '<div class="w-full h-full flex flex-col items-center justify-center text-gray-600 p-2">' +
                          '<span class="text-xl">&#x1F5BC;</span>' +
                          '<span class="text-[9px] font-mono mt-1 text-center truncate w-full px-1">' +
                          img.label +
                          '</span></div>'
                      }
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent
                                  opacity-0 group-hover:opacity-100 transition-opacity duration-200
                                  flex items-end p-2">
                    <span className="text-[9px] font-mono text-white/80 truncate w-full">
                      {img.label}
                    </span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {report.recommendations.length > 0 && (
        <div className="glass-card border-l-[3px] border-l-primary-500 animate-slide-up">
          <h3 className="text-sm font-heading font-semibold text-gray-200 mb-3 flex items-center gap-2">
            <span className="text-base">&#x1F6E1;</span> Recommendations
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {report.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-2 sm:gap-2.5 text-[11px] sm:text-xs text-gray-400
                                      glass rounded-xl px-3 py-2.5">
                <span className="text-primary-400 mt-0.5 flex-shrink-0 text-sm">&#x2713;</span>
                <span className="leading-relaxed">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
