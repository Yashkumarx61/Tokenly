# Product Requirements Document (PRD) — Tokenly

## 1. Overview & Problem Statement
Fast food outlets, street food stalls, Chinese counters, rolls & momos shops, and quick-service food businesses face severe operational bottlenecks during peak hours:
- **Queue Bottlenecks:** Slow manual order taking creates long customer lines and lost sales.
- **Calculation Errors:** Manual price math leads to revenue leaks and cashier mistakes.
- **Portion Complexity:** Stalls frequently sell Half and Full portions of dishes (e.g., Half Manchurian ₹70 / Full Manchurian ₹130), making traditional single-price POS systems awkward.
- **Lack of Multi-Tenancy:** Small business owners need a secure, low-cost SaaS solution with strict data isolation.

**Tokenly** solves this with a mobile-first, high-speed multi-tenant POS and peak-hour token management system featuring 1-tap Half/Full portion billing, atomic sequential daily token numbers (`#001`, `#002`), and instant 58mm/80mm thermal receipt printing.

---

## 2. Target Audience
- Fast Food Outlets & Food Stalls
- Chinese Food Counters, Rolls & Momos Joints
- Food Truck Operators & Food Court Counters
- Quick-Service Restaurants (QSRs) requiring token-based kitchen display callouts

---

## 3. Core MVP Features

### A. Multi-Tenant Authentication & Subscription System
- **Registration & Login:** Business Name, Owner Full Name, Mobile Number, Username ID, Password.
- **Subscription Management:** Annual license model (₹4,999/year or ₹2,999/year) with 365-day tracking and active status badges.
- **Strict Data Isolation:** Every entity (`Category`, `MenuItem`, `Order`, `OrderItem`, `DailyTokenSequence`) is bound to a `business_id`.

### B. Touch-Friendly Cashier POS Terminal (`/pos`)
- **Header:** Red Chef Hat logo, Business Name, Subline, Profile link, and `🍴 Menu` button.
- **Category Filter Pills:** Horizontal scroll bar (`All`, `Chinese`, `Noodles`, `Rolls & Momos`, `Burgers & Snacks`, `Beverages`, `Combos`) with red active pill highlight.
- **2-Column Product Cards:** High-quality food imagery, dish title, veg/non-veg tag, and direct inline variant buttons (`Half ₹X` | `Full ₹Y`).
- **Current Order Drawer:** Live itemized cart list (`1x Full Chowmein ₹110`), quantity increment/decrement (`+` / `-`), payment mode toggle (Cash, UPI, Card), Subtotal, Tax (0%), and Grand Total (`₹150.00`).
- **Master Action Button:** Full-width crimson red **"Generate Token & Bill"** button.

### C. Accelerated Thermal Printer Integration
- **Direct Auto-Print:** Tapping "Generate Token & Bill" instantly submits checkout via AJAX, builds the 58mm/80mm thermal receipt DOM, invokes `window.print()`, and clears the cart state immediately.
- **Prominent Token Number:** Receipt displays an enlarged, bold **TOKEN #001** banner at the top, followed by date/time, itemized list, and grand total.

### D. Admin Menu & Price Management (`/admin`)
- **Category Management:** Add, sort, and delete menu categories.
- **Item & Selling Price Editor:** Add and edit items with Half Price, Full Price, Veg indicator, and availability toggles.
- **Image Manager:** File upload support (`static/uploads/`) and web image URL inputs with instant thumbnail previews.

### E. Permanent Order History & Sales Logs (`/history`)
- **Sales Analytics:** Total Revenue, Tokens Issued, Average Order Value, and Cash vs UPI vs Card payment breakdown.
- **Date Range Filters:** Preset filters (`Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `Custom Date Range`) and search bar for Token # or items.
- **Instant Reprint:** Thermal receipt reprint capability for any past order.
