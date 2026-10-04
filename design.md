# Design System & UI/UX Specification — Tokenly

## 1. Global Visual Design System

Tokenly utilizes a dark, mobile-first design system tailored for high-contrast visibility in fast food counters, food trucks, and dimly lit kitchen environments.

---

## 2. Color Palette

| Token / Usage | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Background Dark** | `#0b0f19` | Main application background (Deep Charcoal Navy) |
| **Surface Card** | `#161f30` | Card & glass panel background |
| **Card Border** | `#1f2d44` | Subtle card & input border divider |
| **Primary Blue** | `#2563eb` | Primary CTA buttons (`.btn-blue`) & subscription cards |
| **Electric Cyan** | `#00f2fe` | Tokenly gradient logo highlight & active icons |
| **Crimson Red CTA** | `#e11d48` | POS master **"Generate Token & Bill"** button (`.btn-red-bill`) |
| **Active Category** | `#e11d48` | Selected category filter pill background |
| **Half Portion Pill**| `rgba(245,158,11,0.2)` | Amber half portion pricing button (`#f59e0b`) |
| **Full Portion Pill**| `rgba(16,185,129,0.2)` | Emerald full portion pricing button (`#10b981`) |
| **Text High Contrast**| `#f9fafb` | Primary dish titles, totals, and headings |
| **Text Muted** | `#94a3b8` | Subtitles, item descriptions, and labels |

---

## 3. Typography & Component Radii

- **Primary Font Family:** Plus Jakarta Sans (`font-sans`)
- **Monospace Font Family:** JetBrains Mono (`font-mono`) for prices, token numbers (`#001`), and total amounts.
- **Card Corner Radius:** `16px` (`rounded-2xl`)
- **Button Corner Radius:** `12px` (`rounded-xl`)
- **Portion Button Target:** Minimum `38px` touch height for high-speed cashier tapping on iOS Safari and touch terminals.

---

## 4. Key Screen Mockup References

### Screen A: Welcome & Login (`Page01.jpeg`)
- Stylized cyan gradient **T** logo.
- Storefront icon on Username field, lock icon & eye reveal toggle on Password field.
- Solid electric blue **"Login to Terminal →"** button.

### Screen B: Subscription Registration (`Page02.jpeg`)
- **"Start Your Subscription"** header card.
- Annual POS Access card displaying **₹4,999/year**.
- Solid electric blue **"Proceed to Payment & Activate →"** CTA button.

### Screen C: POS Terminal (`Page03.jpeg` & `Page04.jpeg`)
- Red Chef Hat logo + Business Name (*Sharma Fast Food*) + subline (*Chinese Food • Fast Delivery Available*).
- Horizontal scrollable category pills with red active tab highlight (`All`, `Chinese`, `Noodles`, `Rolls & Momos`, `Burgers & Snacks`, `Beverages`).
- 2-Column Food Card Grid with dish photo thumbnails and direct inline `Half ₹X` | `Full ₹Y` portion buttons.
- Streamlined Current Order drawer: Subtotal, Grand Total (`₹150.00`), and master red button **"Generate Token & Bill"**.
- Bottom 5 navigation tabs (`Home`, `Menu`, `Order`, `History`, `More`) + status footer (`● v10.0 Online | POS Terminal v1.0`).

---

## 5. Thermal Receipt Print Specifications (`@media print`)

- **Paper Format:** 58mm (2.28 in) standard & 80mm thermal paper roll width.
- **Header:** Uppercase Business Name, Timestamp.
- **Token Banner:** Enlarged **TOKEN #001** (28pt bold font in black border box).
- **Body:** Itemized list with Half/Full portion indicators, quantities, line totals, and grand total.
- **Footprint:** Customer name and table lines removed for fast, zero-waste thermal slip printing.
