"""
Findora Category Verification Schemas & Constants.

Provides universal, category-tailored verification definitions,
blind question prompts, discriminative evidence weights, and lifecycle states
for all 13 item categories in Findora.
"""

# ─── Category Definitions ───────────────────────────────────────────────────
CATEGORIES = [
    ('phone', 'Mobile Phone'),
    ('laptop', 'Laptop'),
    ('wallet', 'Wallet'),
    ('bag', 'Bag / Backpack'),
    ('keys', 'Keys'),
    ('documents', 'Documents / ID Card'),
    ('watch', 'Watch'),
    ('jewelry', 'Jewelry'),
    ('headphones', 'Earbuds / Headphones'),
    ('book', 'Books / Notes'),
    ('clothing', 'Clothing / Apparel'),
    ('electronics', 'Electronics / Gadgets'),
    ('other', 'Other Item'),
]

CATEGORY_KEYS = [c[0] for c in CATEGORIES]

CATEGORY_LABELS = {c[0]: c[1] for c in CATEGORIES}

# ─── Verification Status Lifecycle ──────────────────────────────────────────
# LOST / FOUND -> POTENTIAL_MATCH -> UNDER_VERIFICATION -> VERIFICATION_REQUIRED
# -> VERIFIED_MATCH -> CONTACT_ALLOWED -> RETURN_IN_PROGRESS -> RETURNED -> CLOSED
# Failures / Ambiguities: VERIFICATION_FAILED, ADDITIONAL_PROOF_REQUIRED, MULTIPLE_POSSIBLE_OWNERS
VERIFICATION_STATUS_CHOICES = [
    ('unverified', 'Unverified'),
    ('potential_match', 'Potential Match Found'),
    ('under_verification', 'Under Verification'),
    ('verification_required', 'Verification Required'),
    ('additional_proof_required', 'Additional Proof Required'),
    ('multiple_possible_owners', 'Multiple Possible Owners'),
    ('verified_match', 'Verified Match'),
    ('verification_failed', 'Verification Failed'),
    ('contact_allowed', 'Contact Allowed'),
    ('return_in_progress', 'Return In Progress'),
    ('returned', 'Returned'),
    ('closed', 'Closed'),
]

# ─── Potential Match Confidence Levels ──────────────────────────────────────
MATCH_CONFIDENCE_CHOICES = [
    ('high', 'High Confidence Match'),
    ('medium', 'Medium Confidence Match'),
    ('low', 'Low Confidence Match'),
]

# ─── Evidence Strength Classifications ───────────────────────────────────────
EVIDENCE_STRENGTH_CHOICES = [
    ('strong_identifier', 'Strong Identifier (Serial/IMEI/Asset Tag)'),
    ('distinctive_features', 'Distinctive Physical Characteristics / Private Features'),
    ('generic_candidate', 'Generic Candidate (Common Attributes Only)'),
]

# ─── Evidence Discriminative Scoring Weights ────────────────────────────────
# Principle: 5 common characteristics do NOT equal 1 unique identifier or discriminative proof.
DISCRIMINATIVE_WEIGHTS = {
    # Strong Evidence (Distinctive & High Entropy)
    'exact_identifier': 55.0,       # Exact IMEI / Serial / Service Tag / Asset Tag hash match
    'private_contents': 45.0,       # Non-public wallet/bag internal contents/cards match
    'unique_damage': 40.0,          # Unique private scratch, dent, tear, repair location
    'unique_engraving': 40.0,       # Unique custom engraving, embroidery, or marking
    'exact_key_count_fob': 45.0,    # Exact key count + distinct keychain description
    'photo_receipt_proof': 45.0,    # Owner previous photo with item or purchase receipt
    'wallpaper_lockscreen': 40.0,   # Private lock screen / wallpaper motif
    'custom_sticker_decal': 40.0,   # Specific custom stickers, badges, or charms

    # Medium Evidence (Distinctive when combined)
    'brand_model_exact': 20.0,      # Exact brand and specific model match
    'accessories_match': 20.0,      # Specific case, pouch, strap, eartip, charger
    'edition_annotation': 20.0,     # Book edition, notes, specific highlights
    'color_combination': 15.0,      # Specific primary + secondary color combo
    'location_proximity': 15.0,     # Proximity within 1 km or exact venue match
    'time_proximity': 15.0,         # Incident within 2 hours

    # Weak / Generic Supporting Evidence
    'generic_category': 5.0,        # Same category
    'generic_color': 5.0,           # Single common color (e.g. black, blue)
    'general_description': 5.0,     # General text overlap

    # Penalties
    'contradiction_penalty': -45.0, # Evidence directly contradicts (e.g. 5 keys vs 2 keys, wrong brand)
}

# ─── Category-Specific Verification Schemas & Blind Prompts ────────────────
CATEGORY_VERIFICATION_SCHEMAS = {
    'phone': {
        'label': 'Mobile Phone',
        'has_identifier': True,
        'identifier_name': 'IMEI or Serial Number (Optional)',
        'blind_prompts': [
            {
                'key': 'damage_or_case',
                'finder_prompt': 'Describe any visible scratch, dent, camera damage, or case characteristics on the phone.',
                'owner_prompt': 'Describe any unique physical damage, scratches, camera lens marks, or specific case details.',
                'weight': 'unique_damage',
            },
            {
                'key': 'wallpaper_or_lockscreen',
                'finder_prompt': 'If visible, describe the wallpaper, lock screen artwork, or custom sticker on the back.',
                'owner_prompt': 'Describe your lock screen wallpaper, artwork theme, or any sticker on the back.',
                'weight': 'wallpaper_lockscreen',
            },
            {
                'key': 'accessories_or_sim',
                'finder_prompt': 'Mention any accessories found with the phone (e.g., stylus, attached card holder, charger).',
                'owner_prompt': 'Describe any accessories attached or carried with the phone.',
                'weight': 'accessories_match',
            },
        ],
        'proof_types': ['Purchase invoice/receipt', 'Original box photo', 'Photo of phone prior to loss', 'IMEI/Serial proof'],
    },
    'laptop': {
        'label': 'Laptop',
        'has_identifier': True,
        'identifier_name': 'Service Tag, Serial Number, or Asset ID (Optional)',
        'blind_prompts': [
            {
                'key': 'stickers_or_damage',
                'finder_prompt': 'Describe any stickers, decals, skin, or unique scratches/dents on the laptop body or lid.',
                'owner_prompt': 'Describe any stickers, skin, distinctive scratches, or markings on the laptop lid or palm rest.',
                'weight': 'unique_damage',
            },
            {
                'key': 'keyboard_and_ports',
                'finder_prompt': 'Describe keyboard language/layout, missing keys, webcam cover, or port characteristics.',
                'owner_prompt': 'Describe any keyboard peculiarities, webcam cover, keyboard cover, or damage to ports.',
                'weight': 'unique_damage',
            },
            {
                'key': 'sleeve_or_charger',
                'finder_prompt': 'Describe any laptop sleeve, bag, or charger that was found with it.',
                'owner_prompt': 'Describe the laptop bag, sleeve, or charger carried with the laptop.',
                'weight': 'accessories_match',
            },
        ],
        'proof_types': ['Purchase invoice/receipt', 'Warranty registration / Box', 'Previous photo of laptop', 'Serial / Asset ID proof'],
    },
    'wallet': {
        'label': 'Wallet',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'internal_contents',
                'finder_prompt': 'List 2 or 3 non-public cards, vouchers, or specific items inside the wallet (do NOT list full ID numbers).',
                'owner_prompt': 'List the specific cards, memberships, loyalty cards, receipts, or items stored inside your wallet.',
                'weight': 'private_contents',
            },
            {
                'key': 'wallet_characteristics',
                'finder_prompt': 'Describe the wallet structure (bifold, trifold, coin pouch, zipper, material, inner lining color).',
                'owner_prompt': 'Describe the exact wallet style, material, inner lining color, or brand logo position.',
                'weight': 'brand_model_exact',
            },
            {
                'key': 'unique_wear_or_marks',
                'finder_prompt': 'Describe any unique wear, stitching tear, secret pocket contents, or stains.',
                'owner_prompt': 'Describe any specific wear, secret compartment contents, or unique marks on the wallet.',
                'weight': 'unique_damage',
            },
        ],
        'proof_types': ['Proof of cards inside', 'Receipt of purchase', 'Photo of wallet before loss'],
    },
    'bag': {
        'label': 'Bag / Backpack',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'internal_contents',
                'finder_prompt': 'List 2 or 3 distinctive items or notebooks found inside specific pockets of the bag.',
                'owner_prompt': 'List specific items, books, stationery, or personal items placed inside the bag.',
                'weight': 'private_contents',
            },
            {
                'key': 'keychains_or_pins',
                'finder_prompt': 'Describe any attached keychains, pins, badges, ribbons, or zipper pull modifications.',
                'owner_prompt': 'Describe any keychains, pins, tags, ribbons, or unique attachments on the bag.',
                'weight': 'custom_sticker_decal',
            },
            {
                'key': 'internal_label_or_damage',
                'finder_prompt': 'Describe the inner lining pattern/color, internal brand tag, or zipper damage/stains.',
                'owner_prompt': 'Describe the bag inner lining color, internal labels, or any tear/stain.',
                'weight': 'unique_damage',
            },
        ],
        'proof_types': ['Photo of bag prior to loss', 'Receipt / Brand tags', 'Proof of specific contents'],
    },
    'keys': {
        'label': 'Keys',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'key_count_and_types',
                'finder_prompt': 'State the exact number of keys on the ring and any distinctive key colors or rubber caps.',
                'owner_prompt': 'State the exact number of keys and describe any colored keys, rubber caps, or specific key shapes.',
                'weight': 'exact_key_count_fob',
            },
            {
                'key': 'keychain_trinket',
                'finder_prompt': 'Describe the keychain, lanyard, trinket, bottle opener, car fob, or decorative ring attached.',
                'owner_prompt': 'Describe the exact keychain, lanyard, car fob model, or trinket attached to your keys.',
                'weight': 'exact_key_count_fob',
            },
            {
                'key': 'tags_or_markings',
                'finder_prompt': 'Describe any tag, serial number, engraved text, or name written on any key or fob.',
                'owner_prompt': 'Describe any text, numbers, or tags present on any of the keys or fobs.',
                'weight': 'unique_engraving',
            },
        ],
        'proof_types': ['Spare key photo', 'Photo of keychain prior to loss', 'Car/bike registration for fob'],
    },
    'documents': {
        'label': 'Documents / ID Card',
        'has_identifier': True,
        'identifier_name': 'Document/Card Number (Masked - last 4 digits only)',
        'blind_prompts': [
            {
                'key': 'document_holder_or_name',
                'finder_prompt': 'State the document type and any holder/cover/lanyard color (do NOT write full sensitive private details).',
                'owner_prompt': 'Confirm the exact full name, issuing institution/authority, and document cover or sleeve details.',
                'weight': 'exact_identifier',
            },
            {
                'key': 'document_specific_details',
                'finder_prompt': 'State the issuing year, category (e.g. citizenship, student ID, license, passport), or card color scheme.',
                'owner_prompt': 'State the issuing year, document type, and any other items inside the document sleeve.',
                'weight': 'private_contents',
            },
        ],
        'proof_types': ['Copy/scan of document (with sensitive numbers masked)', 'Institutional enrollment proof / police report'],
    },
    'watch': {
        'label': 'Watch',
        'has_identifier': True,
        'identifier_name': 'Serial Number or Model Number (Optional)',
        'blind_prompts': [
            {
                'key': 'strap_and_clasp',
                'finder_prompt': 'Describe the strap/band material, color, buckle type, or link modifications.',
                'owner_prompt': 'Describe the watch strap material, color, buckle type, or size adjustments.',
                'weight': 'accessories_match',
            },
            {
                'key': 'engraving_or_scratch',
                'finder_prompt': 'Describe any custom engraving on the caseback, bezel scratches, or dial characteristics.',
                'owner_prompt': 'Describe any engraving on the back, unique scratches on the glass/bezel, or dial markers.',
                'weight': 'unique_engraving',
            },
        ],
        'proof_types': ['Purchase invoice/warranty card', 'Watch box / serial card', 'Photo wearing the watch'],
    },
    'jewelry': {
        'label': 'Jewelry',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'material_and_stones',
                'finder_prompt': 'Describe the metal color/type, stone shape/setting, clasp type, or hallmark stamp.',
                'owner_prompt': 'Describe the exact metal type, stone shape/color, clasp style, or hallmark/carat stamp.',
                'weight': 'unique_engraving',
            },
            {
                'key': 'engraving_or_custom',
                'finder_prompt': 'Describe any initials, date, or inscription engraved inside the jewelry.',
                'owner_prompt': 'Describe any custom initials, dates, or symbols engraved inside.',
                'weight': 'unique_engraving',
            },
        ],
        'proof_types': ['Jewelry appraisal/certificate', 'Purchase receipt', 'Clear photo wearing the jewelry'],
    },
    'headphones': {
        'label': 'Earbuds / Headphones',
        'has_identifier': True,
        'identifier_name': 'Serial Number (Optional)',
        'blind_prompts': [
            {
                'key': 'case_cover_or_skin',
                'finder_prompt': 'Describe any protective case cover, skin, lanyard, or stickers on the charging case/headset.',
                'owner_prompt': 'Describe any case cover, skin, charm, or stickers attached to your charging case or headset.',
                'weight': 'custom_sticker_decal',
            },
            {
                'key': 'eartips_and_damage',
                'finder_prompt': 'Describe eartip color/size, headband condition, cushion wear, or scratches.',
                'owner_prompt': 'Describe eartip size/color, headband wear, or specific scratches on the left/right earbud.',
                'weight': 'unique_damage',
            },
        ],
        'proof_types': ['Purchase receipt / box', 'Screenshot of connected Bluetooth device / Find My app', 'Serial number proof'],
    },
    'book': {
        'label': 'Books / Notes',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'handwritten_notes_or_name',
                'finder_prompt': 'Describe any handwritten name, dedication, notes, or inscriptions on the cover or inside pages.',
                'owner_prompt': 'Describe any name, notes, doodles, or inscriptions written inside the book.',
                'weight': 'unique_engraving',
            },
            {
                'key': 'bookmarks_and_highlights',
                'finder_prompt': 'Describe any bookmarks, inserted notes/papers, sticky tabs, or highlighting colors.',
                'owner_prompt': 'Describe any bookmark, inserted papers, sticky tabs, or specific highlighting inside.',
                'weight': 'edition_annotation',
            },
        ],
        'proof_types': ['Photo of book with handwritten notes', 'Receipt / Syllabus proof'],
    },
    'clothing': {
        'label': 'Clothing / Apparel',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'size_tag_and_modifications',
                'finder_prompt': 'State the exact brand, size on the tag, and describe any alterations, tailoring, or custom stitching.',
                'owner_prompt': 'State the exact brand, size tag, and describe any tailoring, alterations, or repairs.',
                'weight': 'unique_damage',
            },
            {
                'key': 'embroidery_or_marks',
                'finder_prompt': 'Describe any logo placement, embroidery, pin marks, unique stains, or pocket contents.',
                'owner_prompt': 'Describe any embroidery, logos, distinctive stains, or items left in the pockets.',
                'weight': 'private_contents',
            },
        ],
        'proof_types': ['Photo wearing the apparel', 'Purchase invoice / brand tag photo'],
    },
    'electronics': {
        'label': 'Electronics / Gadgets',
        'has_identifier': True,
        'identifier_name': 'Serial Number or Model (Optional)',
        'blind_prompts': [
            {
                'key': 'custom_labels_or_damage',
                'finder_prompt': 'Describe any custom labels, asset tags, battery compartment marks, or scratches.',
                'owner_prompt': 'Describe any custom labels, stickers, scratches, or unique hardware modifications.',
                'weight': 'unique_damage',
            },
            {
                'key': 'accessories_and_memory',
                'finder_prompt': 'Describe any cables, lens caps, memory cards, or carry pouch found with the gadget.',
                'owner_prompt': 'Describe any cables, memory card capacity, lens caps, or pouch carried with the item.',
                'weight': 'accessories_match',
            },
        ],
        'proof_types': ['Purchase receipt / original box', 'Previous photo with serial/specs', 'Warranty proof'],
    },
    'other': {
        'label': 'Other Item',
        'has_identifier': False,
        'blind_prompts': [
            {
                'key': 'distinctive_characteristics',
                'finder_prompt': 'Describe 2 or 3 distinctive physical features, marks, custom modifications, or private attributes.',
                'owner_prompt': 'Describe 2 or 3 distinctive private features, marks, custom alterations, or hidden details.',
                'weight': 'unique_damage',
            },
            {
                'key': 'accessories_or_packaging',
                'finder_prompt': 'Describe any pouch, box, container, or attached items found with it.',
                'owner_prompt': 'Describe any container, pouch, or accessories that accompanied the item.',
                'weight': 'accessories_match',
            },
        ],
        'proof_types': ['Clear photo of item before loss', 'Purchase receipt or ownership proof'],
    },
}
