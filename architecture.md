# Architecture Document — Tokenly

## 1. Technology Stack

### Backend
- **Framework:** Python Flask 3.1.1
- **Authentication & Sessions:** Flask-Login 0.6.3 with cryptographically signed cookies (`SECRET_KEY`, `HttpOnly`, `SameSite=Lax`)
- **Database ORM:** SQLAlchemy 2.1.1 / Flask-SQLAlchemy 3.1.1
- **Forms & Security:** Flask-WTF 1.2.2 with CSRFProtect
- **Rate Limiting:** Flask-Limiter 4.1.1 (Memory/Redis backends)
- **Password Security:** Werkzeug 3.1.3 (`generate_password_hash` / `check_password_hash` with scrypt/bcrypt)

### Frontend
- **Structure & Logic:** HTML5 Jinja2 Templates + Vanilla JavaScript (ES6)
- **Styling:** Tailwind CSS CDN + Custom Dark UI Design System (`static/css/style.css`)
- **Printing:** Native Browser Print API (`window.print()`) with dedicated 58mm/80mm thermal CSS (`@media print`)

---

## 2. Directory Structure

```
c:\Tokenly\
├── app.py                  # Flask Application Factory, Error Handlers, Extension Setup
├── config.py               # Configuration Constants, DB URI, Security Flags, Rate Limits
├── models.py               # SQLAlchemy Database Models (Business, Category, MenuItem, etc.)
├── forms.py                # Flask-WTF Forms for Register, Login, Menu Items, Categories
├── utils.py                # Helper Utilities (Token Generator, File Storage, Audit Logs, Seeders)
├── seed.py                 # Initial Demo Data Seeder
├── routes/
│   ├── auth.py             # Public Routes: Landing (/), Login (/login), Register (/register), Logout (/logout)
│   ├── pos.py              # Touch Terminal POS (/pos) & Server Checkout API (/api/pos/checkout)
│   ├── admin.py            # Menu Management Admin (/admin), Items CRUD, Category CRUD, Theme Toggle
│   └── history.py          # Sales History (/history), Date Filters, Reprint API (/history/reprint/<id>)
├── static/
│   ├── css/
│   │   └── style.css       # Dark UI Design System, Custom Buttons, Glass Panels, Thermal Print CSS
│   ├── js/
│   │   ├── pos.js          # POS Cart State, Portion Addition, Server Checkout AJAX, Instant Print
│   │   ├── theme.js        # Dynamic Theme Switcher (Crimson Red / Obsidian Blue)
│   │   └── main.js         # Admin Modals, Status Toggles, Flash Alerts
│   └── uploads/            # Uploaded Dish Photos
└── templates/
    ├── base.html           # Base Responsive Layout with Top Header & Mobile 5-Tab Navbar
    ├── auth/
    │   ├── landing.html    # Product Overview Page
    │   ├── login.html      # Welcome & Login Screen (Screen A matching Page01.jpeg)
    │   ├── register.html   # Subscription Registration Screen (Screen B matching Page02.jpeg)
    │   └── subscription.html # License Details & Expiry Dashboard
    ├── pos/
    │   └── terminal.html   # Touch POS Terminal (Screen C matching Page03.jpeg & Page04.jpeg)
    ├── admin/
    │   └── dashboard.html  # Menu Management Admin, Price Editor, Image Upload Modal
    ├── history/
    │   └── orders.html     # Permanent Sales Logs, Date Filters, Revenue Analytics
    └── errors/
        ├── 404.html        # Custom 404 Page
        └── 500.html        # Custom 500 Server Error Page
```

---

## 3. Database Schema Entity Relationship

```
+-------------------+       +-------------------+       +-------------------+
|     Business      | 1---* |     Category      | 1---* |     MenuItem      |
+-------------------+       +-------------------+       +-------------------+
| id (PK)           |       | id (PK)           |       | id (PK)           |
| business_name     |       | business_id (FK)  |       | business_id (FK)  |
| owner_name        |       | name              |       | category_id (FK)  |
| phone             |       | sort_order        |       | name              |
| username (indexed)|       +-------------------+       | half_price        |
| password_hash     |                                   | full_price        |
| subscription_exp  |                                   | image_url         |
+-------------------+                                   | is_veg / available|
         |                                              +-------------------+
         | 1                                                     | 1
         |                                                       |
         v *                                                     v *
+-------------------+       +-------------------+       +-------------------+
|DailyTokenSequence |       |       Order       | 1---* |     OrderItem     |
+-------------------+       +-------------------+       +-------------------+
| id (PK)           |       | id (PK)           |       | id (PK)           |
| business_id (FK)  |       | business_id (FK)  |       | order_id (FK)     |
| date_key (YYYY-MM)|       | token_number      |       | item_id (FK)      |
| last_token_num    |       | raw_token_num     |       | item_name         |
+-------------------+       | date_key          |       | portion (half/full|
                            | subtotal/tax/total|       | quantity          |
                            | payment_method    |       | unit_price        |
                            | created_at        |       | total_price       |
                            +-------------------+       +-------------------+
```

---

## 4. Execution & Order Checkout Flow

1. **User Action:** Cashier taps `Half` or `Full` portion buttons on food cards to add items to cart.
2. **Client Calculation:** Live subtotal and grand total rendered client-side.
3. **Checkout Request:** Cashier taps **"Generate Token & Bill"**. Frontend sends AJAX `POST` request to `/api/pos/checkout` containing `[{ item_id, portion, quantity }]` and `payment_method`.
4. **Server Financial Verification:**
   - Server validates session and verifies business subscription.
   - For every item, server re-queries `MenuItem.query.filter_by(id=item_id, business_id=current_user.id)` to obtain the authoritative database price.
   - Computes subtotal, tax, and grand total in Python using exact float/Decimal rounding.
5. **Atomic Sequential Token Generation:**
   - Obtains database update lock (`with_for_update()`) on `DailyTokenSequence` for today's date key.
   - Increments `last_token_num` atomically to assign sequence numbers (`#001`, `#002`, `#003`).
6. **Persistence & Response:**
   - Inserts `Order` and `OrderItem` records tied to `business_id`.
   - Logs audit trail entry in `AuditLog`.
   - Returns structured JSON containing token number and receipt breakdown.
7. **Instant Receipt Printing:**
   - Client builds thermal print HTML, invokes `window.print()`, displays notification toast, and clears cart state immediately.
