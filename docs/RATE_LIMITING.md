# Rate Limiting — Research & Policy

## Overview

CENTINEL implements ethical rate limiting for scraping electoral authority websites.
This document describes the research-backed limits, the legal basis, and the
operational modes available.

## Research Summary (June 2025)

### CNE Honduras Infrastructure

| Component | Detail |
|-----------|--------|
| CDN/WAF on cne.hn | Cloudflare (NS: javon/sky.ns.cloudflare.com) |
| resultadosgenerales2025.cne.hn | NOT behind Cloudflare (IP: 27.126.241.124, APNIC range) |
| TREP Backend | Grupo ASD (Colombia), Red Hat OpenStack + Kubernetes |
| Contracted capacity | 200,000 queries/second |
| Election night reality | Collapsed at 57% of tally sheets, ~96 hour blackout |
| Published rate limits | **None** — CNE does not document API limits |
| robots.txt | Not accessible / not published |

### Industry Precedents for Electoral Scraping

| Organization | Scraping Frequency |
|-------------|-------------------|
| New York Times | Every 3-10 minutes per state |
| MinnPost | Every 3 minutes on election night |
| NPR | Every 15 minutes |
| Ohio Secretary of State | Updates every 3 minutes |

### Cloudflare Defaults

Cloudflare does **not** impose default rate limits on visitor traffic. Site operators
configure their own rules. Recommended thresholds from Cloudflare documentation:
- Login endpoints: 5 req/min
- API endpoints: 20 req/min
- General pages: 100 req/min

### Legal Basis

| Law / Precedent | What it says |
|----------------|-------------|
| Decreto 170-2006 (Honduras Transparency Law) | Art. 5, 13, 15, 20: public data must be accessible via "electronic means" |
| Van Buren v. US (2021, US Supreme Court) | Scraping public data does not violate the CFAA |
| hiQ v. LinkedIn (9th Circuit) | Accessing publicly available data is not "unauthorized access" |
| Sandvig v. Barr (2020) | Violating TOS alone cannot criminalize access |
| Honduras Penal Code Art. 398 | Only applies to "unauthorized" access — electoral data is public by law |

## Operational Modes

### Mode: Normal (between elections)

| Parameter | Value |
|-----------|-------|
| Capture interval | 10 minutes |
| Requests/hour | 240 |
| Min interval between requests | 6 seconds |
| Max burst | 5 |
| Jitter | 0-3.2 seconds |

### Mode: Electoral (election night / active counting)

| Parameter | Value |
|-----------|-------|
| Capture interval | 3 minutes |
| Requests/hour | 360 |
| Min interval between requests | 3 seconds |
| Max burst | 6 |
| Jitter | 1-5 seconds |

### Mode: Aggressive (blackout detected / critical data)

| Parameter | Value |
|-----------|-------|
| Capture interval | 1 minute |
| Requests/hour | 480 |
| Min interval between requests | 2 seconds |
| Max burst | 8 |
| Jitter | 2-8 seconds |

### Mode: Conservative (sensitive servers / post-election)

| Parameter | Value |
|-----------|-------|
| Capture interval | 30 minutes |
| Requests/hour | 120 |
| Min interval between requests | 10 seconds |
| Max burst | 3 |
| Jitter | 0.5-4 seconds |

## Hard Ceilings

CENTINEL enforces absolute ceilings that **no preset can exceed**:

| Ceiling | Value | Rationale |
|---------|-------|-----------|
| Max requests/hour | 480 (8/min) | Well below DDoS threshold (50+ req/sec) |
| Min interval | 2 seconds | Prevents burst patterns detectable by WAFs |
| Max burst | 8 | Limits concurrent token availability |

### Custom Mode

Only user-created "custom" presets can bypass these ceilings. When a user creates
a custom preset that exceeds the hard ceiling, CENTINEL:
1. Allows the configuration (operator assumes responsibility)
2. Logs a CRITICAL warning
3. Labels the mode as "custom" in all telemetry
4. Does NOT label it as a CENTINEL preset

This ensures that aggressive scraping beyond research-backed limits is always
an explicit operator decision, never a CENTINEL default.

## Red Lines (what CENTINEL never does)

- More than 10 req/sec sustained to a single endpoint
- Ignore 429/503 responses (always backs off)
- Use multiple IPs to evade rate limiting
- Continue scraping after an explicit cease-and-desist
- Circumvent CAPTCHAs or technical barriers

## Configuration

### YAML (`config/prod/rate_limiter.yaml`)

```yaml
active_mode: normal  # normal | electoral | aggressive | conservative | custom

hard_ceiling:
  max_requests_per_hour: 480
  min_interval_seconds: 2
  max_burst: 8

modes:
  normal:
    capacity: 5
    rate_interval_seconds: 10
    min_interval_seconds: 6
    max_interval_seconds: 12
    max_requests_per_hour: 240
    capture_interval_minutes: 10
  # ... (see file for all modes)
```

### Runtime switching

```python
from centinel_engine.rate_limiter import switch_mode

switch_mode("electoral")         # Switch to election night mode
switch_mode("aggressive")        # Switch to blackout/critical mode
switch_mode("custom", max_requests_per_hour=600)  # Custom (bypasses ceiling)
```

### /ops Panel

The admin panel at `/ops` exposes mode selection through the presets grid.
Factory presets enforce hard ceilings. Only user-saved custom presets can
exceed them.

## Ethical Compliance (3 Pillars)

### 1. Honest User-Agent

All requests use `Centinel-Engine/1.0 (+https://github.com/VectisDev/centinel)`.
No fake browser UAs (Chrome/Firefox/Safari). The User-Agent links to the open-source
project so any server admin can verify our mission.

Implementation: `centinel_engine/proxy_manager.py:USER_AGENT_POOL`

### 2. robots.txt Respect

Before each fetch, `urllib.robotparser` checks the target's robots.txt. Results
are cached for 1 hour per origin. Fail-open: a missing or broken robots.txt never
blocks data collection (the CNE does not currently publish one).

Implementation: `scripts/download_and_hash.py:_check_robots_allowed()`

### 3. Retry-After Respect

When the server sends a `Retry-After` header in a 429/503 response, the rate
limiter uses that value as the minimum wait time. The server's explicit directive
always takes priority over CENTINEL's internal backoff calculations.

Implementation: `src/centinel/downloader.py:_perform_request()` extracts the header,
`centinel_engine/rate_limiter.py:notify_response()` enforces it.

## Adaptive Behavior

Beyond the configured mode, the rate limiter automatically:
1. **Respects Retry-After**: Server-mandated wait times are honored as minimum delays
2. **Backs off on 429s**: 2+ responses in 5 minutes trigger conservative mode (10 min pause)
3. **Exponential backoff on failures**: Each consecutive failure doubles the wait
4. **Random jitter**: Every request adds 0-3.2s random delay to break timing patterns
5. **Per-source throttling**: A 429/503 from a specific endpoint throttles that source for 30 minutes
6. **robots.txt**: Checked before every fetch, cached 1h per origin

## Sources

- Cloudflare Rate Limiting: https://developers.cloudflare.com/waf/rate-limiting-rules/
- Cloudflare Bot Detection: https://developers.cloudflare.com/bots/concepts/bot-score/
- hiQ v. LinkedIn: https://blog.apify.com/hiq-v-linkedin/
- Van Buren v. US: https://en.wikipedia.org/wiki/Van_Buren_v._United_States
- Honduras Decreto 170-2006: http://www.sefin.gob.hn/wp-content/uploads/leyes/LeyDeTransparencia.pdf
- NYT Election Scraping: https://source.opennews.org/articles/elections-scraping/
- MinnPost Election API: https://github.com/MinnPost/election-night-api
- Cloudflare Athenian Project: https://www.cloudflare.com/athenian/guide/
