# Vulnerability Classes That Need No Account

When a target is sales-gated, KYC-walled, or otherwise unreachable without
credentials you cannot obtain, the engagement is not over. A real subset of
reportable bugs is detectable **unauthenticated**: you send a request, the server
volunteers the misconfiguration in a response header or an exposed file, and
nothing is written.

Run these before reporting that a target is unusable. They are also the correct
first pass on ANY target — a hit here is found in minutes and costs nothing.

---

## The discipline that makes this legitimate

1. **Fixed short list, never a wordlist.** Twenty well-known paths is a check; ten
   thousand is a scanner. On a program that restricts automated testing, turning
   the list into a wordlist converts a permitted check into a program violation.
   Write the constraint into the tool so a later edit cannot quietly break it.
2. **GET only. No POST, no mutation, no authentication attempt.** A GET that
   returns a file is proof; a POST that writes data is damage. Presence of an
   admin route is a datum; probing its auth is a different activity.
3. **Only check hosts that answered the reachability probe.** Re-probing dead
   hosts wastes the budget and inflates the request count for nothing.
4. **Gate-check every URL, then sleep from the scope's rate limit.** Same rules as
   the reachability probe.

---

## Class 1 — CORS misconfiguration

Send a GET with `Origin: https://<an-origin-you-clearly-do-not-own>` and read
`Access-Control-Allow-Origin` (ACAO) plus `Access-Control-Allow-Credentials`
(ACAC). Pick an obviously foreign origin so a reflection is unambiguous.

| Observation | Verdict | Why |
|---|---|---|
| ACAO reflects the attacker origin **and** ACAC is `true` | **CRITICAL** | Any site can read the victim's authenticated responses |
| ACAO reflects the attacker origin, ACAC absent | **HIGH** | Data leak for non-credentialed endpoints |
| ACAO is `null` and the server accepts it | **MEDIUM** | Reachable from a sandboxed iframe or a `data:` URL |
| ACAO is `*` **and** ACAC is `true` | **HIGH** (signal) | Browsers block this combination, but it shows intent |
| ACAO is `*`, no credentials | **INFO — not a finding** | Most of the public internet does this |

**A wildcard without credentials is not a finding.** Reporting it burns a
triager's time and earns a not-applicable, which costs reputation. Only escalate a
wildcard when the endpoint demonstrably returns user-specific data.

Probe `null` as a second pass only when the first probe returned no ACAO at all —
otherwise you pay two requests per endpoint to learn nothing new.

---

## Class 2 — exposed configuration, VCS, and backup files

These are findings on presence alone. Keep the list small and specific:

| Group | Paths |
|---|---|
| Version control | `/.git/config`, `/.git/HEAD`, `/.svn/entries` |
| Environment / config | `/.env`, `/.env.local`, `/config.json`, `/application.yml`, `/WEB-INF/web.xml`, `/META-INF/MANIFEST.MF` |
| Backups / dumps | `/backup.zip`, `/backup.tar.gz`, `/db.sql`, `/dump.sql` |
| Spring actuator | `/actuator`, `/actuator/health`, `/actuator/env` |
| Directory listing | `/uploads/`, `/files/`, `/static/`, `/assets/` |
| API docs | `/openapi.json`, `/swagger.json`, `/swagger-ui.html`, `/v3/api-docs` |

Separate **critical** paths (a leak is the finding) from **informational** ones
(API docs are often intended). Collapsing the two produces a report full of
non-issues.

**A 200 is not automatically a hit.** Check for a CDN/WAF interstitial — a
Cloudflare challenge page is HTML, returns 200 on some configurations, and is not
an exposed file. Require a real body over a small size threshold and reject
challenge pages explicitly.

---

## Class 3 — worth a look, rarely eligible alone

- **Security headers** (missing CSP, HSTS, `X-Frame-Options`): almost universally
  listed as an explicit exclusion. Do not report these.
- **TLS/cipher configuration**: same. Often excluded by name.
- **Server/framework version banners**: informational; only a finding with a
  demonstrated exploit.
- **Directory listing on a static asset path**: usually intended.

Read the program's exclusion list before spending requests on this class.

---

## Reporting a negative result

Say exactly what was checked and what a negative means:

> No exposed configuration, VCS, or backup file was found. That is a NEGATIVE
> result, not a clean bill of health: it means this short list was not exposed,
> on these hosts, at this time.

Do not write "the target is secure". The check covers a fixed list of paths on a
fixed set of hosts at one moment; the absence of a hit carries no information
about the rest of the surface. Persist the raw results (status, length, content
type per path) so the negative is auditable rather than asserted.
