# Findora — Free Listing & Paid Featured Listing Specification

## 1. PURPOSE

Findora currently allows users to report lost and found items for free.

This specification introduces a new OPTIONAL monetization feature:

FREE LISTING + PAID FEATURED LISTING

The existing free Lost/Found functionality must remain unchanged.

Users must always be able to:

- Report a lost item for free.
- Report a found item for free.
- Search items for free.
- View item details for free.
- Contact the relevant owner/finder according to the existing system.
- Use the existing chat functionality.
- Use all existing Findora features without payment.

Payment is ONLY required when a user voluntarily chooses to promote
their own item.

The purpose of Featured Listing is to give a user's item higher
visibility in Lost/Found listings and search results for a limited
period.

---

# 2. IMPORTANT EXISTING PROJECT RULE

Findora is an existing Android + Django application.

The existing project MUST NOT be recreated or unnecessarily refactored.

The existing architecture is the source of truth.

Before implementation:

1. Read `FINDORA_MASTER_PROMPT.md`.
2. Inspect the existing Android project.
3. Inspect the existing Django backend.
4. Inspect the existing Item model.
5. Inspect existing Item APIs.
6. Inspect existing authentication.
7. Inspect existing Lost/Found listing logic.
8. Inspect existing Search and Voice Search.
9. Inspect existing Item Details.
10. Identify reusable components.

DO NOT duplicate existing:

- Item models
- Serializers
- Views
- APIs
- Repositories
- Adapters
- Activities
- Fragments
- Services

Add only the minimum required code.

---

# 3. TECHNOLOGY

Existing frontend:

- Android
- Java
- XML

Do NOT convert Java code to Kotlin.

Existing backend:

- Django
- Django REST Framework

Existing database:

- Existing project database

Deployment:

- Django backend deployed on Render.

Payment provider:

- Initially integrate ONE Nepal payment provider.
- Preferred first provider: Khalti.
- The architecture should allow another payment provider such as
  eSewa to be added later without rewriting the entire payment system.

---

# 4. BASIC BUSINESS MODEL

Findora has two types of listings:

## A. FREE LISTING

Every user can create a normal Lost or Found listing without paying.

Example:

User reports:

"Lost iPhone 15"

The item is created normally.

The item appears in the existing Lost Items section according to
the current listing/search logic.

No payment is required.

---

## B. FEATURED LISTING

A user who owns an existing item listing can optionally promote it.

Example:

User creates:

"Lost iPhone 15"

The user opens Item Details and sees:

⭐ Promote This Item

The user selects a promotion package.

Example:

24 Hours — Rs. 50
3 Days — Rs. 100
7 Days — Rs. 200

The user pays through the supported payment provider.

After the backend successfully verifies the payment:

The existing item becomes Featured.

The item receives higher visibility.

---

# 5. IMPORTANT MONETIZATION PRINCIPLE

Payment is OPTIONAL.

Findora must NEVER require payment to:

- Create a listing.
- Search.
- View listings.
- Contact users.
- Chat.
- Claim items.
- Report items.

Featured Listing is an additional visibility service.

The normal free listing remains fully functional.

---

# 6. FEATURED LISTING BENEFIT

The main benefit is PRIORITY VISIBILITY.

A Featured item should appear before normal items when the same
listing/search/category results are displayed.

Example:

LOST ITEMS

FEATURED:

⭐ iPhone 15
⭐ Samsung Phone

NORMAL:

Wallet
Keys
Laptop

The Featured status must NOT change the actual item category.

---

# 7. FEATURED ITEM DISPLAY

A Featured item should have a small visual indicator.

Example:

⭐ FEATURED

Do not create a huge advertisement-style card.

Use the existing Findora UI design.

The badge should be small, clear, and consistent with the current
design.

---

# 8. DATABASE DESIGN

Do NOT create a completely separate Item model.

Add the Featured Listing fields to the EXISTING Item model.

Required fields:

## is_featured

Boolean.

Default:

false

Meaning:

false = normal listing

true = potentially featured

---

## featured_until

DateTime.

Can be:

NULL

for normal items.

For a featured item:

the field contains the exact server-side expiry timestamp.

Example:

is_featured = true

featured_until = 2026-08-20 18:30:00

---

# 9. FEATURED STATUS RULE

An item is considered ACTIVE FEATURED only when:

is_featured == true

AND

featured_until > current server time

This means an item automatically stops being Featured after the
expiration time.

No manual action should be required.

---

# 10. EXPIRED FEATURED ITEMS

When:

featured_until <= current server time

the item is no longer Featured.

However:

DO NOT delete the item.

DO NOT remove the item from the database.

DO NOT change Lost/Found status.

DO NOT change ownership.

DO NOT change chat.

DO NOT change reports/history.

The item simply returns to NORMAL listing priority.

Conceptually:

Before expiry:

⭐ Featured Item

After expiry:

Normal Item

---

# 11. EXISTING ITEM STATUS MUST REMAIN PRIORITY

Featured status must NEVER override the existing Findora item
lifecycle.

For example:

If an item is:

ACTIVE + FEATURED

it can appear as Featured.

If the item becomes:

RETURNED

then the existing Return logic takes priority.

A returned item must NOT appear in active Lost/Found listings
just because it is Featured.

Example:

Returned + Featured

must still be removed from active listings according to the
existing Findora return system.

---

# 12. WHO CAN PROMOTE AN ITEM?

Only the authenticated user who owns the item/listing can promote it.

Example:

Milan creates an item.

Milan:

→ Can see "Promote This Item".

Hari:

→ Can view the item.

Hari:

→ MUST NOT see the promotion control.

A user must never be able to promote another user's item.

The backend MUST verify ownership.

Do not rely only on Android UI restrictions.

---

# 13. ANDROID ITEM DETAILS

Add an optional control to the existing Item Details screen.

For the item's owner:

⭐ Promote This Item

For other users:

Do NOT show the promotion button.

Do not redesign Item Details.

Do not move or remove existing controls.

The promotion option must fit naturally into the existing Item
Details UI.

---

# 14. PROMOTION PACKAGE SCREEN

When the owner clicks:

⭐ Promote This Item

show a simple package selection interface.

Example:

--------------------------------

⭐ Promote Your Item

Get higher visibility for your listing.

24 Hours
Rs. 50

3 Days
Rs. 100

7 Days
Rs. 200

[ Continue ]

--------------------------------

The actual prices must be configurable.

Do not scatter hardcoded prices throughout the Android code.

The backend should remain the authoritative source for price and
promotion duration.

---

# 15. PAYMENT FLOW

The complete payment flow should be:

User
 ↓
Existing Item Details
 ↓
Promote This Item
 ↓
Select Package
 ↓
Create Payment Request
 ↓
Django Backend
 ↓
Payment Provider
 ↓
User completes payment
 ↓
Payment Provider returns result
 ↓
Django verifies transaction
 ↓
Payment marked COMPLETED
 ↓
Existing Item marked FEATURED
 ↓
featured_until calculated
 ↓
Android refreshes Item Details
 ↓
⭐ Featured displayed

---

# 16. PAYMENT MUST NOT BE ACTIVATED BY ANDROID ALONE

NEVER implement:

Android button clicked
→ is_featured = true

This is insecure.

The Android application is not trusted.

The Django backend must verify the payment.

Only after successful server-side verification should:

is_featured = true

be stored.

---

# 17. PAYMENT MODEL

Create a payment model only if an equivalent payment model does
not already exist.

Suggested structure:

Payment

- id
- user
- item
- amount
- currency
- provider
- transaction_id
- status
- promotion_duration
- created_at
- verified_at

Possible statuses:

PENDING
COMPLETED
FAILED
CANCELLED

Use the project's existing naming conventions if different.

---

# 18. PAYMENT RELATIONSHIP

Each payment must be associated with:

1. The authenticated user.
2. The specific item.
3. The selected promotion package.

Example:

User:
Milan

Item:
Lost iPhone

Package:
3 Days

Amount:
Rs. 100

Payment:
PENDING

After verification:

Payment:
COMPLETED

Item:

is_featured = true

featured_until = current time + 3 days

---

# 19. TRANSACTION ID

Every payment must have a unique transaction/payment reference.

The backend must store it.

Do not activate the same payment multiple times.

The payment verification process must be idempotent.

If the verification request is accidentally sent twice,
the system must not:

- charge the user twice
- create duplicate promotion
- create duplicate payment records

---

# 20. PAYMENT AMOUNT VALIDATION

The backend must NOT blindly trust the amount sent by Android.

Example:

Android says:

amount = Rs. 50

The backend must determine that:

24 Hours = Rs. 50

The backend should validate:

- Item
- Package
- Duration
- Expected price
- Payment provider
- Transaction

The user must not be able to modify Android requests to get:

7 Days for Rs. 1

---

# 21. PAYMENT PROVIDER

Initial target:

Khalti

The integration must be isolated.

Create a clean payment service layer if the existing architecture
supports services.

Conceptually:

PaymentService

should handle:

- Create payment
- Verify payment
- Validate transaction
- Return payment status

Do not spread provider-specific code throughout:

- Item views
- Item serializers
- Chat
- Notifications
- Android activities

---

# 22. FUTURE PAYMENT PROVIDERS

The architecture should allow another provider later.

Example:

PaymentProvider

    ├── Khalti
    └── eSewa

Do not implement both unless required.

The current implementation should focus on one provider.

---

# 23. SECRET KEYS

Payment secret credentials MUST NEVER be stored in:

- Android source code
- XML
- GitHub
- public configuration
- Item model
- API responses

For Render deployment, store secrets in environment variables.

Example concept:

PAYMENT_SECRET_KEY

PAYMENT_PUBLIC_KEY

Use the exact environment variable names required by the
implementation.

---

# 24. ANDROID PAYMENT SECURITY

Android should never contain the backend secret key.

Android may contain only information that is safe to expose,
according to the payment provider's documentation.

The Django backend is responsible for sensitive verification.

---

# 25. PAYMENT STATES

The application must handle:

## SUCCESS

Payment verified.

→ Activate Featured Listing.

---

## FAILED

Payment failed.

→ Do not activate Featured.

→ Show appropriate error.

---

## CANCELLED

User cancelled payment.

→ Do not activate Featured.

---

## PENDING

Payment is not confirmed.

→ Do not activate Featured.

---

# 26. PAYMENT SUCCESS SCREEN

After verified payment:

Show something like:

Payment Successful ✓

Your item has been promoted.

Featured until:

20 August 2026, 6:30 PM

[ Done ]

Do not display success merely because the payment screen returned.

Success should be based on backend verification.

---

# 27. PAYMENT FAILURE

If payment fails:

Payment Failed

Your item has not been promoted.

[ Try Again ]

The item remains a normal listing.

---

# 28. FEATURED SORTING

Existing Lost/Found filtering must remain intact.

Only ranking/ordering changes.

Conceptually:

1. Active Featured matching items
2. Active Normal matching items

Example:

User selects:

Phone category

Results:

⭐ Featured Phone
⭐ Featured Phone
Normal Phone
Normal Phone

A Featured Wallet must NOT appear in Phone results.

---

# 29. SEARCH

Existing Search must continue working exactly as before.

If Findora currently searches:

- Item title
- Item category

keep that behavior.

Featured status affects only ranking.

Example:

Search:

phone

Results:

⭐ iPhone
⭐ Samsung Phone
Normal Phone

Do NOT use Featured status as a search keyword.

---

# 30. VOICE SEARCH

Do not break existing Voice Search.

Voice Search should continue using the existing title/category
search functionality.

Featured status only affects ordering.

---

# 31. CATEGORY FILTERS

Existing categories must continue working:

- All
- Phone
- Wallet
- Keys
- Shoes
- etc.

Featured sorting must happen AFTER applying the relevant filter.

Correct:

Phone filter
→ matching phones
→ featured phones first
→ normal phones

Incorrect:

Featured items
→ unrelated categories mixed together

---

# 32. MULTI-DEVICE BEHAVIOR

The Featured status is stored in the backend.

Therefore it must work consistently across devices.

Example:

Milan promotes an item on Device A.

Device B opens the same item.

Device B should receive the correct Featured status from the backend.

Do not store Featured status only in SharedPreferences.

---

# 33. MULTI-USER SECURITY

Test with at least two accounts.

Account A:

Milan

Account B:

Hari

Milan owns Item 1.

Hari must not be able to promote Item 1.

The backend must reject unauthorized promotion attempts.

---

# 34. PROMOTION ENDPOINT

Implement an authenticated backend endpoint according to the
existing API architecture.

Conceptually:

POST

/api/items/{item_id}/promote/

Request should identify the selected promotion package.

Example concept:

{
    "duration": "24h"
}

The exact URL and request format should follow existing Findora
API conventions.

---

# 35. PAYMENT ENDPOINTS

Use the minimum required endpoints.

Possible architecture:

POST /api/payments/create/

POST /api/payments/verify/

POST /api/items/{id}/promote/

However, FIRST inspect the existing architecture and use the
smallest clean design.

Do not create unnecessary endpoints.

---

# 36. PROMOTION ACTIVATION

Promotion activation must happen on the backend.

Conceptually:

payment verified
        ↓
payment.status = COMPLETED
        ↓
item.is_featured = true
        ↓
item.featured_until = now + duration
        ↓
save

This should be performed safely and atomically where appropriate.

---

# 37. TIME HANDLING

All Featured expiration calculations must use SERVER TIME.

Do not rely on the Android device's local clock.

This prevents users from changing their phone time to extend
Featured status.

Use timezone-aware Django datetime handling.

---

# 38. NEPAL TIME

Findora currently uses Nepal time for displayed timestamps.

The Featured expiration shown to the user should follow the
existing Findora timezone/display convention.

However, the backend should use timezone-aware timestamps and
perform comparisons safely.

Do not introduce a second inconsistent time system.

---

# 39. FEATURED BADGE

Example:

⭐ FEATURED

The badge should:

- Be small.
- Be clearly visible.
- Not cover item images.
- Not cover important text.
- Follow existing Findora UI.
- Work in both Light and Dark themes.

---

# 40. LIGHT/DARK THEME

Featured Listing must support the existing Findora theme system.

Light Mode:

- Featured badge readable.
- Text readable.
- Button readable.

Dark Mode:

- Featured badge readable.
- Text readable.
- Button readable.
- No unwanted white backgrounds.

Do not create a separate theme system.

---

# 41. EXISTING RETURN SYSTEM

Featured Listing must not interfere with:

- Mark as Returned
- Return Pending Finder Confirmation
- Active listing removal
- My Reports & History

Example:

Item:

Featured

Then:

Owner receives item.

Owner completes existing return process.

Expected:

Existing return flow works normally.

The item must no longer appear in active Lost/Found listings.

Featured status must not prevent this.

---

# 42. EXISTING CLAIM SYSTEM

Featured Listing must not change:

- Claim Item
- Claim verification
- Owner/Finder relationships
- Item ownership
- Chat

The Featured feature is only a visibility enhancement.

---

# 43. EXISTING CHAT SYSTEM

Do not change:

- Contact Owner
- Contact Finder
- Message sending
- Message receiving
- Image messages
- Notifications
- Conversations

Featured status must have no effect on chat.

---

# 44. EXISTING NOTIFICATIONS

Do not modify notification behavior.

Promotion should not interfere with:

- Message notifications
- Reply notifications
- Item notifications
- Conversation notifications

---

# 45. USER EXPERIENCE

The user should always understand:

1. Normal listing is FREE.
2. Promotion is OPTIONAL.
3. Promotion has a price.
4. Promotion has a duration.
5. Payment is required before activation.
6. Featured status expires automatically.

Do not make the payment option misleading.

---

# 46. OWNER EXPERIENCE

Example:

Milan creates:

Lost iPhone 15

Normal state:

Item Details

[ Contact / existing controls ]

⭐ Promote This Item

Milan selects:

3 Days — Rs. 100

Payment succeeds.

Item Details now shows:

⭐ FEATURED

Featured until:

20 August 2026

---

# 47. OTHER USER EXPERIENCE

Hari views Milan's item.

Hari sees:

⭐ FEATURED

But does NOT see:

Promote This Item

because Hari does not own the item.

---

# 48. ADMIN / DJANGO ADMIN

If appropriate, expose payment/promotion information in the
existing Django Admin.

Do NOT create a second admin panel.

Admin may be able to see:

- User
- Item
- Amount
- Provider
- Transaction ID
- Payment status
- Created time
- Verified time
- Featured expiry

Do not allow unsafe manual changes unless necessary.

---

# 49. DATABASE MIGRATION SAFETY

Existing database data MUST remain safe.

Do NOT:

- Delete database
- Reset migrations
- Drop tables
- Delete users
- Delete existing items

After migration, all existing items should effectively remain
normal/free listings.

Expected:

is_featured = false

featured_until = null

---

# 50. API BACKWARD COMPATIBILITY

Existing Android API functionality must continue working.

Adding:

is_featured
featured_until

must not break existing JSON parsing.

Do not rename existing API fields.

Do not remove existing API fields.

Do not change existing endpoint behavior unnecessarily.

---

# 51. OFFLINE / NETWORK FAILURE

If the user loses network connectivity during payment:

Do NOT activate Featured locally.

The backend must remain authoritative.

Android should show an appropriate network/payment status and allow
the user to retry safely.

Do not create duplicate payments during retry.

---

# 52. DUPLICATE PROMOTION

If an item is already Featured and the owner wants to promote it
again, inspect the existing business requirements before deciding
how to behave.

Preferred simple behavior:

If currently Featured:

Show:

This item is already featured until:
[date/time]

Offer:

Extend Promotion

if extension is implemented.

Do not accidentally create multiple overlapping Featured states.

For the first version, it is acceptable to prevent another
promotion until the current one expires, if that is simpler and
safer.

---

# 53. PAYMENT HISTORY

Payment records should remain stored for accountability.

Do not delete successful payment records simply because the
promotion expires.

A payment record represents a historical transaction.

---

# 54. REFUND LOGIC

Refunds are NOT part of the first version unless required by the
payment provider/business requirements.

Do not invent a refund system.

If payment is successful and verified, the promotion is activated.

---

# 55. REAL PAYMENT VS DEMO PAYMENT

Development/testing may use a sandbox/test payment environment
when supported.

Do not use fake successful payments in production.

For the final application:

Payment status must come from actual provider verification.

---

# 56. DEVELOPMENT PHASES

Implement in this order.

## Phase 1

Database:

- is_featured
- featured_until

Migration.

---

## Phase 2

Backend:

- Promotion logic
- Ownership verification
- Expiration logic
- Featured ordering

---

## Phase 3

Android:

- Promote This Item
- Package selection
- Featured badge
- Featured status

---

## Phase 4

Payment:

- Payment creation
- Payment provider
- Payment verification
- Payment status

---

## Phase 5

Integration:

Payment success
→ Featured activation

---

## Phase 6

Testing:

- Free listing
- Featured listing
- Expiry
- Search
- Categories
- Lost/Found
- Returned items
- Two users
- Two devices
- Light mode
- Dark mode

---

# 57. TEST CASE — FREE LISTING

User:

Milan

Creates:

Lost Phone

Expected:

- No payment required.
- Item is created.
- Item appears normally.
- Existing functionality works.

---

# 58. TEST CASE — FEATURED LISTING

Milan opens own item.

Clicks:

Promote This Item

Selects:

24 Hours

Pays successfully.

Expected:

is_featured = true

featured_until = correct future time

Item shows:

⭐ FEATURED

---

# 59. TEST CASE — PAYMENT FAILURE

Payment fails.

Expected:

is_featured remains false.

Item remains normal.

---

# 60. TEST CASE — EXPIRATION

Featured item reaches:

featured_until

Expected:

Item becomes normal automatically.

No deletion.

No manual action.

---

# 61. TEST CASE — SEARCH

Search:

phone

Expected:

Featured matching phones appear before normal matching phones.

---

# 62. TEST CASE — CATEGORY

Phone category selected.

Expected:

Only phone items.

Featured phones appear before normal phones.

---

# 63. TEST CASE — OWNERSHIP

Milan owns item.

Hari attempts to promote it.

Expected:

Backend rejects request.

---

# 64. TEST CASE — MULTI-DEVICE

Milan promotes item using Device A.

Open same item using Device B.

Expected:

Device B receives Featured state from backend.

---

# 65. TEST CASE — RETURNED ITEM

Featured item becomes returned.

Expected:

Existing return system removes it from active listings.

Featured status must not override return behavior.

---

# 66. TEST CASE — APP RESTART

User promotes item.

Close app.

Reopen app.

Expected:

Featured state is still correct.

---

# 67. TEST CASE — LIGHT/DARK

Featured item must remain readable in:

Light Theme

and

Dark Theme.

---

# 68. SECURITY REQUIREMENTS

The implementation must prevent:

- Unauthorized promotion.
- Fake payment success.
- Amount manipulation.
- Duration manipulation.
- Transaction replay.
- Duplicate payment processing.
- Client-side Featured activation.
- Secret key exposure.

The backend is authoritative.

---

# 69. PERFORMANCE

Featured sorting should be performed efficiently.

Do not retrieve every item and sort huge datasets in Android.

Prefer backend/database-level ordering where appropriate.

Existing pagination should continue working if already implemented.

---

# 70. FINAL ARCHITECTURE

The final system should conceptually look like:

ANDROID

Item Details
    ↓
Promote Item
    ↓
Package Selection
    ↓
Payment
    ↓
Payment Result
    ↓
Backend Verification
    ↓
Featured Status Display


DJANGO

Authentication
    ↓
Item Ownership
    ↓
Payment Creation
    ↓
Payment Verification
    ↓
Promotion Activation
    ↓
Featured Expiration
    ↓
Featured Ordering


DATABASE

Existing Item
    +
is_featured
featured_until

Payment
    +
transaction/payment information


PAYMENT PROVIDER

Khalti initially

Future:

eSewa / other supported providers

---

# 71. MOST IMPORTANT DEVELOPMENT RULE

Do NOT implement this feature by rewriting existing Findora
functionality.

The implementation must be additive.

The existing application should behave exactly the same for users
who never use Featured Listing.

A user who never clicks:

⭐ Promote This Item

should experience Findora exactly as before.

Only users who voluntarily choose promotion should enter the new
payment/Featured flow.

---

# 72. SUCCESS CRITERIA

The feature is considered successfully implemented only when:

✓ Normal listing remains completely FREE.

✓ Existing item creation remains unchanged.

✓ Owner can optionally promote their own item.

✓ Other users cannot promote someone else's item.

✓ Promotion package can be selected.

✓ Payment is processed securely.

✓ Backend verifies payment.

✓ Successful payment activates Featured status.

✓ Failed payment does not activate Featured.

✓ Featured status has an expiration time.

✓ Expired Featured items become normal automatically.

✓ Featured items receive higher listing/search priority.

✓ Existing category filtering still works.

✓ Existing title/category search still works.

✓ Voice Search is not broken.

✓ Returned items still follow existing return logic.

✓ Chat is not affected.

✓ Notifications are not affected.

✓ Existing Lost/Found functionality is not affected.

✓ Featured state works across multiple devices.

✓ Payment records are stored.

✓ Secret credentials are protected.

✓ Existing Django Admin can inspect payment information if
appropriate.

✓ Light and Dark themes support the new UI.

✓ Existing users and items are not lost.

✓ Existing APIs remain backward compatible.

✓ Android project builds successfully.

✓ Django migrations complete successfully.

✓ The complete two-user workflow works correctly.