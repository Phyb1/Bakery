# Changelog

## Bakery UX and ordering improvement batch
- Reworked the homepage around a clear first-visit journey, menu CTAs, featured items, ordering steps, location/hours and helpful contact prompts.
- Added FAQ page covering ordering, confirmations, delivery, collection, payments, custom orders, allergies and cancellations.
- Added persistent floating WhatsApp contact button and more useful multi-item cart checkout fields.
- Cart WhatsApp message now includes customer contact, delivery/collection choice, address, instructions, line totals and a subtotal. It clearly asks the bakery to confirm fees and payment before treating the order as final.
- Fixed blank product-image handling so missing images do not crash product cards/homepage.
- Removed the 15-minute menu response cache so newly added/updated products appear without waiting for a stale cache.
- Added overnight opening-hour handling for schedules such as Fri 18:00-02:00.
- Restyled the public website for responsive mobile-first navigation, product cards, quantity controls, cart, FAQ and footer.
- Added consistent bakery admin branding.
- Direct online payment is not enabled in this batch: it requires a selected provider and merchant credentials, plus verified server-side payment callbacks.
- Repaired `passenger_wsgi.py`: the uploaded file contained README text instead of executable WSGI code, which would prevent cPanel Passenger startup.

## 2026-10-25 — Server-recorded WhatsApp orders

- Added server-side `Order` and `OrderItem` records with unique references, USD totals, order lifecycle statuses, and separate manual payment-verification statuses.
- Added a CSRF-protected JSON order endpoint. The server validates customer details and quantities, checks availability, and calculates all prices from current database values rather than trusting localStorage prices.
- Checkout now saves the order before opening WhatsApp, and sends one itemised message including the order reference and subtotal. The cart is cleared only after the server successfully saves the order.
- Added Django admin order management with searchable customer/reference fields, editable order/payment statuses, staff payment notes, and read-only item snapshots.
- Added tests for successful order creation, price tampering, missing delivery address, unavailable products, invalid quantities, and empty carts.
- Payment remains manual: customer messages/proof are not treated as verified payment. Staff must verify receipt before setting payment status to Paid.
- Delivery fee is currently $0.00 until a bakery-specific fee policy is configured; checkout message asks staff to confirm any applicable fee before final confirmation.
