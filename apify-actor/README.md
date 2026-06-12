# SPIA — Personal Privacy Auditor

**Scan emails, usernames, names & phones across 60+ sources.** Uncover where your personal data is exposed on the surface web, deep web, and dark web.

---

## Features

- **60+ data sources** — Social media, data brokers, breach databases, paste sites, dark web engines
- **Privacy score** — 0-100 rating with categorized exposure breakdown
- **Breach check** — Have I Been Pwned, Dehashed, Collection #1-5, 30+ known breaches
- **Dark web scan** — Ahmia, Tor66, DarkSearch, OnionLand gateways
- **Actionable report** — Personalized recommendations to reduce exposure
- **BYO API keys** — Bring your own SerpAPI, HIBP, and Dehashed keys for deeper results

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✓ | Email, username, full name, or phone |
| `queryType` | enum | — | `auto`, `email`, `username`, `name`, `phone` (default: auto) |
| `serpapiKey` | string | — | SerpAPI key for real Google results |
| `hibpApiKey` | string | — | HIBP key for breach database access |

## Output Example

```json
{
  "query": "user@example.com",
  "query_type": "email",
  "privacy_score": 34,
  "total_exposures": 12,
  "categories": { "breach": 3, "social": 5, "databroker": 4 },
  "exposures": [
    {
      "category": "breach",
      "label": "Adobe 2013",
      "detail": "Email found in 1 security breach",
      "url": "https://haveibeenpwned.com/account/user@example.com",
      "risk_level": "high"
    }
  ],
  "recommendations": [
    "Change your passwords immediately. Use a password manager.",
    "Enable 2FA on all accounts where your email appears compromised."
  ]
}
```

## Try It

1. Run with just a query: `"query": "user@example.com"`
2. Add a SerpAPI key for real Google results
3. Add a HIBP key for breach database access

## Source Code

[github.com/eduardofierroduque-sudo/spia](https://github.com/eduardofierroduque-sudo/spia)
