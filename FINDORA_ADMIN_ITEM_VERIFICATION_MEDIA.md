# FINDORA — ADMIN ITEM VERIFICATION MEDIA

## OBJECTIVE

Improve:

**Django Admin → Items → Select Item → Change Item**

so Admin can review the **actual image uploaded for that exact Item report** by the Owner or Finder.

## REQUIRED BEHAVIOR

### Owner-reported Lost Item

The image uploaded by that Owner during:

**Owner → Report Item → Item Photo**

must appear only in that exact Owner-reported Item's **Change Item** page.

### Finder-reported Found Item

The image uploaded by that Finder during:

**Finder → Report Item → Item Photo**

must appear only in that exact Finder-reported Item's **Change Item** page.

## CRITICAL DATA MATCHING RULE

Images MUST be matched to the **exact Item record**, not merely by:

* category
* item name
* description
* user role
* image filename
* upload date
* similar item

Use the actual Item/Image database relationship and Item ID.

Example:

```text
Owner1 → Lost Laptop → Item ID 101 → Owner1's uploaded image

Finder1 → Found Laptop → Item ID 102 → Finder1's uploaded image
```

Item 101 must show only its own image.

Item 102 must show only its own image.

Do NOT mix Owner and Finder images.

## NEVER SHOW OLD/UNRELATED IMAGES

Do NOT display:

* deleted images
* old test images
* unrelated images
* previously returned item's images
* shoe images unless the exact Item actually contains that image
* images belonging to another Item
* images belonging to another User

If an Item has no valid uploaded image, show **no image** rather than an unrelated/placeholder database image.

## IMPORTANT

Do not create a new image system.

Inspect the existing:

* Item model
* Item Image model/relationship
* Owner report API
* Finder report API
* image upload code
* serializers
* Admin `ItemAdmin`
* Admin forms/inlines
* image storage/path configuration

Trace the image from:

**Android upload → API → database → Item relationship → Django Admin**

and identify the actual cause of any incorrect image association.

## OWNER/FINDER SEPARATION

Determine the report type from the existing Item data.

Do NOT permanently assign Owner/Finder roles to Users.

A User can be an Owner for one report and Finder for another.

## ADMIN PURPOSE

The image is required in Admin so the Admin can inspect the actual reported item and make an informed verification/approval decision.

Do not automatically approve or reject the Item based only on the image.

## SAFETY

Do NOT:

* delete existing Users
* delete Items
* delete valid Item Images
* reset the database
* create duplicate image systems
* attach images manually to unrelated Items
* use hardcoded image filenames
* use a default shoe image
* modify Owner/Finder authentication
* break existing image uploads

Existing valid images must remain intact.

## TEST DATA

Test with multiple reports, including the same category:

```text
Owner1 → Lost Laptop → Image A
Finder1 → Found Laptop → Image B
Owner2 → Lost Laptop → Image C
Finder2 → Found Laptop → Image D
```

Admin must see:

```text
Owner1 Item → Image A
Finder1 Item → Image B
Owner2 Item → Image C
Finder2 Item → Image D
```

No cross-matching.

Also test an Item with no image:

```text
Item → no image
Admin → no unrelated image displayed
```

## SUCCESS CRITERIA

Every Change Item page displays only the image(s) actually belonging to that exact Item.

No stale, deleted, unrelated, or cross-user images may appear.
