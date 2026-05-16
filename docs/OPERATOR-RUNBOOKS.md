# Centinel Engine Operator Runbooks

**ES: Manuales Operativos para Centinel Engine**

Emergency procedures and daily operations for election-night witness operators.

**ES: Procedimientos de emergencia y operaciones diarias para operadores de testigos en noche electoral.**

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Election Night](#election-night)
3. [Failover & Recovery](#failover--recovery)
4. [Troubleshooting](#troubleshooting)
5. [Post-Election](#post-election)

---

## Daily Operations

### Health Check

**Run every 6 hours (or continuously):**

```bash
centinel status
```

**Expected output:**
```
Status: OK
  Last snapshot: 2026-05-16T12:00:00Z (25 minutes ago)
  Chain length: 156
  Merkle root: aaaa...aaaa
  Disk usage: 2.3 GB / 50 GB
  Memory: 450 MB / 8 GB
```

**If status is RED (any failure):**
→ Go to [Troubleshooting](#troubleshooting)

### Snapshot Capture (Automated)

Snapshots run automatically on schedule (e.g., every 5 minutes). To capture manually:

```bash
centinel snapshot
```

**Output:**
```
Snapshot #157 created:
  Timestamp: 2026-05-16T12:05:30Z
  Data size: 145 KB
  Hash: bbbb...bbbb
  Previous hash: aaaa...aaaa
  Chained: ✓
```

**File created:** `hashes/<source>/snapshot_00157.sha256`

### Weekly Checkpoint

**Every Sunday at 00:00 UTC:**

```bash
centinel checkpoint --create
```

**Output:**
```
Checkpoint created:
  Chain length: 892
  Merkle root: cccc...cccc
  First hash: hash_0
  Last hash: hash_891
  Signed: ✓
  OpenTimestamps proof submitted: ✓ (Bitcoin TX: abc...def)
```

**File created:**
- `hashes/transparency/checkpoint-2026-05-16T00-00-00.json`
- `hashes/mirrors/checkpoint-2026-05-16T00-00-00.json` (mirror format for git)

**Then push to mirrors:**

```bash
git -C hashes/mirrors add checkpoint-2026-05-16T00-00-00.json
git -C hashes/mirrors commit -m "Weekly checkpoint: 892 snapshots"
git -C hashes/mirrors push origin main
```

---

## Election Night

### 18:00 (6 PM) — Pre-Election Setup

**Checklist:**
- [ ] All systems green (`centinel status`)
- [ ] Disk has >10 GB free
- [ ] Network connectivity stable (test: `centinel diagnose`)
- [ ] Backup system online (S3, B2, etc.)
- [ ] Witness publicly accessible (test from outside network)
- [ ] Testigos hermanos (sibling witnesses) are reachable
- [ ] All 3 mirror repos (git, OEA, NDI) are writable

**Commands:**
```bash
centinel status
centinel diagnose
df -h /hashes
curl -s https://witness.example.com/api/health
```

### 19:00 (7 PM) — Polls Close, Data Capture Begins

**System automatically:**
- Polls source every 5 minutes (or as configured)
- Creates snapshot per poll
- Verifies chain integrity
- Logs anomalies

**Operator responsibilities:**
- [ ] Monitor Slack/email for alerts
- [ ] Check anomaly log every 30 minutes: `tail -20 hashes/attack_log.jsonl`
- [ ] If anomaly flagged: review via web verifier, document finding

**Check anomalies:**
```bash
# Last 20 anomaly events
tail -20 hashes/attack_log.jsonl | grep -i anomaly

# Or, if API is running:
curl -s https://localhost:8000/audit/anomalies?from=0&to=500 | jq .
```

### 22:00 (10 PM) — Mid-Election Checkpoint

Create a checkpoint every ~3–4 hours during elections:

```bash
centinel checkpoint --create
git -C hashes/mirrors add checkpoint-*.json
git -C hashes/mirrors commit -m "Mid-election checkpoint: $(date -u +'%H:%M UTC')"
git -C hashes/mirrors push origin main
```

**Log the push:**
```bash
echo "Checkpoint pushed at $(date -u +'%Y-%m-%d %H:%M:%S UTC') by $USER" >> hashes/mirrors/PUSH_LOG.txt
git -C hashes/mirrors add PUSH_LOG.txt && git -C hashes/mirrors commit -m "Log push" && git -C hashes/mirrors push origin main
```

### 23:30 (11:30 PM) — Final Checkpoint

When source declares proclamation closed:

```bash
# Final capture
centinel snapshot

# Final checkpoint
centinel checkpoint --create --final

# Sign and anchor
git -C hashes/mirrors add checkpoint-*.json PUSH_LOG.txt
git -C hashes/mirrors commit -m "Final election-night checkpoint"
git -C hashes/mirrors push origin main
```

---

## Failover & Recovery

### Scenario 1: Network Blip (Source Unreachable)

**Symptom:** `Last snapshot: 15 minutes ago` (older than poll frequency)

**Action:**
1. Check connectivity:
   ```bash
   centinel diagnose
   ```
2. If DNS/TLS error: wait 2 minutes, retry
3. If persistent: alert network ops, switch to mirror mode (if configured)

**Mirror mode:**
```bash
# Use alternative data source (if available)
centinel snapshot --source-override=mirror-url
```

### Scenario 2: Disk Full

**Symptom:** `centinel status` shows RED, "No space left"

**Action:**
1. Check usage:
   ```bash
   du -sh hashes/*
   ls -lhS hashes/snapshots/ | head  # Largest snapshots
   ```
2. Archive old data:
   ```bash
   tar -czf hashes/archive/snapshots-2026-05-01-to-15.tar.gz \
     hashes/snapshots/snapshot_{001..500}.json
   rm hashes/snapshots/snapshot_{001..500}.json  # After archive verified
   ```
3. Resume:
   ```bash
   centinel snapshot
   ```

### Scenario 3: Merkle Root Divergence (Sibling Witness Mismatch)

**Symptom:** Your merkle root ≠ sibling witness merkle root

**This is CRITICAL: do not ignore.**

**Action:**
1. Pull latest checkpoints from all mirrors:
   ```bash
   git -C hashes/mirrors pull origin main
   ```
2. Recompute your local Merkle root:
   ```bash
   centinel verify --merkle-only
   ```
3. Compare with siblings:
   ```bash
   # Your root
   cat hashes/transparency/checkpoint-*.json | jq .merkle_root | tail -1
   
   # Sibling roots
   curl -s https://sibling-witness-1.example.com/api/checkpoint | jq .merkle_root
   curl -s https://sibling-witness-2.example.com/api/checkpoint | jq .merkle_root
   ```
4. If yours differs:
   - **DO NOT** overwrite. This is forensic evidence of tampering.
   - Log divergence with exact time:
     ```bash
     echo "Merkle divergence detected at $(date -u +'%Y-%m-%d %H:%M:%S UTC')" >> hashes/DIVERGENCE_LOG.txt
     echo "My root: $(cat hashes/transparency/checkpoint-*.json | jq -r .merkle_root | tail -1)" >> hashes/DIVERGENCE_LOG.txt
     ```
   - **Alert auditors immediately** (email, Slack)
   - **Preserve all snapshots** (do not delete)

### Scenario 4: Operator Station Down (Physical/Hardware Failure)

**If this witness dies:**

**Sibling witnesses:**
1. Continue capturing independently
2. Each has Merkle root: if any 2 agree, consensus is established
3. If all 3 differ: escalate to electoral authority (forensic evidence)

**After recovery:**
1. Restore witness from backups
2. Compare your restored state to siblings' published checkpoints
3. If mismatch: pull sibling data, audit divergence

**Backup restore:**
```bash
# Restore from S3 / B2
s3cmd get s3://centinel-backups/hashes.tar.gz.encrypted /tmp/
gpg --decrypt-file /tmp/hashes.tar.gz.encrypted | tar -xz -C hashes/
```

---

## Troubleshooting

### "Last snapshot is very old"

```bash
# Check logs
tail -50 centinel.log | grep -E "ERROR|snapshot"

# Manually trigger
centinel snapshot

# Check if it succeeds
centinel status
```

### "Chain is broken"

```bash
# Verify chain integrity
centinel verify --chain

# Expected: "Chain valid: 156/156 links"
# If broken: identifies exact index where break occurs
```

### "Merkle root not computing"

```bash
# Check snapshot file count
ls -1 hashes/*/snapshot_*.json | wc -l

# Compute manually
centinel verify --merkle-only

# Check for corrupted JSON
find hashes -name "*.json" -exec python3 -m json.tool {} \; > /dev/null 2>&1 | grep -B1 "error"
```

### "API not responding"

```bash
# Check if running
ps aux | grep centinel

# Restart
systemctl restart centinel  # (or your process manager)

# Check logs
journalctl -u centinel -n 50 --no-pager
```

---

## Post-Election

### Election Results Confirmed (Usually 24–48 Hours After Close)

**Checkpoints locked in (no new updates):**

```bash
# Final verification
centinel verify --full

# Expected: "All checks passed"
```

**Archive the election:**

```bash
# Tar all data
tar -czf /archive/election-2026-05.tar.gz hashes/ logs/ reports/

# Copy to cold storage (offline drive / cloud)
cp /archive/election-2026-05.tar.gz /mnt/cold-storage/
s3cmd put /archive/election-2026-05.tar.gz s3://centinel-archives/
```

**Publish final audit report:**

```bash
# Generate summary
centinel report --election-2026-05 > reports/FINAL-REPORT-2026-05.md

# Push to GitHub (public)
git add reports/FINAL-REPORT-2026-05.md
git commit -m "Final audit report: Honduras 2026 election"
git push origin main
```

---

## Contact & Escalation

**If critical issue:**

1. **Level 1 (Self):** Check runbook above, restart systemd service
2. **Level 2 (Sibling Witness Operators):** Compare roots, audit divergence
3. **Level 3 (Electoral Authority):** Report forensic findings
4. **Level 4 (Media/International Observers):** Data is published; let audit speak

**Key contacts:**
- Sibling Witness Ops: `witness-ops@centinel.example.com`
- Electoral Authority: `cne-audit@tse.hn.gov`
- Auditors: `upnfm@upnfm.hn`, `ndi@ndi.org`

---

## Operational Principles

1. **Never delete data** — even if "corrupted," it's forensic evidence
2. **Always log** — every action, every alert, every manual command
3. **Trust siblings, not self** — Merkle divergence is YOUR evidence of attack, not proof you're right
4. **Keep running** — if one witness dies, others continue; system is federated
5. **Publish early and often** — checkpoints pushed to git = immutable record

---

**Last Updated:** May 2026  
**Maintainer:** Centinel Engine Team
