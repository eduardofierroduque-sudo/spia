# SPIA Privacy Auditor

**Scan emails, usernames, names & phones across 60+ sources on the surface web, deep web, and dark web.**

SPIA (Sistema de Privacidad e Inteligencia de Auditoria) uncovers where personal information is publicly exposed across the internet. It searches social media platforms, data broker sites, breach databases, paste sites, and dark web search engines — then provides a privacy score and actionable recommendations.

## What It Scans

| Category | Sources |
|---|---|
| Social Media | Instagram, X/Twitter, Facebook, LinkedIn, TikTok, GitHub, Reddit, 50+ more |
| Data Brokers | Whitepages, Spokeo, BeenVerified, Intelius, 20+ more |
| Breach Databases | Have I Been Pwned, Dehashed, Collection #1-5, LinkedIn 2021, 30+ known breaches |
| Dark Web | Ahmia, Tor66, DarkSearch, OnionLand search engines |
| Leak Sites | Pastebin, JustPaste, Rentry, Ghostbin, leak forums |

## Input

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | Email, username, full name, or phone number |
| `queryType` | enum | No | `auto`, `email`, `username`, `name`, `phone` |
| `serpapiKey` | string | No | SerpAPI key for real Google results |
| `hibpApiKey` | string | No | HIBP API key for breach checks |

## Output

```json
{
  "query": "user@example.com",
  "query_type": "email",
  "privacy_score": 34,
  "total_exposures": 12,
  "categories": { "breach": 3, "social": 5, "databroker": 4 },
  "exposures": [{ "category": "breach", "label": "Adobe 2013", "detail": "...", "risk_level": "high", "url": "..." }],
  "recommendations": ["Change your passwords immediately...", "Enable 2FA..."]
}
```

## Pricing

This Actor uses **your** API keys. Costs depend on the external APIs you configure. With no keys, it uses DuckDuckGo (free, rate-limited).

## GitHub

Source code: [github.com/eduardofierroduque-sudo/spia](https://github.com/eduardofierroduque-sudo/spia)
