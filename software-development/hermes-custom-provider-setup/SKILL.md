---
name: hermes-custom-provider-setup
description: "Add custom LLM providers to Hermes Agent."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, custom-provider, llm]
    related_skills: [hermes-agent]
---

# Hermes Custom Provider Setup

## When to Use

- User wants to add a new LLM model from a custom/OpenAI-compatible endpoint
- User provides a base URL, API key, and model ID for a new provider
- A custom provider returns 401 despite correct alias config

## Procedure

1. **Add the model alias** via `hermes config set`:
   ```bash
   hermes config set model.aliases.<alias>.model <model-id>
   hermes config set model.aliases.<alias>.provider custom
   hermes config set model.aliases.<alias>.base_url <url>
   hermes config set model.aliases.<alias>.api_key <key>
   ```

2. **CRITICAL: Set top-level `model.base_url`** — the `custom` provider resolves `base_url` from the top-level `model.base_url`, NOT from the alias's own `base_url`. If the top-level value points elsewhere (e.g. `localhost`), the alias will hit the wrong server and return 401.
   ```bash
   hermes config set model.base_url <url>
   ```

3. **Set top-level `model.api_key`** (or `model.key_env`) — same resolution rule as `base_url`.
   ```bash
   hermes config set model.api_key <key>
   # OR use env var:
   hermes config set model.key_env <ENV_VAR_NAME>
   ```

4. **Verify** with a one-shot query:
   ```bash
   hermes chat --model <alias> -q "say hi"
   ```

5. **Restore default model** if needed:
   ```bash
   hermes config set model.default <original-default>
   ```

## Pitfalls

- **`provider: custom` ignores alias-level `base_url`** — it always resolves from top-level `model.base_url`. Setting `base_url` on the alias alone has no effect on which server is contacted. Always set both.
- **`api_key` on alias may be ignored** — same resolution as `base_url`. Set `model.api_key` or `model.key_env` at the top level.
- **Provider string shows `custom:local-(host)`** — this is derived from the top-level `base_url` host. If it shows the wrong host, the top-level `base_url` is wrong.
- **Env var approach is safer for keys** — put the key in `~/.hermes/.env` and reference via `model.key_env` to avoid storing plaintext in `config.yaml`.

## Verification

Always test with `hermes chat --model <alias> -q "test"` before reporting success. A 401 error with `provider: custom` almost always means the top-level `base_url` or `api_key` is wrong, not the alias config.
