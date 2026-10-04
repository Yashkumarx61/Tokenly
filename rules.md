# Coding Standards & AI Guidelines — Tokenly

## 1. Strict Multi-Tenant Data Isolation
- **Rule:** Every database query, insert, update, or delete MUST explicitly filter by `business_id = current_user.id`.
- **Enforcement:** Never execute `MenuItem.query.get(id)` directly without checking `business_id`. Always query `MenuItem.query.filter_by(id=id, business_id=current_user.id).first()`.

---

## 2. Server-Side Financial Math & Price Verification
- **Rule:** Never trust client-submitted cart prices or totals.
- **Enforcement:** The frontend sends item IDs, portion strings (`'half'` or `'full'`), and quantities. The backend re-fetches authoritative item prices from the database and calculates line totals, subtotals, tax, and grand totals using Python's decimal/float precision before writing to the database.

---

## 3. Concurrency & Race Condition Prevention
- **Rule:** Token generation must be atomic to prevent duplicate token numbers during peak-hour multi-terminal rushes.
- **Enforcement:** Use database transaction locking (`with_for_update()`) on `DailyTokenSequence` for sequence updates.

---

## 4. Input Sanitization & SQL Injection Defense
- **Rule:** Prevent XSS and SQL injection across all inputs.
- **Enforcement:**
  - Use SQLAlchemy ORM parameterized queries exclusively.
  - Use Flask-WTF forms for registration, login, and item creation.
  - Store strings clean of malicious script tags (`strip()`, `escape()`).
  - Use dataset attributes (`data-id`, `data-name`, `data-portion`, `data-price`) in Jinja2 HTML templates for inline JavaScript event handlers to avoid quote-escaping syntax errors.

---

## 5. Security & Session Integrity
- **Rule:** Passwords must be hashed using strong one-way hashing (`scrypt`/`bcrypt`).
- **Enforcement:**
  - Use `generate_password_hash` and `check_password_hash` from `werkzeug.security`.
  - Secure session cookies using `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE='Lax'`.
  - Apply `@login_required` on all protected POS, admin, and history routes.

---

## 6. Error Handling & Professional Logging
- **Rule:** Do not leak sensitive stack traces or environment keys to end users on error pages.
- **Enforcement:** Implement centralized error handlers for `404` and `500` HTTP statuses returning user-friendly HTML templates. Log full tracebacks internally via `app.logger.error`.

---

## 7. Fast Touch Terminal UX
- **Rule:** POS touch interactions must be instant with zero unnecessary confirmation modals.
- **Enforcement:**
  - Minimum touch target height of 38px–42px for iOS Safari and touch terminals.
  - Tapping **"Generate Token & Bill"** immediately triggers print and resets cart state in under 1 second.
