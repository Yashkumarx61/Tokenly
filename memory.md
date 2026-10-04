# Project Memory & Decisions Log — Tokenly

## 1. Key Architectural & Design Decisions

- **Multi-Tenant Isolation:**
  - Standardized on `business_id` as the tenant identifier across all database entities (`Category`, `MenuItem`, `Order`, `OrderItem`, `DailyTokenSequence`, `AuditLog`).
  - Added strict session checks and query filters in every blueprint route to guarantee zero cross-tenant data leakage.

- **Financial Calculation Integrity:**
  - Decided against trusting cart line item totals or subtotal values sent from the client.
  - Server checkout API (`/api/pos/checkout`) re-queries database selling prices for each `item_id` and portion choice (`half` vs `full`), computing totals in Python using exact Decimal rounding.

- **Atomic Sequential Token Generation:**
  - Implemented `DailyTokenSequence` table with unique constraint on `(business_id, date_key)`.
  - Uses `with_for_update()` database row locking during checkout to prevent duplicate token numbers (e.g. issuing duplicate `#001`) during concurrent multi-terminal peak hour rushes.

- **Fast 1-Click Thermal Print Flow:**
  - Removed optional customer name, phone number, and table/counter input fields from the POS checkout panel to streamline peak-hour billing.
  - Tapping **"Generate Token & Bill"** invokes `window.print()` directly after receiving checkout API response, formats thermal DOM for 58mm roll paper, and clears cart state immediately.

- **QR Menu Cleanup:**
  - Completely removed QR Code menu generation options and tabs from top navigation and mobile bottom navbar per user request.

- **Admin Price & Image Management:**
  - Added Half Price and Full Price editing in the Admin dashboard.
  - Added `multipart/form-data` image file upload support to save dish photos to `static/uploads/` with unique UUID filenames, alongside web image URL inputs.

---

## 2. Bug Fixes & Technical Gotchas Resolved

- **Jinja2 JavaScript Escaping in HTML Attributes:**
  - *Issue:* Passing Jinja parameters like `{{ item.name|tojson }}` inside inline HTML `onclick="..."` double-quoted attributes caused HTML attribute premature closing and JavaScript syntax errors.
  - *Fix:* Refactored item card buttons and edit modal buttons to store values in HTML5 data-attributes (`data-id`, `data-name`, `data-portion`, `data-price`), calling `handleAddToCart(this)` and `handleOpenEditModal(this)`.

- **Deprecated Datetime Usage:**
  - Replaced deprecated `datetime.utcnow()` references with timezone-aware datetime practices where applicable.

---

## 3. Current Project Status

- **Status:** Complete MVP & Production Ready
- **Database:** SQLite DB (`tokenly.db`) initialized with working demo account `sharmafastfood`.
- **Server:** Flask Server running on `http://127.0.0.1:5000`.
- **Browser Verification:** Verified across all pages (`/login`, `/register`, `/pos`, `/admin`, `/history`).
