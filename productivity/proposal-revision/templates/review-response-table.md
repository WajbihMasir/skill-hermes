# Starter tables for a proposal revision

Copy into the revised document and fill. Keep the language of the document
(formal Bahasa Indonesia in this user's case).

## Response to review (closes the revision)

```markdown
# Lampiran A — Respon terhadap Catatan Review

| # | Catatan | Tindakan |
|---|---|---|
| 1 | <reviewer point, verbatim or closely paraphrased> | <what changed + where: "§5 Ruang Lingkup: dipangkas ke vertical slice; X/Y/Z → Should Have"> |
| 2 | | |
```

Rules: one row per numbered reviewer point, no skipping; the Tindakan cell names
the section that changed so the reviewer can jump straight to it; if a point was
only partially addressed, say which part is deferred and why.

## Threat model (STRIDE + status)

```markdown
## <n>. Keamanan: Threat Model & Keputusan Desain

### Metodologi
Analisis STRIDE terhadap aset kritis: <list assets>. Setiap ancaman dipetakan ke
kontrol yang sudah diimplementasikan dan diuji (<N> test otomatis).

| Ancaman | Skenario | Mitigasi | Status |
|---|---|---|---|
| **Spoofing** | <credential/token theft scenario> | <cookie/token controls, hashing> | ✅ Teruji |
| **Tampering** | <audit-log edit, lost update> | <append-only trigger, OCC version check> | ✅ Teruji |
| **Repudiation** | <actor denies action> | <audit fields: actor, before/after, IP, UA, ts> | ✅ Teruji |
| **Information Disclosure** | <internal data on public page, evidence leak> | <hardcoded filters, field allowlist, private bucket, short-lived presigned URL> | ✅ Teruji |
| **Denial of Service** | <oversized/malicious upload, endpoint spam> | <size cap, magic-byte validation> | ⚠️ Sebagian |
| **Elevation of Privilege** | <self-review, out-of-role action> | <per-route RBAC, SoD 403> | ✅ Teruji |
```

Status vocabulary — keep it honest:

- `✅ Teruji` — a test exists and passes; name the suite.
- `⚠️ Sebagian` — partially covered; say what is missing.
- `Roadmap` — designed but not built.

Also required in this section: **allowlist of fields** permitted on any
unauthenticated page (and an explicit "dilarang tampil" list), the evidence
upload risk (personal data in screenshots) with a retention policy, and the
authentication decision (local accounts vs SSO, token lifetimes, roadmap).

## Success metrics (baseline method + target)

```markdown
| # | Metrik | Baseline (cara ukur di AS-IS) | Target | Verifikasi |
|---|---|---|---|---|
| 1 | <metric> | <wawancara / observasi / hitung: berapa ...> | <number + unit> | <how it is checked> |
```

Never invent the baseline number — the cell names the measurement procedure and
the figure is collected during the AS-IS phase.

## Timeline & deliverables

```markdown
| Tahap | Aktivitas | Durasi | Deliverable |
|---|---|---|---|
| 1. Discovery | <activities> | 1 minggu | <artifact> |

**Total: ± N minggu** (sesuaikan dengan durasi magang aktual).
```

The total line is mandatory — a list of phases without a total cannot be judged
for feasibility. Follow with a risks table (Risiko | Dampak | Probabilitas |
Mitigasi) and an empty sign-off table (Nama | Peran | Tanggal | Bentuk Bukti).
