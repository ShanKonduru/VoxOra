---
description: "Use when writing authentication, JWT handling, token storage, password hashing, input validation, rate limiting, or any security-sensitive code. Covers token hygiene, algorithm confusion attack prevention, input sanitization, and refresh token patterns."
---

# Security Patterns

## JWT — Non-Negotiable Rules

**1. Never put tokens in URL query parameters.** They appear in server logs, browser history, and `Referer` headers.

```python
# ✅ Correct — token in Authorization header or request body
headers={"Authorization": f"Bearer {token}"}

# ❌ Never — token in URL
GET /api/admin/stats?token=eyJ...
```

**2. Reject `alg: none` explicitly before decoding.**

```python
# ✅ Correct — check unverified header first
unverified = jwt.get_unverified_header(token)
if unverified.get("alg", "").lower() == "none":
    raise HTTPException(status_code=401, detail="Invalid token algorithm")
decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
```

**3. Store only the SHA-256 hash of refresh tokens in the database.**

```python
import hashlib

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
```

**4. Refresh tokens travel as httpOnly cookies only.** Access tokens travel as Bearer headers only.

```python
# ✅ Correct — set refresh as httpOnly cookie
response.set_cookie(
    key="refresh_token", value=raw_token,
    httponly=True, secure=True, samesite="strict", max_age=604800
)
```

## Password Hashing

Use `passlib[bcrypt]` with `CryptContext`. Never use `md5`, `sha1`, or plain `sha256` for passwords.

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

## Input Sanitization

All user-supplied text must pass through `InputSanitizer.check(text)` **at system boundaries** (API route handlers or WebSocket receive) — not inside services.

`SanitizationResult.is_safe == False` must terminate the request immediately.

Sanitizer enforces (in order):
1. `len(text) > settings.input_max_length` → block
2. Unicode NFKC normalization (defeats look-alike character attacks)
3. 20+ compiled regex patterns (SQL injection, shell injection, SSRF, path traversal, XSS, prompt injection)
4. Jailbreak keyword dictionary loaded from `backend/security/jailbreak_blocklist.txt`

**Never bypass the sanitizer** by calling AI services directly with raw user input.

## AI Prompt Security — Sandwiched Pattern

Always wrap survey context between prompt anchors. Never concatenate raw user input into AI prompts.

```python
# ✅ Correct — use PromptBuilder, never raw f-strings
system_prompt = PromptBuilder(survey, persona).build()

# ❌ Never
system_prompt = f"Survey: {survey.title}\nUser said: {user_input}"
```

## Rate Limiting

All write endpoints (`POST`, `PATCH`, `DELETE`) must carry a `@limiter.limit(...)` decorator.
Read endpoints that return sensitive data (e.g., session responses) must also be rate-limited.

```python
@router.post("/surveys")
@limiter.limit("20/minute")
async def create_survey(request: Request, ...):
```

## WebSocket Authentication

Session tokens for WebSocket must be sent as the **first text frame** after connection opens — never as a URL query parameter.

```js
// ✅ Correct — auth in first message
ws.onopen = () => ws.send(JSON.stringify({ session_token: token }))

// ❌ Never
new WebSocket(`wss://host/ws/session/123?token=${token}`)
```

## Security Headers (Nginx)

All production responses must include:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
