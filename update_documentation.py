import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os
import shutil

SCREENSHOTS_DATA = [
    {
        "figure": "Figure 6.2.1",
        "title": "User Login & Authentication Interface",
        "file": "login1.png",
        "is_portrait": True,
        "desc": "The primary authentication gateway for returning community members, finders, and item owners. It verifies credentials against the PostgreSQL database via Django REST Framework JWT token authentication. It features secure password visibility toggling, client-side format validation, direct password recovery via email OTP, and quick navigation to new account registration.",
        "elements": [
            "Findora Branding & App Logo: Recognizable visual brand identity and greeting banner.",
            "Email / Username Input Field: Single validated text box accepting registered email or platform username.",
            "Password Input Field: Masked credential input with interactive eye icon to toggle visibility.",
            "Log In Action Button: High-contrast primary button dispatching authentication request and initializing secure session token caching.",
            "Forgot Password Link: Direct navigation trigger initiating the email OTP recovery flow.",
            "Sign Up Navigation: Bottom prompt allowing unregistered users to access the onboarding registration flow."
        ]
    },
    {
        "figure": "Figure 6.2.2",
        "title": "User Registration & Onboarding Screen",
        "file": "register 2.png",
        "is_portrait": True,
        "desc": "The onboarding interface allowing new users to create an account in the Findora ecosystem. It captures essential user profile information, enforces validation rules (unique username, email format, phone number, and password complexity matching), and generates a verified user record with default community reputation points.",
        "elements": [
            "Full Name & Username Inputs: Text fields capturing user legal name and unique community handle.",
            "Email & Contact Phone Inputs: Validated fields ensuring verified contact channels for item recovery notifications.",
            "Password & Confirm Password Inputs: Dual security fields enforcing matching complexity and encryption standards.",
            "Create Account Button: Primary submission button transmitting registration payload to the backend API.",
            "Existing User Prompt: Direct navigation link ('Already have an account? Log In') returning to the login gateway."
        ]
    },
    {
        "figure": "Figure 6.2.3",
        "title": "Finder Dashboard & Categorized Home Feed",
        "file": "finder dashboards 5.png",
        "is_portrait": True,
        "desc": "The central discovery hub of Findora displaying an aggregated feed of active lost and found items. It provides instant keyword search, dynamic category filter chips, visual status badges, and streamlined bottom navigation for seamless multitasking across the platform.",
        "elements": [
            "Real-time Search Bar: Top search field filtering listings dynamically by title, keyword, or landmark location.",
            "Category Filter Chips: Horizontally scrollable category selectors (All, Electronics, Wallet, Documents, Keys, Accessories, Books).",
            "Item Listing Cards: Card views displaying item thumbnail photo, title, discovery location, relative timestamp, and distinct status tags ('LOST' in red badge / 'FOUND' in green badge).",
            "Bottom Navigation Bar: Permanent 5-tab navigation bar granting one-tap access to Home, Search, Post Item, Messages, and Profile."
        ]
    },
    {
        "figure": "Figure 6.2.4",
        "title": "Item Details & Finder Action Overview",
        "file": "finderac 4.png",
        "is_portrait": True,
        "desc": "The detailed specification view for an individual item post. It presents high-resolution item imagery, categorized metadata, discovery location, and direct action triggers allowing legitimate owners to initiate contact or start ownership claim verification.",
        "elements": [
            "High-Resolution Image Viewer: Card-styled image preview supporting multi-touch pinch-to-zoom.",
            "Item Specification Card: Item title, category badge, reporting timestamp, and detailed condition description.",
            "Location & Map Section: Textual address details paired with a 'View Map' button triggering external Google Maps navigation.",
            "Contact & Claim Actions: Primary 'Contact Finder' button opening real-time encrypted chat, and 'Claim Item' button initiating ownership verification."
        ]
    },
    {
        "figure": "Figure 6.2.5",
        "title": "Report Lost Item Screen",
        "file": "report lost item.png",
        "is_portrait": True,
        "desc": "The structured submission form allowing owners to post a missing possession to the community network. It captures item categorization, unique identifying markers, date and time of loss, location landmarks, and optional reference photos to assist finders in identifying the property.",
        "elements": [
            "Category Dropdown Selector: Standardized classification menu (Electronics, Bags, Wallets, Cards, Jewelry, Others).",
            "Title and Description Inputs: Multi-line text areas capturing distinct visual traits, brand, model, and serial numbers.",
            "Date & Time Pickers: Interactive dialogs capturing approximate timeframe of loss.",
            "Location & Landmark Input: Address text box with optional GPS pin-point tagging.",
            "Media Attachment Uploader: Optional reference image picker supporting camera capture or gallery import.",
            "Submit Lost Report Button: Commits listing to backend database with immediate local cache synchronization."
        ]
    },
    {
        "figure": "Figure 6.2.6",
        "title": "Report Found Item Screen",
        "file": "reporting found item 6.png",
        "is_portrait": True,
        "desc": "The creation interface for community members who discover misplaced items. It facilitates photo capture, location tagging, and configuration of a secret ownership verification question that claimants must answer to prove genuine ownership.",
        "elements": [
            "Photo Upload Area: Mandatory high-clarity photo attachment supporting multi-image upload and compression.",
            "Item Title & Category: Input fields specifying discovered item name and category classification.",
            "Discovery Location & Time: Specific physical location (e.g. 'Library 2nd Floor, Desk 14') and discovery timestamp.",
            "Secret Ownership Question: Custom security question prompt configured by finder (e.g. 'What is written on the back keychain?').",
            "Post Found Item Action: Submits listing for administrative moderation and automatic community matching."
        ]
    },
    {
        "figure": "Figure 6.2.7",
        "title": "Item Claim Submission & Ownership Proof Interface",
        "file": "report item 3.png",
        "is_portrait": True,
        "desc": "The security checkpoint interface presented to potential claimants. To prevent false claims, it requires the user to submit detailed answers to the finder's security question along with optional supporting evidence such as purchase receipts or serial number certificates.",
        "elements": [
            "Item Summary Header: Reference ID, item name, and verification policy instructions.",
            "Finder's Security Question: Display of the secret verification question configured during found item reporting.",
            "Claimant Answer Field: Multi-line text field where claimant provides specific private details known only to the true owner.",
            "Proof Attachment Button: Optional uploader for proof documents, receipts, or previous photos of the item.",
            "Submit Claim Button: Routes verification request to the finder and system administrators for review."
        ]
    },
    {
        "figure": "Figure 6.2.8",
        "title": "Claim Verification & Return Handshake Status",
        "file": "report item 3.1.png",
        "is_portrait": True,
        "desc": "The active claim coordination view showing item status during verification and handover. It facilitates the dual-confirmation return protocol once physical handover occurs, rewarding the finder with reputation points and updating the item lifecycle state to resolved.",
        "elements": [
            "Lifecycle Status Banner: Visual indicator showing 'Claim Accepted – Handover in Progress'.",
            "Handshake Return Button: 'Confirm Return' button requiring dual-party confirmation from both owner and finder.",
            "Reputation & Star Rating Dialog: 5-star rating input and testimonial feedback submitted upon successful handover.",
            "Audit Timestamp Record: Chronological log recording initial post, claim acceptance, and handover completion."
        ]
    },
    {
        "figure": "Figure 6.2.9",
        "title": "1-on-1 Real-Time In-App Chat Interface",
        "file": "chat.png",
        "is_portrait": True,
        "desc": "The integrated end-to-end communication channel between finders and item owners. It enables instant text messaging, image sharing, message status indicators, hover action controls, and full context options (Copy, Edit, Delete for Me, Delete for Everyone).",
        "elements": [
            "Top Conversation Toolbar: Profile avatar, participant display name, and contextual role badge ('Finder' / 'Owner').",
            "Message Bubble Stream: Sent (purple) and received (dark surface) message bubbles with timestamps and '(Edited)' labels.",
            "Context Bottom Sheet: Modal offering 'Copy Message', 'Edit Message', 'Delete for Me', and 'Delete for Everyone'.",
            "Edit Mode Banner: Preview banner displaying original message text with a cancel (X) button above input field.",
            "Input Bar & Attachments: Camera/gallery attachment button, multi-line text input field, and floating Send button."
        ]
    },
    {
        "figure": "Figure 6.2.10",
        "title": "Administrator Panel – Item Moderation Registry",
        "file": "verify item1.png",
        "is_portrait": False,
        "desc": "The desktop web console used by platform administrators to monitor, review, and moderate all submitted lost and found listings across the platform.",
        "elements": [
            "Item Moderation Table: Tabular view displaying Item ID, Title, Category, Reporter Username, Report Type (Lost/Found), Timestamp, and Status.",
            "Status Filter Tabs: Quick filters for 'Pending Review', 'Approved', 'Flagged', and 'Resolved' listings.",
            "Search & Search Input: Global keyword search for locating specific reports or accounts.",
            "Action Controls: Individual action buttons per listing ('View Detail', 'Approve', 'Flag / Reject')."
        ]
    },
    {
        "figure": "Figure 6.2.11",
        "title": "Admin Item Detail & Ownership Verification View",
        "file": "verify item2.png",
        "is_portrait": False,
        "desc": "The in-depth administrative inspection view allowing moderators to examine uploaded evidence photos, claimant verification answers, and conflicting ownership claims to ensure fair dispute resolution.",
        "elements": [
            "High-Resolution Proof Viewer: Full-size side-by-side inspection of found item photo and claimant proof submission.",
            "Claimant & Finder Reputation Profile: Overview of user trust scores, account age, and return history.",
            "Secret Question & Answer Comparison Box: Side-by-side display of finder's question and claimant's response for verification audit.",
            "Dispute Resolution Override: Administrative override controls allowing direct approval or request for additional proof."
        ]
    },
    {
        "figure": "Figure 6.2.12",
        "title": "Admin Item Approval & Moderation Decision Workflow",
        "file": "verify item 3.png",
        "is_portrait": False,
        "desc": "The decision execution interface where administrators finalize moderation actions, log regulatory notes, and broadcast approved listings to the community feed.",
        "elements": [
            "Moderation Decision Selector: Dropdown / radio options to set status to 'Approved', 'Under Review', or 'Rejected'.",
            "Admin Reason / Notes Box: Mandatory explanation field for rejected or flagged listings sent directly to the user.",
            "Save & Update Status Button: Commits changes to the database and broadcasts push notifications to matched users.",
            "Audit Log: Timestamped log of previous administrative actions and moderator remarks."
        ]
    },
    {
        "figure": "Figure 6.2.13",
        "title": "Master Administration Dashboard & Platform Analytics",
        "file": "Admin panel.png",
        "is_portrait": False,
        "desc": "The executive administrative dashboard presenting platform-wide metrics, user activity statistics, return success rates, reputation point economy analytics, and server health monitoring.",
        "elements": [
            "KPI Summary Metric Cards: Total Registered Users, Active Lost Reports, Active Found Reports, Successful Returns, and Recovery Rate.",
            "Real-Time Activity Stream: Live feed of recent registrations, claim submissions, and confirmed handovers.",
            "System Health Monitor: API response latency, database connection pool, and storage utilization.",
            "Navigation Sidebar: Direct access to User Accounts, Item Listings, Claims, Transactions, Notifications, and System Configuration."
        ]
    }
]

def update_complete_document():
    src_file = "Final_Document_Format_Complete_Diagrams.docx"
    backup_file = "Final_Document_Format_Complete_Diagrams.backup.docx"
    shutil.copyfile(src_file, backup_file)
    print(f"Backup created: {backup_file}")

    doc = docx.Document(src_file)

    # 1. Update List of Figures (Table 4)
    table_lof = doc.tables[4]
    
    # Remove rows from row 23 onwards (which were Figure 6.2.1 to 6.2.5 placeholders)
    # Let's inspect rows first
    rows_to_delete = []
    for idx, row in enumerate(table_lof.rows):
        if idx > 0 and len(row.cells) >= 1:
            first_cell_text = row.cells[0].text.strip()
            if first_cell_text.startswith("Figure 6.2."):
                rows_to_delete.append(row)
    
    for row in rows_to_delete:
        row._tr.getparent().remove(row._tr)

    # Add updated Figure 6.2.1 through 6.2.13 rows
    start_page = 36
    for idx, item in enumerate(SCREENSHOTS_DATA):
        fig_num = item["figure"]
        fig_title = item["title"]
        page_num = str(start_page + (idx // 2))
        
        row_cells = table_lof.add_row().cells
        row_cells[0].text = fig_num
        row_cells[1].text = fig_title
        row_cells[2].text = page_num
        
        # Format font
        for c_idx, cell in enumerate(row_cells):
            cell.paragraphs[0].runs[0].font.name = "Times New Roman"
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            if c_idx != 1:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    print("Table 4 (List of Figures) updated.")

    # 2. Find Chapter 6 and Chapter 7 indices
    p_ch6_2_idx = None
    p_ch7_idx = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "6.2 App Snapshots":
            p_ch6_2_idx = i
        if p.text.strip() == "CHAPTER 7: CONCLUSION":
            p_ch7_idx = i

    print(f"Target indices: 6.2 idx={p_ch6_2_idx}, Ch7 idx={p_ch7_idx}")

    target_p = doc.paragraphs[p_ch7_idx]

    # Insert Section 6.2 Heading & Intro
    target_p.insert_paragraph_before("6.2 App Snapshots and Interface Documentation", "Heading 2")
    
    p_intro = target_p.insert_paragraph_before(
        "This section provides comprehensive screen-by-screen documentation of the Findora platform across the native Android mobile application and the web-based Administrator moderation console. Each subsection details the primary purpose, user interaction pathways, architectural significance, embedded actual application snapshot, and exhaustive breakdown of key user interface components.",
        "Normal"
    )
    p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p_intro.runs:
        p_intro.runs[0].font.name = "Times New Roman"
        p_intro.runs[0].font.size = Pt(12)

    # Insert each screenshot subsection
    for idx, item in enumerate(SCREENSHOTS_DATA):
        sub_heading = f"6.2.{idx + 1} {item['title']}"
        target_p.insert_paragraph_before(sub_heading, "Heading 3")
        
        # Description paragraph
        p_desc = target_p.insert_paragraph_before(item["desc"], "Normal")
        p_desc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if p_desc.runs:
            p_desc.runs[0].font.name = "Times New Roman"
            p_desc.runs[0].font.size = Pt(12)

        # Image paragraph (centered)
        p_img = target_p.insert_paragraph_before()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_img = p_img.add_run()
        img_width = Inches(2.85) if item["is_portrait"] else Inches(5.5)
        run_img.add_picture(item["file"], width=img_width)

        # Caption paragraph (centered, bold)
        caption_text = f"{item['figure']} – {item['title']}"
        p_cap = target_p.insert_paragraph_before(caption_text, "Normal")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p_cap.runs:
            p_cap.runs[0].font.name = "Times New Roman"
            p_cap.runs[0].font.size = Pt(10.5)
            p_cap.runs[0].bold = True

        # Key UI Elements Header
        p_key_hdr = target_p.insert_paragraph_before("Key UI Elements:", "Normal")
        if p_key_hdr.runs:
            p_key_hdr.runs[0].font.name = "Times New Roman"
            p_key_hdr.runs[0].font.size = Pt(11)
            p_key_hdr.runs[0].bold = True

        # Bullet items
        for elem in item["elements"]:
            p_bullet = target_p.insert_paragraph_before(f"• {elem}", "Normal")
            p_bullet.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_bullet.paragraph_format.left_indent = Inches(0.25)
            if p_bullet.runs:
                p_bullet.runs[0].font.name = "Times New Roman"
                p_bullet.runs[0].font.size = Pt(11)

        # Spacing paragraph
        target_p.insert_paragraph_before("", "Normal")

    # Insert Section 6.3: Comprehensive User Documentation & Operational Guidelines
    target_p.insert_paragraph_before("6.3 Operational Workflow and User Guidelines", "Heading 2")
    
    workflow_text_1 = (
        "Findora provides a unified, step-by-step workflow designed to streamline lost item recovery while eliminating fraud and maintaining complete transactional accountability. The end-to-end operational lifecycle spans eight primary phases:"
    )
    p_wf1 = target_p.insert_paragraph_before(workflow_text_1, "Normal")
    p_wf1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p_wf1.runs:
        p_wf1.runs[0].font.name = "Times New Roman"
        p_wf1.runs[0].font.size = Pt(12)

    workflows = [
        ("1. User Onboarding & Security Authentication", "Users register with validated email and contact credentials. Authentication tokens are securely managed via Android EncryptedSharedPreferences and Django REST Framework JWT tokens."),
        ("2. Reporting Lost Belongings", "Owners document missing items by selecting category, entering distinct descriptive identifiers, setting loss date/time, providing location context, and uploading optional reference photos."),
        ("3. Posting Discovered Property", "Finders photograph discovered items, specify the discovery location/time, and define a secret verification question that only the rightful owner can accurately answer."),
        ("4. Automated Matching & Community Discovery", "The platform indexes active reports in real time, notifying owners when a matching found item is logged within the same spatial-temporal proximity."),
        ("5. Secure Ownership Claim Submission", "Claimants review item details and submit private answers to the secret question along with optional evidence (purchase receipts or serial numbers)."),
        ("6. 1-on-1 End-to-End Encrypted Coordination", "Finders and owners communicate via real-time in-app chat to coordinate a safe public handover location without sharing private phone numbers."),
        ("7. Dual-Confirmation Handshake & Reputation Rating", "Upon physical item return, both parties click 'Confirm Return'. The system marks the item resolved, awards community reputation points, and collects finder star ratings."),
        ("8. Administrative Oversight & Moderation", "Platform moderators review flagged posts, audit disputed claims, verify proof documents, and manage community trust scores via the web admin console.")
    ]

    for title, desc in workflows:
        p_step = target_p.insert_paragraph_before(f"{title}: {desc}", "Normal")
        p_step.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_step.paragraph_format.left_indent = Inches(0.25)
        if p_step.runs:
            p_step.runs[0].font.name = "Times New Roman"
            p_step.runs[0].font.size = Pt(11)

    target_p.insert_paragraph_before("", "Normal")

    # Now remove old paragraphs from p_ch6_2_idx to p_ch7_idx - 1
    # We must collect the elements to remove
    to_remove = []
    record = False
    for p in doc.paragraphs:
        if p.text.strip() == "6.2 App Snapshots":
            record = True
        if p.text.strip() == "6.2 App Snapshots and Interface Documentation":
            record = False
        if record:
            to_remove.append(p)

    for p in to_remove:
        p._element.getparent().remove(p._element)

    doc.save(src_file)
    print(f"Updated {src_file} successfully!")


def create_standalone_documentation():
    dest_file = "documentation.docx"
    doc = docx.Document()

    # Set page margins (A4, Left=1.5 in, Right=1.0 in, Top=1.0 in, Bottom=1.0 in)
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # Document Title Page / Header
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("FINDORA: COMMUNITY-DRIVEN LOST AND FOUND PLATFORM\n")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(18)
    r_title.font.color.rgb = RGBColor(0x3B, 0x34, 0x82)

    r_sub = p_title.add_run("Comprehensive System & User Interface Documentation\n")
    r_sub.bold = True
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = RGBColor(0x53, 0x4A, 0xB7)

    r_meta = p_title.add_run("Android Client Application & Web Administrative Console\n\n")
    r_meta.italic = True
    r_meta.font.name = "Times New Roman"
    r_meta.font.size = Pt(11)

    # Divider
    p_div = doc.add_paragraph("―" * 45)
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Executive Overview
    p_h1 = doc.add_paragraph("1. Project Overview & Architecture", "Heading 1")
    p_ov = doc.add_paragraph(
        "Findora is a community-driven digital lost and found ecosystem engineered to streamline the recovery of misplaced personal property across university campuses and local communities. By replacing unstructured social media posts and manual physical desks with a centralized, verified digital repository, Findora delivers structured item categorization, secret verification question proof-of-ownership, dual-confirmation return handshakes, real-time 1-on-1 chat, and community reputation incentives."
    )
    p_ov.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p_ov.runs:
        p_ov.runs[0].font.name = "Times New Roman"
        p_ov.runs[0].font.size = Pt(12)

    # Key Architectural Highlights
    p_h2 = doc.add_paragraph("2. Technical Framework & System Stack", "Heading 1")
    tech_points = [
        ("Mobile Client", "Native Android developed in Java 17 / Android SDK 35 utilizing ViewBinding, Material Design 3 UI components, Retrofit 2 REST networking, and Glide image pipeline."),
        ("Backend Services", "Django REST Framework 5.1 with Python 3.12, PostgreSQL relational database, Redis cache, and Gunicorn / Daphne ASGI server."),
        ("Security & Moderation", "JWT token authentication, bcrypt password hashing, role-based access control, and dedicated web-based administrative moderation console."),
        ("Real-time Messaging", "In-app 1-on-1 messaging with full multi-device support, message editing, message deletion (for me / for everyone), hover actions, and right-click context menu.")
    ]
    for k, v in tech_points:
        p_tp = doc.add_paragraph(f"• {k}: {v}")
        p_tp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_tp.paragraph_format.left_indent = Inches(0.25)
        if p_tp.runs:
            p_tp.runs[0].font.name = "Times New Roman"
            p_tp.runs[0].font.size = Pt(11)

    # Section 3: Screen-by-Screen User & Admin Interface Documentation
    doc.add_paragraph("3. Screen-by-Screen User & Administrator Documentation", "Heading 1")
    p_s_intro = doc.add_paragraph(
        "This section documents all 13 core application screens across the mobile application and administrative portal. Each screen is presented with its purpose, operational details, embedded high-resolution screenshot, and key user interface elements."
    )
    p_s_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p_s_intro.runs:
        p_s_intro.runs[0].font.name = "Times New Roman"
        p_s_intro.runs[0].font.size = Pt(12)

    for idx, item in enumerate(SCREENSHOTS_DATA):
        doc.add_paragraph(f"3.{idx + 1} {item['title']}", "Heading 2")
        
        p_desc = doc.add_paragraph(item["desc"])
        p_desc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if p_desc.runs:
            p_desc.runs[0].font.name = "Times New Roman"
            p_desc.runs[0].font.size = Pt(12)

        # Image paragraph
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_img = p_img.add_run()
        img_width = Inches(2.85) if item["is_portrait"] else Inches(5.5)
        run_img.add_picture(item["file"], width=img_width)

        # Caption
        p_cap = doc.add_paragraph(f"Figure {idx + 1} – {item['title']}")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p_cap.runs:
            p_cap.runs[0].font.name = "Times New Roman"
            p_cap.runs[0].font.size = Pt(10.5)
            p_cap.runs[0].bold = True

        # Key UI Elements
        p_key_hdr = doc.add_paragraph("Key UI Elements:")
        if p_key_hdr.runs:
            p_key_hdr.runs[0].font.name = "Times New Roman"
            p_key_hdr.runs[0].font.size = Pt(11)
            p_key_hdr.runs[0].bold = True

        for elem in item["elements"]:
            p_bullet = doc.add_paragraph(f"• {elem}")
            p_bullet.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_bullet.paragraph_format.left_indent = Inches(0.25)
            if p_bullet.runs:
                p_bullet.runs[0].font.name = "Times New Roman"
                p_bullet.runs[0].font.size = Pt(11)

        doc.add_paragraph()

    # Section 4: Operational Workflow & Guidelines
    doc.add_paragraph("4. Operational Workflow & User Guidelines", "Heading 1")
    p_w_intro = doc.add_paragraph(
        "Findora incorporates an intuitive end-to-end recovery lifecycle designed to guide users seamlessly from initial item loss through secure claim validation and confirmed return:"
    )
    p_w_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if p_w_intro.runs:
        p_w_intro.runs[0].font.name = "Times New Roman"
        p_w_intro.runs[0].font.size = Pt(12)

    workflows = [
        ("1. User Registration & Profile Setup", "New users create a verified account with legal name, contact credentials, and avatar. Session tokens are securely cached for seamless app launches."),
        ("2. Reporting a Lost Possession", "Owners specify item category, detailed descriptors, approximate loss timeframe, location context, and optional reference photos."),
        ("3. Reporting a Discovered Found Item", "Finders photograph discovered items, input discovery location/time, and configure a secret proof question that only the rightful owner can answer."),
        ("4. Community Matching & Notification Dispatch", "The platform dynamically matches item descriptors across categories and spatial coordinates, broadcasting immediate alerts to potential owners."),
        ("5. Ownership Verification & Claim Submission", "Claimants submit private answers to the secret question and upload supporting evidence (receipts, serial certificates, photos) for review."),
        ("6. In-App Communication & Handover Coordination", "Finders and owners coordinate a safe public handover location via real-time encrypted in-app chat."),
        ("7. Dual-Confirmation Handshake & Reputation Rating", "Both parties tap 'Confirm Return' upon physical item exchange, awarding reputation points and recording 5-star finder ratings."),
        ("8. Admin Moderation & Dispute Resolution", "Platform administrators oversee flagged listings, review disputed ownership submissions, and maintain community integrity via the web admin panel.")
    ]

    for title, desc in workflows:
        p_step = doc.add_paragraph(f"{title}: {desc}")
        p_step.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_step.paragraph_format.left_indent = Inches(0.25)
        if p_step.runs:
            p_step.runs[0].font.name = "Times New Roman"
            p_step.runs[0].font.size = Pt(11)

    doc.save(dest_file)
    print(f"Created standalone {dest_file} successfully!")


if __name__ == "__main__":
    update_complete_document()
    create_standalone_documentation()
