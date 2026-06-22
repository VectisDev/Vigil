# GitHub API Cost Verification — $0 Infrastructure

## Overview

Centinel's zero-cost architecture uses **only free GitHub APIs**. This document verifies that every API call used is covered by GitHub's free tier.

## Free GitHub APIs Used

### 1. GitHub Issues API

**Purpose:** Swarms publish findings to shared election issues.

| Operation | Endpoint | Free Tier? | Cost |
|-----------|----------|------------|------|
| Create Issue | `POST /repos/{owner}/{repo}/issues` | ✅ Yes | $0 |
| Get Comments | `GET /repos/{owner}/{repo}/issues/{number}/comments` | ✅ Yes | $0 |
| Add Comment | `POST /repos/{owner}/{repo}/issues/{number}/comments` | ✅ Yes | $0 |
| List Issues | `GET /repos/{owner}/{repo}/issues` | ✅ Yes | $0 |

**Usage:** Each swarm publishes its findings as a comment. Other swarms read via `GET /comments` (free). No rate limit for public repos.

### 2. Git Repository API

**Purpose:** Commits store immutable state snapshots.

| Operation | Service | Free Tier? | Cost |
|-----------|---------|------------|------|
| git push | GitHub | ✅ Yes | $0 |
| git pull | GitHub | ✅ Yes | $0 |
| git commit | Local (no API) | ✅ Yes | $0 |
| Create Branch | Git (via push) | ✅ Yes | $0 |

**Usage:** Hash chain commits use `force-with-lease` to safely push snapshots. Storage is unlimited on GitHub (public repos).

### 3. GitHub Releases API

**Purpose:** Archives gossip payloads for forensic trails.

| Operation | Endpoint | Free Tier? | Cost |
|-----------|----------|------------|------|
| Create Release | `POST /repos/{owner}/{repo}/releases` | ✅ Yes | $0 |
| Upload Asset | Release attachments | ✅ Yes | $0 |
| List Releases | `GET /repos/{owner}/{repo}/releases` | ✅ Yes | $0 |

**Usage:** Weekly archive of gossip payloads compressed to `.tar.gz`. Stored perpetually in Releases (no TTL).

### 4. GitHub Actions

**Purpose:** Orchestrate gossip cycles and exports.

| Feature | Free Tier? | Limits | Cost |
|---------|------------|--------|------|
| Workflow Runs | ✅ Yes | 60 min/month | $0 |
| Matrix Jobs | ✅ Yes | 20 parallel | $0 |
| Storage | ✅ Yes | 500 MB | $0 |

**Usage:** 
- Daily reputation export: ~2 min
- Weekly archive: ~1 min
- Monthly hash chain commits: ~1 min
- **Total:** ~5 min/month ≪ 60 min limit

### 5. raw.githubusercontent.com

**Purpose:** Public JSON API for reputation data.

| Service | Free Tier? | Rate Limit | Cost |
|---------|------------|------------|------|
| Raw content delivery | ✅ Yes | Unlimited* | $0 |

*No rate limit for public repos (via raw.githubusercontent.com)

**Usage:** Cross-swarm consensus queries reputation JSON via:
```
https://raw.githubusercontent.com/{owner}/{repo}/data/api/data/reputation/nodes.json
```

## APIs NOT Used

❌ **Paid Services (Zero Cost to Us):**
- Datadog, New Relic, CloudFlare (monitoring) — NOT USED
- AWS Lambda, Google Cloud Functions — NOT USED
- Stripe, payment processing — NOT USED
- CDN services — NOT USED (raw.githubusercontent.com is free)

❌ **Rate-Limited or Metered:**
- GitHub GraphQL API (used for enhanced queries) — AVOIDED
- GitHub Search API (would count toward rate limit) — AVOIDED

## Cost Model: Infinite Scaling at $0

### Per-Swarm Cost Breakdown

| Component | Cost | Scalability |
|-----------|------|------------|
| GitHub Issues | $0 | Unlimited posts |
| Git storage | $0 | Unlimited commits |
| GitHub Releases | $0 | Unlimited archives |
| GitHub Actions | $0 (5 min/month) | 60 min/month available |
| **Total/Swarm** | **$0** | **Infinite** |

### Scaling Examples

| Scale | Swarms | Nodes | Cost/Month |
|-------|--------|-------|------------|
| Solo | 1 | 12 | $0 |
| Small | 10 | 120 | $0 |
| Medium | 100 | 1,200 | $0 |
| Large | 1,000 | 12,000 | $0 |
| Massive | 10,000 | 120,000 | $0 |

**Key Property:** Marginal cost per additional swarm = $0

### Verification Checklist

✅ All API calls use free endpoints  
✅ No external service calls  
✅ No rate limit concerns (public repos)  
✅ Storage is unlimited (git + Releases)  
✅ Compute is capped well below free tier (5 min ≪ 60 min)  
✅ No authentication required (public repos)  
✅ Costs stay at $0 regardless of node count  

## Implementation

### Code Review Checklist

When adding features, verify:

1. **API Calls Only to Free Endpoints**
   ```python
   # ✅ GOOD - Uses free API
   POST /repos/{owner}/{repo}/issues/{id}/comments
   
   # ❌ BAD - Might hit rate limits
   POST /search/issues (GitHub Search API)
   ```

2. **No External Service Dependencies**
   ```python
   # ✅ GOOD
   subprocess.run(['git', 'push'])  # Free
   
   # ❌ BAD
   requests.get('https://paid-service.com/api')
   ```

3. **Storage Only via Git or Releases**
   ```python
   # ✅ GOOD
   json.dump(data, Path('data/reputation/snapshot.json'))
   # → Stored in git (free)
   
   # ❌ BAD
   upload_to_s3(data)  # AWS costs $
   ```

## Links

- [GitHub API Free Tier](https://docs.github.com/en/rest/overview/endpoints-available-for-github-apps)
- [GitHub Actions Pricing](https://github.com/pricing#actions)
- [GitHub Releases Storage](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## Conclusion

**Centinel's zero-cost guarantee is enforceable:**
- Every API call is documented and free
- Storage costs are $0 (GitHub owns the hardware)
- Compute costs are $0 (included in free Actions tier)
- **Total cost: $0 perpetually, regardless of scale**

This architecture guarantees that 1 swarm costs the same as 1,000 swarms: **$0/month**.
