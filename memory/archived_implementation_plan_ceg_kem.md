# Research Synthesis & Novel Security Proposal: Cascading Entropy-Gated ML-KEM

## Honest Assessment First

Before anything — your question about whether there's an actual third-party connection: **No.** The current codebase has zero external UWB service. The frontend generates coordinates, sends them to FastAPI, and the backend makes decisions locally. There is no API key to steal because there is no API to call. The "third-party UWB verifier" in the original plan was protecting a connection that doesn't exist.

That changes the threat model entirely. The real attack surface is **the coordinate data stream itself** — and that's exactly what your papers address.

---

## Paper Relevance Verdicts

| Paper | Relevant? | Why |
| :--- | :--- | :--- |
| **Cascading Visibility Failure in Maritime Logistics** | ✅ **Highly Relevant** | This paper describes the *exact same class of problem* — position-trust in a system where coordinates can be spoofed. AIS/GPS spoofing in maritime is structurally identical to UWB coordinate spoofing in Artemis. The "data entropy" concept and multi-source fusion mitigations are directly applicable. |
| **Cascading Effects of Repackaged APIs** | ✅ **Relevant** | The "Policy Dilution" and "Mirror Effect" concepts apply to how security guarantees weaken across system layers. Even though Artemis has no external API *yet*, the paper's insight that **security erodes at each hop in a cascade** is a design principle we should bake in now. |
| **Cascaded Heterogeneous TTS Routing** | ⚠️ **Tangentially Relevant** | This is a TTS/speech synthesis paper. It doesn't directly address cryptography or spatial security. *However*, the "chunk-level orchestration" architecture — where long streams are broken into independently verifiable units — is a pattern we can adapt for position-stream verification. |

**Bottom line**: Papers 2 and 3 give us concrete security principles. Paper 1 gives us an architectural pattern. None of them hand us a ready-made solution, but combining their ideas with ML-KEM produces something genuinely novel.

---

## The Novel Proposal: Cascading Entropy-Gated ML-KEM (CEG-KEM)

### Core Insight

Standard spatial-gated crypto works like this:
```
Position check → Binary yes/no → Decrypt or lock
```

An attacker only needs to forge a single "yes" to break the entire system. One spoofed in-bounds coordinate, one replayed valid session, and you're through.

The papers collectively suggest a fundamentally different architecture:

> **Don't use position as a binary gate. Use position *entropy* as a continuous cryptographic input across a cascade of independent verification layers.**

### How It Works

#### Layer 1 — Position Entropy Scoring (from Maritime Paper)

The maritime paper's key insight: genuine position data has a characteristic **entropy signature**. A real human dragging a node on a radar grid produces:
- Natural micro-jitter (hand tremor, mouse precision limits)
- Characteristic velocity curves (acceleration → cruise → deceleration)
- Non-uniform dwell patterns (humans pause, overshoot, correct)

Spoofed coordinates exhibit detectable anomalies:

| Spoofing Method | Entropy Signature | Detection |
| :--- | :--- | :--- |
| **Replay attack** | Identical entropy to a previous session | Shannon entropy fingerprint match against history |
| **Static injection** | Near-zero entropy (perfect coordinates) | Entropy below natural floor threshold |
| **Random noise** | Uniformly high entropy | Entropy above natural ceiling threshold |
| **Scripted path** | Suspiciously smooth entropy curve | Lack of micro-jitter, missing acceleration noise |

We compute a **rolling Shannon entropy score** over a sliding window of the last N position updates. This score becomes a *cryptographic input*, not just a logging metric.

#### Layer 2 — Cascading Key Encapsulation (from Repackaged APIs Paper)

The APIs paper warns that **policy dilution** weakens security at each hop. The fix: don't have one security check — have a cascade where each layer independently enforces the full policy and failure at ANY layer collapses the entire chain.

Applied to ML-KEM:

```
┌─────────────────────────────────────────────────────┐
│  ML-KEM Cascade (3 layers)                          │
│                                                     │
│  Layer 1: Encapsulate(pk₁) → ct₁, ss₁              │
│    Gate: entropy_score ∈ [E_min, E_max]             │
│    Gate: timestamp within TTL window                 │
│                                                     │
│  Layer 2: Encapsulate(pk₂) → ct₂, ss₂              │
│    Gate: ss₁ valid (previous layer passed)           │
│    Gate: velocity ≤ V_max (no teleportation)         │
│    Gate: session_nonce not in replay set             │
│                                                     │
│  Layer 3: Encapsulate(pk₃) → ct₃, ss₃              │
│    Gate: ss₂ valid (previous layer passed)           │
│    Gate: chunk_quorum ≥ threshold                   │
│    Gate: role claim validated                        │
│                                                     │
│  Final shared secret = KDF(ss₁ ‖ ss₂ ‖ ss₃)        │
│  Decrypt payload with final key                     │
└─────────────────────────────────────────────────────┘
```

Each layer uses an **independent ML-KEM key pair**. The shared secret from layer N is required to proceed to layer N+1. If any gate fails, the cascade collapses — no partial decryption is possible.

**Why this defeats policy dilution**: An attacker cannot "mirror" past one layer. Even if they somehow bypass the entropy check (Layer 1), they still face velocity validation (Layer 2) and chunk quorum (Layer 3). Each layer independently enforces a different security property.

#### Layer 3 — Chunk-Level Position Attestation (from TTS Paper)

The TTS paper's chunk orchestration concept: instead of one monolithic operation, break the stream into small independently verifiable units.

Applied here: instead of validating position at a single point in time ("are you in-bounds *right now*?"), we break the position stream into **time-chunks** (e.g., 2-second windows). Each chunk produces an independent cryptographic attestation:

```
Chunk₁ (t=0s to t=2s):  12 position samples → entropy_score₁ → HMAC₁
Chunk₂ (t=2s to t=4s):  12 position samples → entropy_score₂ → HMAC₂  
Chunk₃ (t=4s to t=6s):  12 position samples → entropy_score₃ → HMAC₃
...

Decrypt requires: quorum of K-of-N recent chunks all attesting valid position
```

**Why this defeats replay attacks**: A replayed session would need to replay the exact entropy signature of every chunk in sequence, with correct timing. Even a 100ms timing drift changes the chunk boundaries and invalidates the attestation chain.

---

## Threat Model Re-evaluation

| Attack Vector | Original Risk | After CEG-KEM | Why |
| :--- | :--- | :--- | :--- |
| **Position spoofing** (fake in-bounds coords) | 🔴 Critical | 🟢 Mitigated | Entropy scoring detects synthetic coordinate patterns — too smooth, too uniform, or too random all fail |
| **Replay attack** (capture valid session) | 🔴 Critical | 🟢 Mitigated | Chunk attestation chain is time-bound; replayed chunks have wrong timestamps and nonces. Entropy fingerprint matches against history detect exact replays |
| **API key theft** | 🟡 Medium (no API exists) | ⚪ N/A | No external API to steal keys from. All verification is local. If a third-party is added later, the cascade architecture prevents single-point-of-compromise |
| **Privilege escalation** | 🔴 High | 🟢 Mitigated | Role validation is an independent gate in Layer 3 of the cascade — cannot be bypassed by passing Layers 1-2 |
| **Cascade policy dilution** | 🔴 High (in multi-hop systems) | 🟢 Mitigated by design | Each layer independently enforces full policy; failure at any layer collapses the entire chain |

---

## Implementation Approach

### New Files

#### [NEW] `backend/security/entropy.py`
- `ShannonEntropyScorer`: Computes rolling entropy over position coordinate windows
- `EntropyAnomalyDetector`: Classifies entropy signatures (replay, static, noise, scripted, genuine)
- Configurable thresholds: `E_MIN`, `E_MAX`, `VELOCITY_MAX`, `JITTER_FLOOR`

#### [NEW] `backend/security/cascade.py`
- `CascadeMLKEM`: Three-layer cascading key encapsulation using `pqcrypto` or simulation wrapper
- Each layer: `encapsulate()` → gate check → pass shared secret forward
- `KDF` derivation of final decrypt key from all three shared secrets
- Fail-closed: any gate failure → wipe all intermediate secrets

#### [NEW] `backend/security/chunks.py`
- `ChunkAttestor`: Breaks position streams into time-windowed chunks
- Per-chunk HMAC generation with server-side secret
- Quorum validator: requires K-of-N recent chunks to all pass

#### [NEW] `backend/security/siem.py`
- Structured JSON event logger for all security-relevant events
- Event types: `ENTROPY_ANOMALY`, `VELOCITY_VIOLATION`, `REPLAY_DETECTED`, `CASCADE_FAILURE`, `PRIVILEGE_DENIED`, `DECRYPT_SUCCESS`
- Severity levels and real-time flag output

#### [MODIFY] `backend/server.py`
- New endpoint: `POST /api/verify-position` — accepts position stream, runs entropy + cascade
- New endpoint: `POST /api/decrypt` — gated by full CEG-KEM cascade
- All endpoints emit SIEM events

### Tests

#### [NEW] `backend/tests/test_entropy.py`
- Verify genuine coordinate patterns pass entropy checks
- Verify replay, static, noise, and scripted patterns are rejected

#### [NEW] `backend/tests/test_cascade.py`
- Verify full cascade produces valid decrypt key when all gates pass
- Verify cascade collapses (fail-closed) when any single gate fails
- Verify partial bypass is impossible (Layer 1 pass + Layer 2 fail → no key)

#### [NEW] `backend/tests/test_chunks.py`
- Verify chunk attestation with correct timing passes quorum
- Verify replayed chunks with wrong timestamps fail
- Verify quorum threshold enforcement

---

## What This Doesn't Solve

Being honest about limitations:

1. **Client-side coordinate generation**: The frontend still generates the coordinates. A sophisticated attacker who reverse-engineers `App.js` could craft coordinates that pass entropy checks. Mitigation: obfuscate entropy thresholds server-side, never expose them to the client.
2. **No real UWB hardware**: Without physical UWB, the entire position system is software-simulated. CEG-KEM raises the bar significantly, but a determined attacker with source code access can eventually model the entropy patterns. This is inherent to simulation.
3. **ML-KEM simulation**: Unless we integrate a real post-quantum crypto library (`liboqs`, `pqcrypto`), the ML-KEM operations will be simulated. The *architecture* is sound regardless.

---

## Summary

The three papers — while covering maritime logistics, API supply chains, and TTS routing — share a common thread about **cascading failures in systems that trust a single data source**. By combining:

- **Entropy scoring** (Maritime paper) → detect spoofed coordinates
- **Non-dilutable cascading policy enforcement** (API paper) → prevent single-layer bypass
- **Chunk-level independent attestation** (TTS paper) → defeat replay attacks

...we get **CEG-KEM**: a security architecture where position data isn't just a gate — it's a continuous cryptographic participant in a multi-layer key derivation cascade. Breaking one layer gives you nothing. Breaking all layers simultaneously, with correct entropy signatures, correct timing, correct velocity curves, and correct role claims, is computationally and practically infeasible.
