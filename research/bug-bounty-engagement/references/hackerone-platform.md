# HackerOne Platform Mechanics

Depth reference for `bug-bounty-engagement`. Numbers and rules change — verify on
the platform before relying on any specific value.

---

## Reputation

A profile starts at a base value and moves with each report's terminal state.

| Outcome | Effect |
|---|---|
| Resolved / Triaged | **gain** |
| Duplicate of a report that was already resolved, filed **before** it went public | small gain |
| Informative / self-closed | no change |
| **Not Applicable** | **loss** |
| Duplicate of a resolved report filed **after** it went public | **loss** |
| Duplicate of an N/A report | **loss** |
| **Spam** | **largest loss** (about double N/A) |

Reputation gates private invitations and caps how many reports you may submit in a
period. Duplicate chains stop affecting reputation after the third link.

Bounty size also feeds reputation, scaled by deviation from the program's mean.

**The operating consequence:** a loss is comparable in magnitude to a gain, so two
careless reports outweigh one good one. Volume without validation is
account-destroying.

---

## Report lifecycle

```
New -> Pending Program Review -> Triaged -> Resolved
 |                                  |
 |                                  +-> Retesting -> Resolved
 +-> Needs More Info --(30 days)--> Informative (no reputation change)
 +-> Closed: Resolved / Informative / Duplicate / N-A / Spam
```

`Triaged` means validated AND reproducible — a human followed the steps and saw
the impact. `Needs More Info` auto-closes as Informative after ~30 days **without**
a reputation penalty, so an incomplete report is a slow loss rather than a fast one.

---

## Severity is required

Severity must be selected for bug bounty, vulnerability disclosure, and challenge
programs (programs may opt out). Ratings: None / Low / Medium / High / Critical.

Supported calculation methods, chosen **per program**:

| Method | Note |
|---|---|
| CVSS 3.1 | official standard |
| CVSS 3.0 | platform's custom implementation |
| CVSS 4.0 | official standard; newer programs increasingly use it |
| Manual | program defines its own scheme |

A tool that only emits one version cannot serve programs requiring another.

---

## Structured scope

Asset types a program can define:

| Type | Example |
|---|---|
| Domain | `www.example.com` |
| **Wildcard** | `*.example.com` |
| URL | `www.example.com/app1` |
| CIDR | `172.200.0.0/16`, `2001:db8::/48` |
| iOS: App Store / Testflight / .ipa | `com.domain.myapp` |
| Android: Play Store / .apk | `com.domain.myapp` |
| Windows: Microsoft Store | store id |
| Source code | repository URL |
| Executable | packaged binary |
| Hardware / IoT | model number |
| AI Model | model identifier |
| Other | — |

Each asset carries **independent** flags:

- `eligible_for_submission` — may you file against it at all?
- `eligible_for_bounty` — will it be paid?
- `instruction` — asset-specific rules shown on the report form
- `max_severity` — the cap for that asset

**Keep the two eligibility flags separate.** Collapsing them into one "in scope"
boolean produces a scope that maps fine and pays nothing.

A URL asset's **path is part of the authorization boundary**: scoping
`www.example.com/app1` does not authorize `/app2`. A flat global path allow-list
cannot express "only `/api` on host X, all paths on host Y" — see
`audit-robustness-probes` for the leak that causes.

---

## Pulling the public directory

The directory pages are client-rendered, and `.json` variants return HTTP 406.
The **GraphQL endpoint is public** and is the reliable way to enumerate programs.

```bash
curl -sL --max-time 45 -X POST \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  --data-binary '{"query":"{ teams(first:5) { edges { node { handle name } } } }"}' \
  https://hackerone.com/graphql
```

**Field names are snake_case**, and the error messages name the correct spelling
(`Did you mean submission_state?`). When a field is unknown, introspect rather
than guess:

```graphql
{ __type(name: "Team") { fields { name } } }
```

That is how you discover fields such as `offers_bounties`, `submission_state`,
`resolved_report_count`, `reports_received_last_90_days`,
`average_bounty_lower_amount`, `structured_scopes`, and `structured_scope_asset_types`.

**Connection fields need sub-selections.** A field returning a connection (e.g.
`structured_scopes`, `submission_requirements`) errors with "Field must have
selections" if requested bare — you must select `edges { node { ... } }`.

Useful filters for a target shortlist:

```graphql
query Dir($n: Int!, $after: String) {
  teams(first: $n, after: $after,
        where: {submission_state: {_eq: open}, offers_bounties: {_eq: true}}) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      handle name resolved_report_count reports_received_last_90_days
      average_bounty_lower_amount average_bounty_upper_amount
      structured_scopes(first: 100) {
        edges { node { asset_type asset_identifier
                       eligible_for_bounty eligible_for_submission
                       instruction max_severity } }
      }
    } }
  }
}
```

Paginate with `pageInfo.endCursor` / `hasNextPage`. A few hundred programs is a
few requests.

Read a single program's policy text with:

```graphql
query P($h: String!) { team(handle: $h) { handle name policy scope_description } }
```

`policy` is the field to grep for the automation keyword families.

---

## Policy keyword families

Scan the `policy` text for these. The middle column is what decides the bucket.

| Family | Phrases |
|---|---|
| Automation | "automated tools or scanners", "automatic security scanners", "scripting or other automation" |
| Validation requirement | "without validation", "without real impact", "without proof of exploitability", "based only on results from automated", "not detailed enough" |
| Prohibited activity | "denial of service", "DoS", "brute force", "social engineering", "physical" |
| Scope exclusions | "out of scope", "not eligible", "excluded" |
| Rate expectations | "rate limit", "recurring and/or scheduled scans" |

A policy that mentions automation **with** a validation qualifier is CONDITIONAL,
not forbidden. Read the qualifier before concluding.

---

## API access (for scope ingestion)

Base `https://api.hackerone.com/v1/`, **HTTP Basic auth** with
`<api_username>:<api_token>` — the username is **not** an email address.

| Endpoint | Use |
|---|---|
| `GET /hackers/programs` | programs + structured scopes |
| `GET /hackers/programs/{handle}/structured_scopes` | one program's scope |
| `GET /hackers/hacktivity` | **disclosed reports** — the duplicate-check source |
| `GET /hackers/me/reports` | your own reports — outcome tracking |

Documented rate limits: reads ~600/min (report pages ~300/min), writes 25 per 20
seconds.

Responses are JSON:API shaped: `{"data": [...], "links": {"next": ...}}`.
**Follow `links.next` verbatim** — re-parsing its query string and re-encoding it
double-encodes the page cursor and silently repeats page 1 forever. See
`audit-robustness-probes` for the exact failure signature.

`hacktivity` takes a Lucene-style `queryString`, filterable by `severity_rating`,
`asset_type`, `substate`, `cwe`, `cve_ids`, `reporter`, `team`,
`total_awarded_amount`, `disclosed_at`, `has_collaboration`, `disclosed`.
That is how you check duplicate risk before writing a report.

Store the token in the environment, never in a config file:

```bash
export HERMES_HUNTER_H1_API_USERNAME="..."
export HERMES_HUNTER_H1_API_TOKEN="..."
```

---

## Platform-level rules that sit on top of program policy

The platform's own code of conduct applies everywhere, regardless of what a
program allows:

- AI-assisted research is permitted when used responsibly; the expectation is a
  **valid, reproducible report with demonstrated impact**, not volume.
- Submissions that are duplicates, unverifiable, or lacking depth are what get
  filtered — so those three failure modes are the engineering targets.
- Identity verification gates participation.
- One account per person; account sharing is prohibited.
- Public disclosure only after the coordinated-disclosure window closes.

---

## Source note

Platform pages may block automated extraction (403) or require login. When that
happens, the public GraphQL endpoint above is the working alternative for
program, scope, and policy data. Quote policy language you actually read, and
flag anything you could not retrieve rather than paraphrasing from memory.
