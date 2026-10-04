# Actionable MVP Tasks & Checklist — Tokenly

## Phase 1: Foundation & Core Multi-Tenant Architecture
- [x] Create project structure, configuration settings, and database URI setup (`config.py`).
- [x] Implement SQLAlchemy multi-tenant database models (`Business`, `Category`, `MenuItem`, `DailyTokenSequence`, `Order`, `OrderItem`, `AuditLog`) in `models.py`.
- [x] Create Flask-WTF forms for registration, login, menu item creation, and category creation (`forms.py`).
- [x] Build multi-tenant helper functions, atomic token generator, audit logger, and default menu seeder (`utils.py`).

## Phase 2: Authentication & Subscription System
- [x] Build public routes for landing (`/`), registration (`/register`), login (`/login`), and logout (`/logout`) in `routes/auth.py`.
- [x] Implement registration and annual subscription activation (365-day expiry tracking).
- [x] Design Welcome & Login screen matching `Page01.jpeg` (`templates/auth/login.html`).
- [x] Design Subscription Registration screen matching `Page02.jpeg` (`templates/auth/register.html`).

## Phase 3: Touch-Friendly Cashier POS Terminal
- [x] Build `/pos` terminal route and server-side checkout API `/api/pos/checkout` (`routes/pos.py`).
- [x] Implement 2-column food card grid with high-res dish photography and direct inline `Half ₹X` | `Full ₹Y` portion buttons matching `Page04.jpeg`.
- [x] Build horizontal category filter pills (`All`, `Chinese`, `Noodles`, `Rolls & Momos`, `Burgers & Snacks`, `Beverages`) with crimson red active highlight matching `Page03.jpeg`.
- [x] Implement live cart state management, quantity increment/decrement, subtotal, tax, and grand total math in `static/js/pos.js`.
- [x] Streamline checkout drawer by removing customer name, phone, and table/counter # fields.
- [x] Add master crimson red **"Generate Token & Bill"** button (`.btn-red-bill`).

## Phase 4: Thermal Printer Integration & 1-Click Print
- [x] Configure `@media print` CSS for 58mm and 80mm Bluetooth/USB thermal paper rolls in `static/css/style.css`.
- [x] Implement atomic transaction locking (`with_for_update()`) for daily sequential token generation (`#001`, `#002`).
- [x] Implement instant 1-click print flow: trigger `window.print()`, build thermal DOM, and reset cart state instantly in under 1 second.
- [x] Format thermal slip with enlarged **TOKEN #001** header and stripped customer/table space.

## Phase 5: Admin Menu Management & Price/Image Editing
- [x] Build `/admin` dashboard routes for Category CRUD and Item CRUD (`routes/admin.py`).
- [x] Add inline/modal Half Price and Full Price editing for menu items (`templates/admin/dashboard.html`).
- [x] Add image file upload handling (`static/uploads/`) and web image URL inputs with real-time thumbnail preview.
- [x] Completely remove obsolete QR Menu option from desktop header and mobile bottom navbar.

## Phase 6: Permanent Sales Logs & History
- [x] Build `/history` order logs route with date range filtering (`Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `Custom Date Range`) and token search.
- [x] Calculate revenue metrics summary (Total Revenue, Tokens Issued, Average Ticket Size, Cash vs UPI vs Card breakdown).
- [x] Add thermal receipt reprint feature for historical orders (`/history/reprint/<id>`).

## Phase 7: UI/UX Dark Theme Re-Skin & Polish
- [x] Implement master dark design system in `static/css/style.css` (`#0b0f19` background, `#161f30` cards, cyan gradient T logo).
- [x] Add status footer indicator (`● v10.0 Online | POS Terminal v1.0`) and mobile 5-tab navbar (`Home`, `Menu`, `Order`, `History`, `More`).
- [x] Verify complete application flow across desktop and mobile viewports via browser testing.
