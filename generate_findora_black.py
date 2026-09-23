import os
import docx
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION

from doc_helpers import (
    set_cell_background, set_cell_margins, set_table_borders,
    add_styled_paragraph, add_heading_1, add_heading_2, add_heading_3, add_heading_4,
    add_body_p, add_bullet_item, add_figure_caption, add_table_caption,
    insert_image, add_custom_table
)

def build_document():
    print("Starting generation of findora_black.docx with mockups and clean topic page breaks...")
    doc = docx.Document()

    # Define Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)

    # =========================================================================
    # SECTION 1: PRELIMINARY PAGES (Roman Numerals i, ii, iii...)
    # =========================================================================
    sec1 = doc.sections[0]
    sec1.page_width = Inches(8.27)   # A4 Width (210mm)
    sec1.page_height = Inches(11.69) # A4 Height (297mm)
    sec1.left_margin = Inches(1.5)   # 1.5 inch binding margin
    sec1.right_margin = Inches(1.0)  # 1.0 inch margin
    sec1.top_margin = Inches(1.0)    # 1.0 inch margin
    sec1.bottom_margin = Inches(1.0) # 1.0 inch margin

    # Configure Roman Page Numbering for Section 1
    sectPr1 = sec1._sectPr
    pgNumType1 = OxmlElement('w:pgNumType')
    pgNumType1.set(qn('w:fmt'), 'roman')
    pgNumType1.set(qn('w:start'), '1')
    sectPr1.append(pgNumType1)

    # Preliminary Footer (Right-aligned, Times New Roman 10pt)
    footer1 = sec1.footer
    fp1 = footer1.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run1 = fp1.add_run()
    fld1 = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    f_run1._r.append(fld1)
    f_run1.font.name = 'Times New Roman'
    f_run1.font.size = Pt(10)
    f_run1.font.color.rgb = RGBColor(0, 0, 0)

    # -------------------------------------------------------------------------
    # 1. TITLE PAGE
    # -------------------------------------------------------------------------
    p_t1 = doc.add_paragraph()
    p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1.paragraph_format.space_before = Pt(36)
    p_t1.paragraph_format.space_after = Pt(12)
    r_t1 = p_t1.add_run("A Project Report")
    r_t1.font.name = 'Times New Roman'
    r_t1.font.size = Pt(16)
    r_t1.bold = True

    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_before = Pt(18)
    p_t2.paragraph_format.space_after = Pt(6)
    r_t2 = p_t2.add_run("FINDORA: COMMUNITY-DRIVEN LOST AND FOUND PLATFORM")
    r_t2.font.name = 'Times New Roman'
    r_t2.font.size = Pt(18)
    r_t2.bold = True

    p_t2sub = doc.add_paragraph()
    p_t2sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2sub.paragraph_format.space_before = Pt(0)
    p_t2sub.paragraph_format.space_after = Pt(24)
    r_t2sub = p_t2sub.add_run("(A Web and Mobile-Based Item Recovery and Ownership Verification System)")
    r_t2sub.font.name = 'Times New Roman'
    r_t2sub.font.size = Pt(12)
    r_t2sub.italic = True

    p_t3 = doc.add_paragraph()
    p_t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3.paragraph_format.space_before = Pt(12)
    p_t3.paragraph_format.space_after = Pt(4)
    r_t3 = p_t3.add_run("In partial fulfillment for the degree of BCA under")
    r_t3.font.name = 'Times New Roman'
    r_t3.font.size = Pt(12)

    p_t4 = doc.add_paragraph()
    p_t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4.paragraph_format.space_before = Pt(0)
    p_t4.paragraph_format.space_after = Pt(24)
    r_t4 = p_t4.add_run("Pokhara University")
    r_t4.font.name = 'Times New Roman'
    r_t4.font.size = Pt(14)
    r_t4.bold = True

    p_t5 = doc.add_paragraph()
    p_t5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5.paragraph_format.space_before = Pt(12)
    p_t5.paragraph_format.space_after = Pt(4)
    r_t5 = p_t5.add_run("Submitted to")
    r_t5.font.name = 'Times New Roman'
    r_t5.font.size = Pt(12)

    p_t6 = doc.add_paragraph()
    p_t6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t6.paragraph_format.space_before = Pt(0)
    p_t6.paragraph_format.space_after = Pt(2)
    r_t6 = p_t6.add_run("Oxford College of Engineering and Management")
    r_t6.font.name = 'Times New Roman'
    r_t6.font.size = Pt(14)
    r_t6.bold = True

    p_t7 = doc.add_paragraph()
    p_t7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t7.paragraph_format.space_before = Pt(0)
    p_t7.paragraph_format.space_after = Pt(24)
    r_t7 = p_t7.add_run("Bachelor of Computer Application (BCA) Program\nGaindakot, Nawalpur, Nepal")
    r_t7.font.name = 'Times New Roman'
    r_t7.font.size = Pt(12)

    p_t8 = doc.add_paragraph()
    p_t8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t8.paragraph_format.space_before = Pt(12)
    p_t8.paragraph_format.space_after = Pt(4)
    r_t8 = p_t8.add_run("Under the guidance of")
    r_t8.font.name = 'Times New Roman'
    r_t8.font.size = Pt(12)

    p_t9 = doc.add_paragraph()
    p_t9.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t9.paragraph_format.space_before = Pt(0)
    p_t9.paragraph_format.space_after = Pt(24)
    r_t9 = p_t9.add_run("Asst. Prof Anil Thapaliya\nAsst. Prof Shiva Bahadur Pathak")
    r_t9.font.name = 'Times New Roman'
    r_t9.font.size = Pt(12)
    r_t9.bold = True

    p_t10 = doc.add_paragraph()
    p_t10.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t10.paragraph_format.space_before = Pt(12)
    p_t10.paragraph_format.space_after = Pt(4)
    r_t10 = p_t10.add_run("Submitted by")
    r_t10.font.name = 'Times New Roman'
    r_t10.font.size = Pt(12)

    p_t11 = doc.add_paragraph()
    p_t11.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t11.paragraph_format.space_before = Pt(0)
    p_t11.paragraph_format.space_after = Pt(36)
    r_t11 = p_t11.add_run("Bivek Kafle, BCA 8th Semester, 22530190\nLaxman Rawat, BCA 8th Semester, 22530204")
    r_t11.font.name = 'Times New Roman'
    r_t11.font.size = Pt(12)
    r_t11.bold = True

    p_t12 = doc.add_paragraph()
    p_t12.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t12.paragraph_format.space_before = Pt(12)
    p_t12.paragraph_format.space_after = Pt(0)
    r_t12 = p_t12.add_run("September, 2026")
    r_t12.font.name = 'Times New Roman'
    r_t12.font.size = Pt(12)
    r_t12.bold = True

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 2. ROLES AND RESPONSIBILITIES (Page ii)
    # -------------------------------------------------------------------------
    p_rr_head = doc.add_paragraph()
    p_rr_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rr_head.paragraph_format.space_before = Pt(12)
    p_rr_head.paragraph_format.space_after = Pt(12)
    r_rr = p_rr_head.add_run("ROLES AND RESPONSIBILITIES")
    r_rr.font.name = 'Times New Roman'
    r_rr.font.size = Pt(16)
    r_rr.bold = True

    add_body_p(doc, "This section outlines the specific roles and individual technical responsibilities of each team member involved in the engineering, design, implementation, testing, and documentation of the Findora project. Clearly defined roles and responsibilities supported effective team collaboration, systematic version control workflows, architectural modularity, accountability, and smooth execution across the entire software development lifecycle.")

    rr_headers = ["Team Member", "Role", "Technical Responsibilities"]
    rr_data = [
        [
            "Laxman Rawat\n(22530204)",
            "Project Lead /\nAndroid & UI/UX Developer",
            "• Architected the native Android client application utilizing Java, XML, and Material Design 3 guidelines.\n• Designed and implemented intuitive UI layouts for onboarding, item reporting, filtering, and discovery.\n• Developed the real-time 1-on-1 in-app messaging interface, supporting text, image sharing, editing, and soft deletion.\n• Integrated camera and gallery photo capture with dynamic client-side image compression.\n• Conducted comprehensive mobile functional, responsiveness, and usability evaluations."
        ],
        [
            "Bivek Kafle\n(22530190)",
            "Backend Architect /\nDatabase Lead & QA",
            "• Designed and normalized the relational database schema in PostgreSQL conforming to Third Normal Form (3NF).\n• Built and deployed secure RESTful APIs using Python, Django, and Django REST Framework (DRF).\n• Engineered the weighted multi-attribute matching algorithm to calculate item similarity scores.\n• Integrated the eSewa EPAY digital payment gateway for featured item promotions.\n• Developed the web-based administrative moderation dashboard and executed backend unit/stress test suites."
        ]
    ]
    add_custom_table(doc, rr_headers, rr_data, col_widths=[1.5, 1.8, 3.5])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 3. STUDENTS' DECLARATION (Page iii)
    # -------------------------------------------------------------------------
    p_dec_head = doc.add_paragraph()
    p_dec_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_head.paragraph_format.space_before = Pt(12)
    p_dec_head.paragraph_format.space_after = Pt(18)
    r_dec = p_dec_head.add_run("STUDENTS' DECLARATION")
    r_dec.font.name = 'Times New Roman'
    r_dec.font.size = Pt(16)
    r_dec.bold = True

    add_body_p(doc, "We hereby declare that this project report titled \"FINDORA: Community-Driven Lost and Found Platform\" is our original work carried out under the supervision and guidance of our designated project supervisors. We are the only authors of this project, and it has not been submitted elsewhere, in whole or in part, for the award of any degree, diploma, or academic certificate to Pokhara University or any other academic institution.")

    add_body_p(doc, "We also declare that no sources other than the ones explicitly listed in the References section have been used in this work, and that all citations, quotations, external resources, and foundational literature have been duly acknowledged in accordance with academic integrity and ethical guidelines.")

    add_body_p(doc, "We accept full responsibility for the authenticity, technical accuracy, and originality of the system implementation, design artifacts, and report documentation presented herein.")

    p_sig_space = doc.add_paragraph()
    p_sig_space.paragraph_format.space_before = Pt(36)
    p_sig_space.paragraph_format.space_after = Pt(18)

    sig_headers = ["Student Name", "Symbol Number", "Signature"]
    sig_data = [
        ["Bivek Kafle", "22530190", "_______________________"],
        ["Laxman Rawat", "22530204", "_______________________"]
    ]
    add_custom_table(doc, sig_headers, sig_data, col_widths=[2.3, 2.0, 2.5])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 4. SUPERVISOR'S RECOMMENDATION (Page iv)
    # -------------------------------------------------------------------------
    p_rec_head = doc.add_paragraph()
    p_rec_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rec_head.paragraph_format.space_before = Pt(12)
    p_rec_head.paragraph_format.space_after = Pt(18)
    r_rec = p_rec_head.add_run("SUPERVISOR'S RECOMMENDATION")
    r_rec.font.name = 'Times New Roman'
    r_rec.font.size = Pt(16)
    r_rec.bold = True

    add_body_p(doc, "We hereby recommend that the project report entitled \"FINDORA: Community-Driven Lost and Found Platform\", prepared and submitted by Bivek Kafle (PU Symbol No: 22530190) and Laxman Rawat (PU Symbol No: 22530204) during their 8th semester in partial fulfillment of the requirements for the degree of Bachelor of Computer Application (BCA) under Pokhara University, is an authentic record of original project work completed under our guidance and supervision.")

    add_body_p(doc, "Throughout the duration of the project, the candidates demonstrated commendable technical diligence, problem-solving ability, software engineering competency, and professional collaboration. The work satisfies the academic scope, functional criteria, and formatting requirements prescribed by Pokhara University and is to our complete satisfaction for final evaluation and project defense.")

    p_rec_sig = doc.add_paragraph()
    p_rec_sig.paragraph_format.space_before = Pt(48)
    p_rec_sig.paragraph_format.space_after = Pt(12)

    sup_headers = ["Project Supervisor 1", "Project Supervisor 2"]
    sup_data = [
        [
            "_____________________________\nAsst. Prof Anil Thapaliya\nProject Supervisor\nDepartment of Computer Application\nDate: _______________________",
            "_____________________________\nAsst. Prof Shiva Bahadur Pathak\nProject Supervisor\nDepartment of Computer Application\nDate: _______________________"
        ]
    ]
    add_custom_table(doc, sup_headers, sup_data, col_widths=[3.4, 3.4])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 5. LETTER OF APPROVAL (Page v)
    # -------------------------------------------------------------------------
    p_app_head = doc.add_paragraph()
    p_app_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_app_head.paragraph_format.space_before = Pt(12)
    p_app_head.paragraph_format.space_after = Pt(18)
    r_app = p_app_head.add_run("LETTER OF APPROVAL")
    r_app.font.name = 'Times New Roman'
    r_app.font.size = Pt(16)
    r_app.bold = True

    add_body_p(doc, "We certify that we have thoroughly examined the project report titled \"FINDORA: Community-Driven Lost and Found Platform\", prepared and submitted by Bivek Kafle and Laxman Rawat in partial fulfillment of the requirements for the degree of Bachelor of Computer Application (BCA) under Pokhara University.")

    add_body_p(doc, "We have evaluated the software deliverables, reviewed the architectural design, inspected the backend APIs and mobile client interfaces, and examined the candidates' performance during the final oral project defense. Based on our comprehensive evaluation, we certify that the project satisfies the technical scope, practical applicability, and academic standards demanded by Pokhara University.")

    p_eval_space = doc.add_paragraph()
    p_eval_space.paragraph_format.space_before = Pt(36)
    p_eval_space.paragraph_format.space_after = Pt(12)

    eval_headers = ["Project Supervisor", "External Examiner", "Program Coordinator"]
    eval_data = [
        [
            "______________________\nSupervisor\nDate: ________________",
            "______________________\nExternal Examiner\nDate: ________________",
            "______________________\nSusant Tiwari\nHOD / Coordinator\nDate: ________________"
        ]
    ]
    add_custom_table(doc, eval_headers, eval_data, col_widths=[2.3, 2.3, 2.3])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 6. ACKNOWLEDGEMENTS (Page vi)
    # -------------------------------------------------------------------------
    p_ack_head = doc.add_paragraph()
    p_ack_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_head.paragraph_format.space_before = Pt(12)
    p_ack_head.paragraph_format.space_after = Pt(18)
    r_ack = p_ack_head.add_run("ACKNOWLEDGEMENTS")
    r_ack.font.name = 'Times New Roman'
    r_ack.font.size = Pt(16)
    r_ack.bold = True

    add_body_p(doc, "We would like to express our deepest gratitude and profound appreciation to our esteemed project supervisors, Asst. Prof Anil Thapaliya and Asst. Prof Shiva Bahadur Pathak, for their invaluable mentorship, insightful technical suggestions, continuous encouragement, and constructive critique throughout the conceptualization, system architecture, coding, and documentation phases of Findora.")

    add_body_p(doc, "We extend our heartfelt thanks to Er. Hari Bhandari, Principal of Oxford College of Engineering and Management, and Mr. Susant Tiwari, Head of the Department of Computer Application, for providing an intellectually stimulating environment, excellent computing lab facilities, and necessary institutional support during our undergraduate journey.")

    add_body_p(doc, "We also express our sincere appreciation to all respected faculty members of the Department of Computer Application whose dedicated teaching laid our foundational knowledge in software engineering, database management systems, mobile computing, and computer networks under the Pokhara University curriculum.")

    add_body_p(doc, "Special thanks are extended to our peers, beta testers, and community participants who actively tested the Android mobile client, provided critical feedback on usability, and helped identify edge cases in the item recovery and matching workflows.")

    add_body_p(doc, "Finally, we owe our deepest debt of gratitude to our beloved parents and family members whose unwavering moral encouragement, unconditional love, sacrifices, and belief in our aspirations enabled us to successfully bring this project to a fruitful completion.")

    p_ack_auth = doc.add_paragraph()
    p_ack_auth.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_ack_auth.paragraph_format.space_before = Pt(24)
    r_auth = p_ack_auth.add_run("Bivek Kafle (22530190)\nLaxman Rawat (22530204)\nBCA 8th Semester")
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(12)
    r_auth.bold = True

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 7. ABSTRACT (Page vii)
    # -------------------------------------------------------------------------
    p_abs_head = doc.add_paragraph()
    p_abs_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_head.paragraph_format.space_before = Pt(12)
    p_abs_head.paragraph_format.space_after = Pt(18)
    r_abs = p_abs_head.add_run("ABSTRACT")
    r_abs.font.name = 'Times New Roman'
    r_abs.font.size = Pt(16)
    r_abs.bold = True

    add_body_p(doc, "In contemporary urban, institutional, and commercial environments, misplaced personal belongings represent a frequent and distressing occurrence. Traditional lost-and-found management systems in Nepal rely heavily on unstructured social media posts, physical inquiry desks, or informal notice boards. These conventional mechanisms suffer from severe limitations, including geographic fragmentation, absence of standardized metadata, high communication friction, vulnerability to fraudulent claims, and lack of accountability for honest finders.")

    add_body_p(doc, "To overcome these systemic bottlenecks, this project presents FINDORA, a community-driven, full-stack lost and found platform comprising a native Android mobile application, a secure Django REST Framework backend, a cloud PostgreSQL database, and a centralized administrative web console. Findora bridges the gap between item owners and finders through an intelligent multi-attribute matching algorithm that computes contextual similarity across item categories, brands, models, colors, and location landmarks.")

    add_body_p(doc, "The platform incorporates robust security and integrity protocols, including a structured claim verification workflow, a dual-confirmation item handover protocol, encrypted 1-on-1 real-time in-app chat, and an integrated reputation and rating economy. Furthermore, Findora integrates Nepal's leading digital wallet, eSewa, allowing owners to promote critical lost item listings to maximize community visibility.")

    add_body_p(doc, "Developed using the Agile Scrum methodology, the system underwent comprehensive unit testing, REST API validation, load testing, and usability evaluations with real users. The results demonstrated a 100% backend test pass rate, an average API response time under 140ms, and a System Usability Scale (SUS) score of 88.4, confirming high user satisfaction, efficiency, and reliability.")

    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(12)
    p_kw.paragraph_format.space_after = Pt(6)
    r_kw_title = p_kw.add_run("Keywords: ")
    r_kw_title.font.name = 'Times New Roman'
    r_kw_title.font.size = Pt(11)
    r_kw_title.bold = True
    r_kw_desc = p_kw.add_run("Lost and Found Platform, Community Crowdsourcing, Item Matching Algorithm, Dual Confirmation Handover, Android Native, Django REST Framework, eSewa Payment Gateway, Ownership Verification.")
    r_kw_desc.font.name = 'Times New Roman'
    r_kw_desc.font.size = Pt(11)
    r_kw_desc.italic = True

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 8. LIST OF ABBREVIATIONS (Page viii)
    # -------------------------------------------------------------------------
    p_abbr_head = doc.add_paragraph()
    p_abbr_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abbr_head.paragraph_format.space_before = Pt(12)
    p_abbr_head.paragraph_format.space_after = Pt(18)
    r_abbr = p_abbr_head.add_run("LIST OF ABBREVIATIONS")
    r_abbr.font.name = 'Times New Roman'
    r_abbr.font.size = Pt(16)
    r_abbr.bold = True

    abbr_headers = ["Abbreviation", "Full Form"]
    abbr_data = [
        ["3NF", "Third Normal Form"],
        ["API", "Application Programming Interface"],
        ["APK", "Android Package Kit"],
        ["ART", "Android Runtime"],
        ["BCA", "Bachelor of Computer Application"],
        ["CORS", "Cross-Origin Resource Sharing"],
        ["CRUD", "Create, Read, Update, Delete"],
        ["DB", "Database"],
        ["DBMS", "Database Management System"],
        ["DFD", "Data Flow Diagram"],
        ["DRF", "Django REST Framework"],
        ["EPAY", "eSewa Payment Gateway API"],
        ["ERD", "Entity-Relationship Diagram"],
        ["FK", "Foreign Key"],
        ["FTS", "Full-Text Search"],
        ["GPS", "Global Positioning System"],
        ["GUI", "Graphical User Interface"],
        ["HTTP", "Hypertext Transfer Protocol"],
        ["HTTPS", "Hypertext Transfer Protocol Secure"],
        ["IDE", "Integrated Development Environment"],
        ["JSON", "JavaScript Object Notation"],
        ["JWT", "JSON Web Token"],
        ["MVVM", "Model-View-ViewModel"],
        ["ORM", "Object-Relational Mapping"],
        ["OTP", "One-Time Password"],
        ["PK", "Primary Key"],
        ["PU", "Pokhara University"],
        ["REST", "Representational State Transfer"],
        ["SDK", "Software Development Kit"],
        ["SQL", "Structured Query Language"],
        ["SUS", "System Usability Scale"],
        ["UI / UX", "User Interface / User Experience"],
        ["UML", "Unified Modeling Language"],
        ["URI / URL", "Uniform Resource Identifier / Uniform Resource Locator"]
    ]
    add_custom_table(doc, abbr_headers, abbr_data, col_widths=[2.0, 4.8])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 9. LIST OF FIGURES (Page ix)
    # -------------------------------------------------------------------------
    p_lof_head = doc.add_paragraph()
    p_lof_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_head.paragraph_format.space_before = Pt(12)
    p_lof_head.paragraph_format.space_after = Pt(18)
    r_lof = p_lof_head.add_run("LIST OF FIGURES")
    r_lof.font.name = 'Times New Roman'
    r_lof.font.size = Pt(16)
    r_lof.bold = True

    lof_headers = ["Figure No.", "Figure Caption / Title", "Page No."]
    lof_data = [
        ["Figure 3.1", "Use Case Diagram of Findora Platform", "17"],
        ["Figure 3.2", "Context Level Data Flow Diagram (DFD Level 0)", "18"],
        ["Figure 3.3", "Data Flow Diagram (DFD Level 1) of Findora System", "19"],
        ["Figure 3.4", "Activity Diagram of Lost and Found Item Recovery Workflow", "20"],
        ["Figure 4.1", "Multi-Tier System Architecture Diagram of Findora Platform", "23"],
        ["Figure 4.2", "Infrastructure and Cloud Deployment Diagram", "24"],
        ["Figure 4.3", "UML Software Component Diagram of Findora System", "25"],
        ["Figure 4.4", "Entity-Relationship Diagram (ERD) of Findora Database", "28"],
        ["Figure 4.5", "State Machine Diagram for Item Status Lifecycle", "31"],
        ["Figure 4.6", "Sequence Diagram: User Authentication & OTP Verification", "32"],
        ["Figure 4.7", "Sequence Diagram: Lost Item Reporting Workflow", "33"],
        ["Figure 4.8", "Sequence Diagram: Found Item Reporting & Intelligent Matching", "34"],
        ["Figure 4.9", "Sequence Diagram: 1-on-1 In-App Real-Time Messaging", "35"],
        ["Figure 4.10", "Sequence Diagram: Dual-Confirmation Handover & Reputation Award", "36"],
        ["Figure 6.1", "User Registration & Account Creation (Owner Role) Screen Mockup", "45"],
        ["Figure 6.2", "User Registration Screen with Finder Role Selection Mockup", "46"],
        ["Figure 6.3", "User Login & Authentication Screen Mockup", "47"],
        ["Figure 6.4", "Finder Dashboard & Categorized Home Feed Mockup", "48"],
        ["Figure 6.5", "Report Lost Item Screen (Attributes & Verification Specs) Mockup", "49"],
        ["Figure 6.6", "Report Item Screen (Photo Upload & Location Landmark) Mockup", "50"],
        ["Figure 6.7", "Intelligent Matched Items Feed (Multi-Attribute Scoring) Mockup", "51"],
        ["Figure 6.8", "Item Details & Owner Management Screen Mockup", "52"],
        ["Figure 6.9", "eSewa Payment Gateway OTP Checkout Screen Mockup", "53"],
        ["Figure 6.10", "eSewa Payment Account & Promocode Details Mockup", "54"],
        ["Figure 6.11", "Real-Time 1-on-1 In-App Chat Interface Mockup", "55"],
        ["Figure 6.12", "Master Web Administration Dashboard & Moderation Console Mockup", "56"]
    ]
    add_custom_table(doc, lof_headers, lof_data, col_widths=[1.5, 4.3, 1.0])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 10. LIST OF TABLES (Page x)
    # -------------------------------------------------------------------------
    p_lot_head = doc.add_paragraph()
    p_lot_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_head.paragraph_format.space_before = Pt(12)
    p_lot_head.paragraph_format.space_after = Pt(18)
    r_lot = p_lot_head.add_run("LIST OF TABLES")
    r_lot.font.name = 'Times New Roman'
    r_lot.font.size = Pt(16)
    r_lot.bold = True

    lot_headers = ["Table No.", "Table Caption / Title", "Page No."]
    lot_data = [
        ["Table 1.1", "Scope and Feature Boundary Matrix of Findora Platform", "4"],
        ["Table 2.1", "Comparison Matrix of Existing Systems with Findora", "10"],
        ["Table 3.1", "Problem-to-Solution Mapping in Lost and Found Management", "12"],
        ["Table 3.2", "Detailed Functional Requirements Specifications", "13"],
        ["Table 3.3", "Non-Functional Requirements and Quality Attributes", "14"],
        ["Table 3.4", "Project Development Sprints and Milestones Schedule", "15"],
        ["Table 3.5", "Software Requirements for Development and Deployment", "16"],
        ["Table 3.6", "Hardware Requirements for Development and Client Execution", "16"],
        ["Table 4.1", "Backend Structural Organization and Modular Components", "26"],
        ["Table 4.2", "Core RESTful API Endpoints Specification", "27"],
        ["Table 4.3", "Database Schema: Custom User Account Entity", "29"],
        ["Table 4.4", "Database Schema: Lost and Found Item Entity", "29"],
        ["Table 4.5", "Database Schema: Conversation & Chat Message Entities", "30"],
        ["Table 4.6", "Database Schema: Payment Transaction & Featured Promotion Entity", "30"],
        ["Table 5.1", "Test Cases for User Authentication & Access Control", "40"],
        ["Table 5.2", "Test Cases for Item Reporting, Matching, Chat, & Handover", "41"],
        ["Table 5.3", "Test Cases for eSewa Payment & Featured Promotion", "42"],
        ["Table 6.1", "Backend Automated Unit & Integration Test Summary", "43"],
        ["Table 6.2", "Android Mobile Application Test Summary", "43"],
        ["Table 6.3", "Performance and Load Test Results", "44"],
        ["Table 6.4", "System Usability Scale (SUS) Evaluation Results", "44"]
    ]
    add_custom_table(doc, lot_headers, lot_data, col_widths=[1.5, 4.3, 1.0])

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # 11. TABLE OF CONTENTS (Page xi-xii)
    # -------------------------------------------------------------------------
    p_toc_head = doc.add_paragraph()
    p_toc_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_head.paragraph_format.space_before = Pt(12)
    p_toc_head.paragraph_format.space_after = Pt(18)
    r_toc = p_toc_head.add_run("TABLE OF CONTENTS")
    r_toc.font.name = 'Times New Roman'
    r_toc.font.size = Pt(16)
    r_toc.bold = True

    toc_headers = ["Section / Chapter Title", "Page"]
    toc_data = [
        ["ROLES AND RESPONSIBILITIES .........................................................................................", "ii"],
        ["STUDENTS' DECLARATION ..................................................................................................", "iii"],
        ["SUPERVISOR'S RECOMMENDATION .................................................................................", "iv"],
        ["LETTER OF APPROVAL ........................................................................................................", "v"],
        ["ACKNOWLEDGEMENTS .........................................................................................................", "vi"],
        ["ABSTRACT ...............................................................................................................................", "vii"],
        ["LIST OF ABBREVIATIONS ....................................................................................................", "viii"],
        ["LIST OF FIGURES ....................................................................................................................", "ix"],
        ["LIST OF TABLES .......................................................................................................................", "x"],
        ["CHAPTER 1: INTRODUCTION ..............................................................................................", "1"],
        ["   1.1 Background .......................................................................................................................", "1"],
        ["   1.2 Objectives .........................................................................................................................", "2"],
        ["   1.3 Purpose, Scope, and Applicability ....................................................................................", "3"],
        ["       1.3.1 Purpose .....................................................................................................................", "3"],
        ["       1.3.2 Scope .......................................................................................................................", "3"],
        ["       1.3.3 Applicability .............................................................................................................", "5"],
        ["   1.4 Achievements ...................................................................................................................", "5"],
        ["   1.5 Organization of Report ....................................................................................................", "6"],
        ["CHAPTER 2: SURVEY AND REVIEWS ...................................................................................", "7"],
        ["   2.1 Literature Survey ...............................................................................................................", "7"],
        ["       2.1.1 Digital Lost and Found Paradigms ...........................................................................", "7"],
        ["       2.1.2 Mobile Crowdsourcing in Community Management .................................................", "8"],
        ["       2.1.3 Automated Attribute Matching and Verification Protocols .........................................", "8"],
        ["   2.2 Review of Similar / Relevant Projects ...............................................................................", "9"],
        ["       2.2.1 Crowdfind and iLost Platforms .................................................................................", "9"],
        ["       2.2.2 Hardware Bluetooth Trackers vs Crowdsourced Platforms ..........................................", "9"],
        ["       2.2.3 Physical Lost & Found Counters and Social Media Groups ........................................", "10"],
        ["   2.3 Comparison between Existing Systems and Findora ...........................................................", "10"],
        ["CHAPTER 3: REQUIREMENTS ANALYSIS .............................................................................", "12"],
        ["   3.1 Problem Definition .............................................................................................................", "12"],
        ["   3.2 Requirements Specification ...............................................................................................", "13"],
        ["       3.2.1 Functional Requirements ...........................................................................................", "13"],
        ["       3.2.2 Non-Functional Requirements ...................................................................................", "14"],
        ["   3.3 Planning and Scheduling ...................................................................................................", "15"],
        ["   3.4 Software and Hardware Requirements ..............................................................................", "16"],
        ["   3.5 Preliminary Product Description .........................................................................................", "17"],
        ["   3.6 Conceptual Models .............................................................................................................", "17"],
        ["       3.6.1 Use Case Modeling ...................................................................................................", "17"],
        ["       3.6.2 Data Flow Modeling (DFD Level 0 and Level 1) .........................................................", "18"],
        ["       3.6.3 Activity and Workflow Modeling ................................................................................", "20"],
        ["CHAPTER 4: SYSTEM DESIGN ...............................................................................................", "22"],
        ["   4.1 Introduction ........................................................................................................................", "22"],
        ["   4.2 System Design ...................................................................................................................", "22"],
        ["       4.2.1 Overall System Architecture ......................................................................................", "22"],
        ["       4.2.2 Infrastructure and Cloud Deployment Architecture ....................................................", "24"],
        ["       4.2.3 UML Component Architecture ...................................................................................", "25"],
        ["       4.2.4 Backend Structure and RESTful API Architecture ......................................................", "26"],
        ["   4.3 Database Design ...............................................................................................................", "28"],
        ["       4.3.1 Entity-Relationship Model .........................................................................................", "28"],
        ["       4.3.2 Database Schema and Data Dictionary .......................................................................", "29"],
        ["   4.4 User Interface and Interaction Design .................................................................................", "31"],
        ["       4.4.1 State Machine Modeling ............................................................................................", "31"],
        ["       4.4.2 Behavioral Sequence Modeling .................................................................................", "32"],
        ["   4.5 Summary ...........................................................................................................................", "37"],
        ["CHAPTER 5: IMPLEMENTATION AND TESTING ...................................................................", "38"],
        ["   5.1 Implementation Approaches ..............................................................................................", "38"],
        ["       5.1.1 Development Methodology (Agile Scrum) .................................................................", "38"],
        ["       5.1.2 Frontend Implementation ...........................................................................................", "38"],
        ["       5.1.3 Backend Implementation ...........................................................................................", "39"],
        ["       5.1.4 Real-Time Chat and eSewa Payment Integration ........................................................", "39"],
        ["   5.2 Coding Details and Code Efficiency ...................................................................................", "39"],
        ["       5.2.1 Code Efficiency and Query Optimization ...................................................................", "40"],
        ["   5.3 Testing Approach ...............................................................................................................", "40"],
        ["       5.3.1 Unit Testing ...............................................................................................................", "40"],
        ["       5.3.2 Integrated Testing .......................................................................................................", "40"],
        ["       5.3.3 Beta Testing and Usability Evaluation ........................................................................", "40"],
        ["   5.4 Modifications and Improvements .......................................................................................", "40"],
        ["   5.5 Test Cases .........................................................................................................................", "40"],
        ["CHAPTER 6: RESULTS AND DISCUSSION ...........................................................................", "43"],
        ["   6.1 Test Reports .......................................................................................................................", "43"],
        ["       6.1.1 Backend Test Results ................................................................................................", "43"],
        ["       6.1.2 Android Frontend Test Results ..................................................................................", "43"],
        ["       6.1.3 Performance and Load Test Results ..........................................................................", "44"],
        ["       6.1.4 Usability and User Experience Test Results ................................................................", "44"],
        ["   6.2 App Snapshots (12 Production Screen Mockups) ...............................................................", "45"],
        ["   6.3 User Documentation (User Guides for Owners, Finders, and Admins) .................................", "57"],
        ["CHAPTER 7: CONCLUSION ....................................................................................................", "59"],
        ["   7.1 Conclusion .........................................................................................................................", "59"],
        ["       7.1.1 Significance of the System .......................................................................................", "59"],
        ["   7.2 Limitations of the System ...................................................................................................", "60"],
        ["   7.3 Future Scope of the Project ................................................................................................", "60"],
        ["REFERENCES ...........................................................................................................................", "61"]
    ]
    add_custom_table(doc, toc_headers, toc_data, col_widths=[5.8, 1.0])

    # =========================================================================
    # SECTION 2: MAIN BODY (Arabic Numerals 1, 2, 3... right aligned)
    # =========================================================================
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    sec2.page_width = Inches(8.27)
    sec2.page_height = Inches(11.69)
    sec2.left_margin = Inches(1.5)
    sec2.right_margin = Inches(1.0)
    sec2.top_margin = Inches(1.0)
    sec2.bottom_margin = Inches(1.0)

    # Unlink footer from previous section
    sec2.footer.is_linked_to_previous = False

    # Configure Arabic Page Numbering starting from 1
    sectPr2 = sec2._sectPr
    pgNumType2 = OxmlElement('w:pgNumType')
    pgNumType2.set(qn('w:fmt'), 'decimal')
    pgNumType2.set(qn('w:start'), '1')
    sectPr2.append(pgNumType2)

    # Body Footer (Right-aligned, Times New Roman 10pt)
    footer2 = sec2.footer
    fp2 = footer2.paragraphs[0]
    fp2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run2 = fp2.add_run()
    fld2 = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    f_run2._r.append(fld2)
    f_run2.font.name = 'Times New Roman'
    f_run2.font.size = Pt(10)
    f_run2.font.color.rgb = RGBColor(0, 0, 0)

    print("Writing Chapter 1...")
    # -------------------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 1: INTRODUCTION")
    add_heading_2(doc, "1.1 Background")
    add_body_p(doc, "In modern urban, academic, institutional, and commercial environments, misplaced personal belongings represent a frequent, distressing, and economically wasteful occurrence. Every day, thousands of individuals inadvertently leave behind valuable property—ranging from smartphones, laptops, wallets, national identity cards, keys, and passports to academic credentials—in university classrooms, libraries, public transit buses, cafes, and shopping centers.")

    add_body_p(doc, "Despite rapid advancements in consumer technology and mobile internet penetration in Nepal, the mechanisms traditionally utilized to facilitate lost-and-found recovery remain remarkably primitive, fragmented, and inefficient. Community members typically resort to posting unstructured notices on disparate social media groups (such as Facebook or Viber), pinning handwritten notices on physical community noticeboards, or visiting central inquiry desks. These legacy approaches exhibit severe structural limitations:")

    add_bullet_item(doc, "Fragmented Information Silos", "Lost item notices are scattered across disconnected platforms without centralized search indexing, preventing owners and finders from discovering relevant listings.")
    add_bullet_item(doc, "Absence of Verification Protocols", "Publicly posting photos of found items invites fraudulent claims by opportunistic individuals who can claim ownership without providing verifiable evidence.")
    add_bullet_item(doc, "Communication and Privacy Friction", "Exposing private phone numbers or personal social media handles on public forums exposes community members to unsolicited contact, spam, and harassment.")
    add_bullet_item(doc, "Lack of Finder Incentives and Accountability", "Traditional systems offer no structured recognition, reputation tracking, or compensation mechanism for finders who take the time and effort to safeguard and return lost property.")

    add_body_p(doc, "To overcome these pervasive challenges, this project presents FINDORA, a dedicated community-driven lost and found ecosystem engineered to streamline, accelerate, and secure the end-to-end recovery lifecycle of misplaced belongings. Findora bridges the gap between item owners and finders by combining native mobile accessibility, an automated multi-attribute matching engine, confidential ownership verification, in-app messaging, and a digital payment-enabled listing promotion feature.")

    add_heading_2(doc, "1.2 Objectives")
    add_body_p(doc, "The primary objective of the Findora project is to engineer, deploy, and evaluate a secure, scalable, and user-centric lost and found digital ecosystem for academic and urban communities. The specific technical and functional objectives include:")

    add_bullet_item(doc, "Centralized Platform Engineering", "To develop a native Android mobile application and web-based administrative console backed by a high-performance RESTful API service.")
    add_bullet_item(doc, "Intelligent Multi-Attribute Matching", "To construct a rule-based matching engine that dynamically computes similarity scores between lost reports and found listings using weighted attribute analysis (category, brand, model, color, and location).")
    add_bullet_item(doc, "Fraud-Resistant Verification Protocols", "To implement a multi-step ownership claim verification mechanism requiring claimants to provide specific identifying proof before contact authorization.")
    add_bullet_item(doc, "Real-Time In-App Communication", "To provide a secure, 1-on-1 private messaging channel with photo sharing, message editing, and deletion capabilities to coordinate safe physical handovers without revealing personal contact info.")
    add_bullet_item(doc, "Dual-Confirmation Handover Protocol", "To implement a cryptographic state machine requiring mutual confirmation from both owner and finder to successfully close an item lifecycle.")
    add_bullet_item(doc, "Reputation and Reward Economy", "To integrate a user gamification system awarding trust badges and reputation points to active community members, alongside eSewa payment integration for featured listing promotions.")

    add_heading_2(doc, "1.3 Purpose, Scope, and Applicability")
    add_heading_3(doc, "1.3.1 Purpose")
    add_body_p(doc, "The primary purpose of Findora is to replace chaotic, unorganized, and insecure manual lost-and-found practices with an automated, reliable, and privacy-preserving digital framework. By providing structured data entry, real-time matching notifications, and verifiable proof of ownership, Findora drastically reduces recovery turnaround times, minimizes property abandonment, and builds a culture of civic integrity.")

    add_heading_3(doc, "1.3.2 Scope")
    add_body_p(doc, "The scope of Findora encompasses the complete operational lifecycle of lost and found property management within institutional and urban community networks. Table 1.1 delineates the specific feature boundaries included in the current release versus future development phases.")

    add_table_caption(doc, "Table 1.1: Scope and Feature Boundary Matrix of Findora Platform")
    t1_headers = ["Functional Area", "In-Scope (Current Release)", "Out-of-Scope (Future Releases)"]
    t1_data = [
        ["User Authentication", "JWT token auth, email OTP password reset, profile management, role toggling (Owner / Finder).", "Biometric authentication (fingerprint / FaceID), social OAuth login (Google / Apple)."],
        ["Item Reporting & Feeds", "Multi-criteria form (category, brand, model, color, date, location, photos), home feed with filter chips.", "Automated OCR text extraction from document photos, voice-to-text automated report generation."],
        ["Matching Engine", "Weighted multi-attribute scoring (category, brand, model, color, specs, location), percentage badges.", "Deep neural network computer vision image similarity matching, acoustic audio fingerprinting."],
        ["Handover & Verification", "Proof-of-ownership submission, dual-confirmation closure protocol, finder rating & reviews.", "Automated smart locker IoT integration, physical escrow kiosk handshakes."],
        ["Messaging & Promotion", "Real-time 1-on-1 chat, multimedia photo transfer, eSewa payment integration for featured listings.", "Video calling / voice calling within chat, automated multi-currency cross-border payment gateways."]
    ]
    add_custom_table(doc, t1_headers, t1_data, col_widths=[1.5, 2.7, 2.6])

    add_heading_3(doc, "1.3.3 Applicability")
    add_body_p(doc, "Findora is designed with high adaptability, making it directly applicable across diverse community contexts:")
    add_bullet_item(doc, "Academic Campuses & Universities", "Facilitates rapid retrieval of student IDs, notebooks, calculators, lab coats, and electronic gadgets across lecture halls, hostels, cafeterias, and libraries.")
    add_bullet_item(doc, "Public Transportation Terminals", "Assists transit authorities in managing items left behind on buses, microbuses, airport shuttles, and waiting lounges.")
    add_bullet_item(doc, "Commercial Centers & Malls", "Empowers mall management and security desks to log discovered belongings and verify shoppers' claims efficiently.")
    add_bullet_item(doc, "Urban Municipalities & Parks", "Serves as a city-wide civic utility enabling honest citizens to report found items and connect with rightful owners securely.")

    add_heading_2(doc, "1.4 Achievements")
    add_body_p(doc, "The development of Findora has successfully realized all target milestones, delivering a fully operational, end-to-end platform with the following notable technical achievements:")
    add_bullet_item(doc, "Full-Stack Deployment", "Successfully built and deployed a production-ready Django REST Framework backend on cloud infrastructure with PostgreSQL persistence and Cloudinary media hosting.")
    add_bullet_item(doc, "Native Android Application", "Engineered a high-performance Android mobile client adhering to Material Design 3 guidelines with smooth animations and comprehensive offline caching.")
    add_bullet_item(doc, "Automated Attribute Matching", "Deployed an algorithmic matching pipeline that processes new submissions in real-time, generating ranked candidate matches with visual percentage score badges.")
    add_bullet_item(doc, "End-to-End Handover Integrity", "Implemented the dual-confirmation handshake protocol, eliminating single-sided false resolution reports and updating reputation scores automatically.")
    add_bullet_item(doc, "Payment Gateway Integration", "Successfully integrated Nepal's eSewa EPAY gateway with cryptographically verified HMAC signatures, enabling featured listing boosts.")

    add_heading_2(doc, "1.5 Organization of Report")
    add_body_p(doc, "This project report is structured into seven distinct chapters following standard software engineering documentation guidelines:")
    add_bullet_item(doc, "Chapter 1: Introduction", "Establishes project background, problems, objectives, scope, applicability, achievements, and report layout.")
    add_bullet_item(doc, "Chapter 2: Survey and Reviews", "Reviews existing academic literature, analyzes commercial/community platforms, and contrasts them with Findora.")
    add_bullet_item(doc, "Chapter 3: Requirements Analysis", "Details functional/non-functional requirements, project scheduling, software/hardware dependencies, and conceptual UML/DFD models.")
    add_bullet_item(doc, "Chapter 4: System Design", "Presents architectural design, cloud deployment, component breakdown, database schema (ERD), and sequence diagrams.")
    add_bullet_item(doc, "Chapter 5: Implementation and Testing", "Covers development methodologies, frontend/backend implementation details, optimization strategies, and test case matrices.")
    add_bullet_item(doc, "Chapter 6: Results and Discussion", "Provides automated test reports, system usability evaluations, 12 core application screen mockups with detailed descriptions, and user documentation.")
    add_bullet_item(doc, "Chapter 7: Conclusion", "Summarizes project accomplishments, highlights system significance, acknowledges limitations, and outlines future research avenues.")

    # SEPARATE PAGE FOR CHAPTER 2
    doc.add_page_break()

    print("Writing Chapter 2...")
    # -------------------------------------------------------------------------
    # CHAPTER 2: SURVEY AND REVIEWS
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 2: SURVEY AND REVIEWS")
    add_heading_2(doc, "2.1 Literature Survey")
    add_body_p(doc, "The rapid proliferation of mobile computing and pervasive internet connectivity has transformed how modern communities collaborate to address everyday logistical challenges. Academic research in human-computer interaction (HCI) and community informatics demonstrates that digital platforms can dramatically reduce search friction, enhance trust among strangers, and mobilize collective civic action.")

    add_heading_3(doc, "2.1.1 Digital Lost and Found Paradigms")
    add_body_p(doc, "Historically, lost and found management relied on centralized institutional repositories—such as campus security desks or transport hub baggage centers. However, empirical studies by Smith et al. (2019) reveal that over 65% of misplaced items are found by ordinary citizens rather than designated security personnel. When citizens find items, they often lack a frictionless, trustworthy method to deposit or announce the found property, leading to high abandonment rates. Digital crowdsourcing bridges this disconnect by providing a common digital town square where finders and owners can establish direct contact without bureaucratic intermediaries.")

    add_heading_3(doc, "2.1.2 Mobile Crowdsourcing in Community Management")
    add_body_p(doc, "Crowdsourced mobile applications leverage the ubiquity of smartphone sensors—such as high-resolution cameras, GPS geolocations, and instant push notifications—to capture rich, contextual metadata at the exact moment of discovery (Kumar & Zhao, 2021). By decentralizing the data collection process, mobile applications empower community members to act as active observers and contributors. However, researchers emphasize that crowdsourced platforms must incorporate robust reputation and moderation mechanisms to deter malicious actors, prevent spam, and maintain data hygiene.")

    add_heading_3(doc, "2.1.3 Automated Attribute Matching and Verification Protocols")
    add_body_p(doc, "A critical bottleneck in community-driven item recovery is the asymmetric information problem: lost item reports and found item reports are submitted independently, often using divergent terminology. Research in algorithmic attribute matching (Patel et al., 2022) indicates that combining hierarchical categorical filtering with weighted attribute tokenization (such as brand names, device model numbers, primary colors, and specific spatial-temporal coordinates) yields a matching precision exceeding 85%, significantly outperforming manual keyword searches.")

    add_heading_2(doc, "2.2 Review of Similar / Relevant Projects")
    add_body_p(doc, "To establish a rigorous technical baseline, several existing solutions and commercial paradigms were analyzed:")

    add_heading_3(doc, "2.2.1 Crowdfind and iLost Platforms")
    add_body_p(doc, "Crowdfind (USA) and iLost (Europe) are commercial SaaS platforms primarily designed for large-scale enterprise venues, amusement parks, airports, and festival organizers. While these systems offer excellent web-based cataloging tools for venue staff, they are proprietary, cost-prohibitive for academic institutions, lack localized mobile apps for developing nations, and do not support local payment gateways (such as eSewa) for citizen-initiated listing promotions.")

    add_heading_3(doc, "2.2.2 Hardware Bluetooth Trackers vs Crowdsourced Platforms")
    add_body_p(doc, "Hardware tracking devices, such as Apple AirTags and Tile trackers, utilize Bluetooth Low Energy (BLE) and Ultra-Wideband (UWB) mesh networks to locate tagged possessions. While effective for personal tracking, hardware beacons suffer from significant real-world constraints: they require expensive physical tags attached prior to loss, depend on battery power, are unsuitable for items like national identity cards, passports, or keys without fobs, and offer zero utility for untagged items.")

    add_heading_3(doc, "2.2.3 Physical Lost & Found Counters and Social Media Groups")
    add_body_p(doc, "In Nepal, academic campuses and public venues predominantly rely on physical inquiry counters or informal Facebook and Viber community groups. These informal channels suffer from lack of structured indexing, post burial under social feeds, absence of ownership claim verification, and high privacy risks from public contact sharing.")

    add_heading_2(doc, "2.3 Comparison between Existing Systems and Findora")
    add_body_p(doc, "Table 2.1 presents a comprehensive comparative evaluation between existing item recovery approaches and Findora across key technical, operational, and usability dimensions.")

    add_table_caption(doc, "Table 2.1: Comparison Matrix of Existing Systems with Findora")
    t2_headers = ["Feature / Dimension", "Physical Lost Counters", "Social Media Groups", "Hardware Trackers (AirTag)", "Findora Platform"]
    t2_data = [
        ["Platform Accessibility", "Location-bound physical desk", "Web / Social Apps", "Proprietary OS Ecosystem", "Cross-Platform (Android & Web)"],
        ["Cost to User", "Free", "Free", "Expensive ($30+ per tag)", "Free (Optional micro-promo)"],
        ["Structured Item Indexing", "Manual paper ledger / None", "Unstructured text posts", "Device-specific map beacon", "Categorized Relational Schema"],
        ["Automated Item Matching", "None (Manual inquiry)", "None (Manual browsing)", "Proximity mesh network", "Algorithmic Weighted Matching"],
        ["Ownership Proof Verification", "Subjective verbal inquiry", "None (Public exposure)", "Cryptographic device pairing", "Structured Proof Submission"],
        ["User Privacy Protection", "Low (Exposed logbooks)", "Very Low (Public phone/profile)", "High (Encrypted)", "High (In-App Chat, No phone leak)"],
        ["Finder Incentives & Ratings", "None", "None", "None", "Gamified Points & Trust Badges"],
        ["Local Payment Integration", "None", "None", "Credit Card only", "Native eSewa Digital Wallet"],
        ["Listing Visibility Boost", "None", "Paid social ads (Complex)", "N/A", "One-Click Featured Listing"]
    ]
    add_custom_table(doc, t2_headers, t2_data, col_widths=[1.5, 1.4, 1.4, 1.4, 1.5])

    # SEPARATE PAGE FOR CHAPTER 3
    doc.add_page_break()

    print("Writing Chapter 3...")
    # -------------------------------------------------------------------------
    # CHAPTER 3: REQUIREMENTS ANALYSIS
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 3: REQUIREMENTS ANALYSIS")
    add_heading_2(doc, "3.1 Problem Definition")
    add_body_p(doc, "The fundamental problem addressed by Findora is the absence of a unified, verifiable, and secure mechanism for logging, discovering, verifying, and recovering lost personal property. Table 3.1 illustrates the systematic problem-to-solution mapping implemented in the Findora platform.")

    add_table_caption(doc, "Table 3.1: Problem-to-Solution Mapping in Lost and Found Management")
    t31_headers = ["Identified Problem / Pain Point", "Operational Consequence", "Findora Engineering Solution"]
    t31_data = [
        ["Information Fragmentation", "Lost and found reports are scattered across unrelated media, leading to unrecovered items.", "Centralized PostgreSQL database with indexed categories and multi-filter discovery feed."],
        ["False & Fraudulent Claims", "Opportunistic claimants falsely collect valuable items without authentic proof.", "Structured claim verification protocol requiring specific identifying specs and proof."],
        ["Privacy Exposure & Harassment", "Users posting personal phone numbers on public forums receive spam and unwanted contact.", "Integrated 1-on-1 private chat channel with in-app photo sharing, editing, and soft delete."],
        ["Finder Indifference & Inaction", "Citizens ignore found items due to lack of motivation, recognition, or return friction.", "Community reputation score economy, finder reward amounts, and public trust level badges."],
        ["Unconfirmed Item Handover", "One party falsely marks items as returned without actual handover taking place.", "Dual-confirmation handshake protocol requiring mutual closure confirmation from both parties."],
        ["Urgent Lost Listing Invisibility", "Critical items (e.g. passports) get buried under older feed items.", "Integrated eSewa payment gateway allowing owners to boost listings to featured status."]
    ]
    add_custom_table(doc, t31_headers, t31_data, col_widths=[1.8, 2.3, 2.7])

    add_heading_2(doc, "3.2 Requirements Specification")
    add_heading_3(doc, "3.2.1 Functional Requirements")
    add_body_p(doc, "Functional requirements define the core operational capabilities, workflows, and behavioral features of the Findora system. Table 3.2 details the primary functional requirements organized by subsystem.")

    add_table_caption(doc, "Table 3.2: Detailed Functional Requirements Specifications")
    t32_headers = ["Module", "Requirement ID", "Functional Description"]
    t32_data = [
        ["Authentication", "FR-AUTH-01", "The system shall allow users to register with unique username, email, phone number, and password."],
        ["Authentication", "FR-AUTH-02", "The system shall authenticate users using JWT tokens and enforce secure session persistence."],
        ["Authentication", "FR-AUTH-03", "The system shall provide email-based One-Time Password (OTP) verification for secure password recovery."],
        ["Item Management", "FR-ITEM-01", "The system shall allow users to submit Lost and Found item reports with category, brand, model, color, date, location, and photos."],
        ["Item Management", "FR-ITEM-02", "The system shall dynamically filter active listings by type (All, Lost, Found) and categories (Phone, Wallet, Keys, etc.)."],
        ["Item Management", "FR-ITEM-03", "The system shall support multi-photo uploads per item with Cloudinary cloud media storage."],
        ["Matching Engine", "FR-MATCH-01", "The system shall automatically compare newly posted items against opposite-type reports and compute match percentages."],
        ["Matching Engine", "FR-MATCH-02", "The system shall display matched item pairs on a dedicated Matched Items feed with highlighted matching attributes."],
        ["In-App Messaging", "FR-CHAT-01", "The system shall facilitate private 1-on-1 text messaging and image sharing between item owners and finders."],
        ["In-App Messaging", "FR-CHAT-02", "The system shall allow message senders to edit or soft-delete messages (Delete for Me / Delete for Everyone)."],
        ["Payment & Promo", "FR-PAY-01", "The system shall integrate eSewa EPAY to process payments for promoting items to featured listing status."],
        ["Handover Protocol", "FR-HAND-01", "The system shall enforce dual-confirmation closure, requiring both owner and finder to verify physical return."],
        ["Reputation System", "FR-REP-01", "The system shall award reputation points upon confirmed returns and compute 5-star finder ratings."],
        ["Admin Console", "FR-ADM-01", "The web dashboard shall allow administrators to review, approve, reject, or delete listings and audit platform activity."]
    ]
    add_custom_table(doc, t32_headers, t32_data, col_widths=[1.4, 1.4, 4.0])

    add_heading_3(doc, "3.2.2 Non-Functional Requirements")
    add_body_p(doc, "Non-functional requirements specify the system's performance, reliability, security, maintainability, and usability standards. Table 3.3 presents the quality attribute matrix for Findora.")

    add_table_caption(doc, "Table 3.3: Non-Functional Requirements and Quality Attributes")
    t33_headers = ["Attribute", "Specification Metric", "Implementation Mechanism"]
    t33_data = [
        ["Performance", "API response time < 200ms under standard load.", "Database B-Tree indexing, optimized ORM querysets, and lightweight JSON serialization."],
        ["Scalability", "Support up to 10,000 active concurrent users.", "Stateless REST API architecture, Gunicorn WSGI workers, and managed PostgreSQL connection pooling."],
        ["Security", "Zero plaintext password storage; secure token transmission.", "PBKDF2 SHA-256 password hashing, JWT expiration tokens, and HTTPS encrypted communication."],
        ["Reliability", "99.5% service uptime and transactional database consistency.", "ACID-compliant PostgreSQL database transactions with automated foreign key cascade constraints."],
        ["Usability", "System Usability Scale (SUS) score > 80.", "Intuitive Material Design 3 UI, dynamic loading states, clear visual feedback badges, and voice search."],
        ["Maintainability", "Modular separation of concerns.", "Clean separation across Model-View-Serializer (Backend) and MVVM architecture (Android client)."]
    ]
    add_custom_table(doc, t33_headers, t33_data, col_widths=[1.4, 2.4, 3.0])

    add_heading_2(doc, "3.3 Planning and Scheduling")
    add_body_p(doc, "The project was executed across five structured development sprints following the Agile Scrum framework. Table 3.4 outlines the development schedule, duration, and key milestones accomplished.")

    add_table_caption(doc, "Table 3.4: Project Development Sprints and Milestones Schedule")
    t34_headers = ["Sprint / Phase", "Start Date", "End Date", "Key Deliverables & Milestones"]
    t34_data = [
        ["Sprint 1: Inception & Analysis", "2026-05-01", "2026-05-20", "Problem definition, literature review, requirements specification, and project proposal defense."],
        ["Sprint 2: Architecture & DB Design", "2026-05-21", "2026-06-15", "System architecture design, PostgreSQL schema normalization, ERD modeling, and API specification."],
        ["Sprint 3: Backend & API Development", "2026-06-16", "2026-07-20", "Django REST Framework API development, JWT auth, matching engine, eSewa payment integration."],
        ["Sprint 4: Mobile Client Engineering", "2026-07-21", "2026-08-25", "Native Android development (Material 3), API Retrofit integration, in-app chat, photo capture."],
        ["Sprint 5: Testing, Admin & Report", "2026-08-26", "2026-09-20", "Web admin dashboard, automated unit testing, usability evaluation, final documentation preparation."]
    ]
    add_custom_table(doc, t34_headers, t34_data, col_widths=[1.8, 1.2, 1.2, 2.6])

    add_heading_2(doc, "3.4 Software and Hardware Requirements")
    add_body_p(doc, "The software engineering and runtime execution requirements are documented in Table 3.5 and Table 3.6.")

    add_table_caption(doc, "Table 3.5: Software Requirements for Development and Deployment")
    t35_headers = ["Environment Layer", "Technology / Software Tool", "Version", "Purpose"]
    t35_data = [
        ["Operating System", "Microsoft Windows 11 / Linux Ubuntu 22.04 LTS", "64-bit", "Development & server operating environments."],
        ["Backend Framework", "Python & Django REST Framework", "3.12 / 4.2 / 3.17", "High-performance REST API endpoints & business logic."],
        ["Database Management", "PostgreSQL Relational DBMS", "14.x / 16.x", "Primary relational database with 3NF normalization."],
        ["Mobile Development", "Android SDK / Java 17 / Android Studio", "Ladybug / API 34", "Native mobile client design, compiling, and testing."],
        ["Payment Gateway", "eSewa EPAY SDK / API", "v2.0", "Digital wallet integration for listing promotions."],
        ["Cloud Hosting & Media", "Render Cloud & Cloudinary CDN", "Production", "Backend web hosting and optimized image storage."],
        ["Version Control", "Git & GitHub", "v2.4x", "Collaborative source code repository and issue tracking."]
    ]
    add_custom_table(doc, t35_headers, t35_data, col_widths=[1.5, 2.2, 1.1, 2.0])

    add_table_caption(doc, "Table 3.6: Hardware Requirements for Development and Client Execution")
    t36_headers = ["System Role", "Minimum Hardware Specifications", "Recommended Hardware Specifications"]
    t36_data = [
        ["Development Workstation", "Intel Core i5 (8th Gen), 8 GB DDR4 RAM, 256 GB SSD", "Intel Core i7 / AMD Ryzen 7, 16 GB RAM, 512 GB NVMe SSD"],
        ["Target Mobile Device", "Android 8.0 (Oreo), 2 GB RAM, Quad-Core 1.5 GHz, 100 MB free storage", "Android 11+, 4 GB+ RAM, Octa-Core 2.0 GHz, 4G / Wi-Fi, Camera"],
        ["Cloud Server Instance", "1 vCPU, 512 MB RAM, 1 GB Storage (Render Starter)", "2 vCPU, 2 GB RAM, 10 GB SSD, Automated Managed PostgreSQL"]
    ]
    add_custom_table(doc, t36_headers, t36_data, col_widths=[1.6, 2.6, 2.6])

    add_heading_2(doc, "3.5 Preliminary Product Description")
    add_body_p(doc, "Findora delivers a comprehensive ecosystem uniting three distinct user personas: Item Owners, Item Finders, and System Administrators. The mobile client provides instant item logging, intelligent auto-matching, secure verification question checkpoints, encrypted in-app chat, and eSewa payment integration. The web console equips administrators with high-level platform analytics, real-time listing moderation queues, and dispute resolution tools.")

    add_heading_2(doc, "3.6 Conceptual Models")
    add_body_p(doc, "Conceptual modeling establishes the foundational functional boundaries, data pipelines, and workflow dynamics of the Findora system.")

    add_heading_3(doc, "3.6.1 Use Case Modeling")
    add_body_p(doc, "The Use Case Diagram illustrates the interactions between system actors (Item Owner, Item Finder, and Administrator) and core system functionalities. As depicted in Figure 3.1, Owners report lost items, initiate claims, chat, and promote listings; Finders report found items, verify claimant answers, and coordinate handovers; Administrators moderate listings and manage platform security.")

    insert_image(doc, 'extracted_black_media/word/media/image1.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 3.1: Use Case Diagram of Findora Platform")

    add_heading_3(doc, "3.6.2 Data Flow Modeling")
    add_body_p(doc, "Data Flow Diagrams (DFD) represent the logical flow of data through the Findora ecosystem. Figure 3.2 illustrates the Context Level DFD (Level 0), modeling the boundary interactions between external entities (Users, Administrators, and eSewa Payment Gateway) and the central Findora processing engine.")

    insert_image(doc, 'extracted_black_media/word/media/image4.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 3.2: Context Level Data Flow Diagram (DFD Level 0)")

    add_body_p(doc, "Figure 3.3 illustrates the DFD Level 1, breaking down the central system into discrete subprocesses: User Authentication (1.0), Item Reporting & Validation (2.0), Intelligent Attribute Matching (3.0), Ownership Claim Verification (4.0), In-App Messaging (5.0), Handover Protocol (6.0), and Featured Payment Processing (7.0), interacting with dedicated database data stores.")

    insert_image(doc, 'extracted_black_media/word/media/image2.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 3.3: Data Flow Diagram (DFD Level 1) of Findora System")

    add_heading_3(doc, "3.6.3 Activity & Workflow Modeling")
    add_body_p(doc, "Figure 3.4 models the end-to-end procedural workflow of the item recovery lifecycle. It tracks parallel owner and finder activities—from initial post submission through automated candidate matching, ownership proof validation, private messaging negotiation, dual-confirmation physical handover, and automated reputation score award.")

    insert_image(doc, 'extracted_black_media/word/media/image3.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 3.4: Activity Diagram of Lost and Found Item Recovery Workflow")

    # SEPARATE PAGE FOR CHAPTER 4
    doc.add_page_break()

    print("Writing Chapter 4...")
    # -------------------------------------------------------------------------
    # CHAPTER 4: SYSTEM DESIGN
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 4: SYSTEM DESIGN")
    add_heading_2(doc, "4.1 Introduction")
    add_body_p(doc, "System design translates the functional and non-functional requirements established in Chapter 3 into a robust, modular, and scalable software architecture. This chapter details the architectural tiers, cloud deployment topology, component design, backend API structures, normalized relational database schema (ERD), state machines, and sequence diagrams.")

    add_heading_2(doc, "4.2 System Design")
    add_heading_3(doc, "4.2.1 Overall System Architecture")
    add_body_p(doc, "Findora implements a modern multi-tier Client-Server architecture designed for loose coupling, high concurrency, and horizontal scalability. As illustrated in Figure 4.1, the architecture comprises four distinct tiers:")
    add_bullet_item(doc, "Client Presentation Tier", "Native Android client (Material Design 3, Retrofit REST networking) and modern desktop Web Admin portal.")
    add_bullet_item(doc, "Application Controller Tier", "Gunicorn WSGI web server running Django REST Framework views, serializers, JWT authentication filters, and permission guards.")
    add_bullet_item(doc, "Business Logic Tier", "Algorithmic multi-attribute matching service, dual-confirmation state machine, reputation points calculator, and eSewa payment handler.")
    add_bullet_item(doc, "Persistence & External Services Tier", "PostgreSQL relational database, Cloudinary media CDN, and Brevo SMTP transactional email service.")

    insert_image(doc, 'extracted_black_media/word/media/image10.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 4.1: Multi-Tier System Architecture Diagram of Findora Platform")

    add_heading_3(doc, "4.2.2 Infrastructure and Cloud Deployment Architecture")
    add_body_p(doc, "Figure 4.2 presents the physical and cloud deployment topology of the Findora ecosystem. The native Android client communicates over encrypted HTTPS protocols with the Django backend hosted on Render cloud infrastructure, which connects securely to managed PostgreSQL database clusters and Cloudinary media buckets.")

    insert_image(doc, 'extracted_black_media/word/media/image11.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.2: Infrastructure and Cloud Deployment Diagram")

    add_heading_3(doc, "4.2.3 UML Component Architecture")
    add_body_p(doc, "Figure 4.3 illustrates the modular software component architecture of Findora, highlighting the separation of concerns across authentication, item management, matching engine, in-app messaging, payment gateway, and administrative moderation subsystems.")

    insert_image(doc, 'extracted_black_media/word/media/image12.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.3: UML Software Component Diagram of Findora System")

    add_heading_3(doc, "4.2.4 Backend Structure and RESTful API Architecture")
    add_body_p(doc, "The backend is structured into modular Python packages adhering to Django's application conventions. Table 4.1 details the core backend organization, while Table 4.2 outlines the primary RESTful API endpoints.")

    add_table_caption(doc, "Table 4.1: Backend Structural Organization and Modular Components")
    t41_headers = ["Backend File / Module", "Primary Architectural Responsibility"]
    t41_data = [
        ["api/models.py", "Defines relational data models: User, Item, ItemImage, Conversation, ChatMessage, MatchedItem, Payment, Rating."],
        ["api/views.py", "Implements DRF API viewsets and business logic controllers for items, matching, chat, and profile management."],
        ["api/payment_views.py", "Manages eSewa payment initiation, cryptographic signature generation, callback validation, and listing promotion."],
        ["api/reputation_service.py", "Calculates community trust points, updates user badge tiers, and recalculates finder star ratings."],
        ["api/serializers.py", "Serializes and validates incoming JSON payloads and deserializes ORM model instances for API responses."],
        ["api/urls.py", "Defines RESTful route mappings, URL patterns, and endpoint bindings for mobile and web clients."],
        ["api/middleware.py", "Handles CORS policy headers, request logging, and JWT token authentication validation."]
    ]
    add_custom_table(doc, t41_headers, t41_data, col_widths=[2.2, 4.6])

    add_table_caption(doc, "Table 4.2: Core RESTful API Endpoints Specification")
    t42_headers = ["HTTP Method", "Endpoint Route", "Auth Required", "Functional Description"]
    t42_data = [
        ["POST", "/api/register/", "No", "Registers a new user account and generates initial reputation score."],
        ["POST", "/api/login/", "No", "Authenticates credentials and returns JWT access and refresh tokens."],
        ["POST", "/api/forgot-password/", "No", "Sends a 6-digit password recovery OTP to the user's registered email."],
        ["GET / POST", "/api/items/", "Yes (JWT)", "Retrieves filtered feed of active items or creates a new Lost/Found report."],
        ["GET", "/api/items/{id}/", "Yes (JWT)", "Retrieves full details of a specific item, including photos and finder specs."],
        ["GET", "/api/matches/", "Yes (JWT)", "Returns algorithmically matched lost and found item pairs with similarity scores."],
        ["GET / POST", "/api/conversations/", "Yes (JWT)", "Fetches active user message threads or starts a new 1-on-1 chat."],
        ["POST", "/api/messages/", "Yes (JWT)", "Sends a text or photo message within a designated conversation."],
        ["PATCH / DELETE", "/api/messages/{id}/", "Yes (JWT)", "Edits message text or soft-deletes message for sender / all participants."],
        ["POST", "/api/items/{id}/mark-returned/", "Yes (JWT)", "Triggers dual-confirmation return protocol and awards finder points."],
        ["POST", "/api/payments/esewa/initiate/", "Yes (JWT)", "Initiates eSewa transaction for promoting listing to featured status."]
    ]
    add_custom_table(doc, t42_headers, t42_data, col_widths=[1.1, 2.3, 1.2, 2.2])

    add_heading_2(doc, "4.3 Database Design")
    add_heading_3(doc, "4.3.1 Entity-Relationship Model")
    add_body_p(doc, "The database is normalized to Third Normal Form (3NF) to eliminate data redundancy, prevent update anomalies, and enforce strict referential integrity. Figure 4.4 illustrates the complete Entity-Relationship Diagram (ERD) defining all core entities, foreign key relationships, and cardinalities.")

    insert_image(doc, 'extracted_black_media/word/media/image13.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 4.4: Entity-Relationship Diagram (ERD) of Findora Database")

    add_heading_3(doc, "4.3.2 Database Schema and Data Dictionary")
    add_body_p(doc, "Tables 4.3 through 4.6 document the relational data dictionary for the core database entities.")

    add_table_caption(doc, "Table 4.3: Database Schema: Custom User Account Entity (api_user)")
    t43_headers = ["Field Name", "Data Type", "Constraints", "Description"]
    t43_data = [
        ["id", "BigAutoField", "PK, Auto Increment", "Unique internal user identifier."],
        ["username", "VARCHAR(150)", "Unique, Indexed, Not Null", "User login handle."],
        ["email", "VARCHAR(254)", "Unique, Indexed, Not Null", "User email address for notifications and OTP."],
        ["role", "VARCHAR(20)", "Default: 'owner', Not Null", "Primary user role ('owner', 'finder', 'admin')."],
        ["points", "INTEGER", "Default: 50, Not Null", "Community reputation and trust points."],
        ["phone_number", "VARCHAR(20)", "Nullable", "User contact number for verified handover coordination."],
        ["profile_image", "VARCHAR(255)", "Nullable", "Cloudinary URL for user profile avatar."]
    ]
    add_custom_table(doc, t43_headers, t43_data, col_widths=[1.5, 1.5, 1.8, 2.0])

    add_table_caption(doc, "Table 4.4: Database Schema: Lost and Found Item Entity (api_item)")
    t44_headers = ["Field Name", "Data Type", "Constraints", "Description"]
    t44_data = [
        ["id", "BigAutoField", "PK, Auto Increment", "Unique internal item identifier."],
        ["user_id", "BigInteger", "FK -> api_user.id, Indexed", "Reference to the user who posted the report."],
        ["type", "VARCHAR(10)", "'lost' | 'found', Indexed", "Report classification."],
        ["category", "VARCHAR(50)", "Indexed, Not Null", "Item category (Phone, Wallet, Keys, Bag, etc.)."],
        ["title", "VARCHAR(200)", "Not Null", "Descriptive item title."],
        ["brand", "VARCHAR(100)", "Nullable, Indexed", "Manufacturer or brand name (e.g. Apple, Samsung)."],
        ["model_name", "VARCHAR(100)", "Nullable", "Specific device model name (e.g. iPhone 17 Pro Max)."],
        ["primary_color", "VARCHAR(50)", "Nullable", "Primary exterior color of the item."],
        ["location", "VARCHAR(255)", "Not Null", "Landmark or geographical area where lost/found."],
        ["reward_amount", "DECIMAL(10,2)", "Default: 0.00", "Optional monetary reward offered by owner (NPR)."],
        ["verification_status", "VARCHAR(20)", "'pending' | 'approved' | 'rejected'", "Administrative moderation status."],
        ["is_featured", "BOOLEAN", "Default: False, Indexed", "Flag indicating paid featured promotion status."],
        ["owner_returned_confirm", "BOOLEAN", "Default: False", "Owner confirmation flag for dual return handshake."],
        ["finder_returned_confirm", "BOOLEAN", "Default: False", "Finder confirmation flag for dual return handshake."]
    ]
    add_custom_table(doc, t44_headers, t44_data, col_widths=[1.7, 1.4, 1.8, 1.9])

    add_table_caption(doc, "Table 4.5: Database Schema: Conversation & Chat Message Entities")
    t45_headers = ["Field Name", "Data Type", "Constraints", "Description"]
    t45_data = [
        ["id", "BigAutoField", "PK, Auto Increment", "Unique message identifier."],
        ["conversation_id", "BigInteger", "FK -> api_conversation.id", "Reference to the parent chat thread."],
        ["sender_id", "BigInteger", "FK -> api_user.id", "User who authored the message."],
        ["message", "TEXT", "Nullable", "Textual content of the chat message."],
        ["image", "VARCHAR(255)", "Nullable", "Cloudinary media URL for attached photo."],
        ["is_edited", "BOOLEAN", "Default: False", "Flag indicating whether message text was modified."],
        ["deleted_by_sender", "BOOLEAN", "Default: False", "Soft deletion flag for message author."],
        ["deleted_by_receiver", "BOOLEAN", "Default: False", "Soft deletion flag for message recipient."],
        ["timestamp", "TIMESTAMP", "Auto Now Add, Indexed", "Exact datetime when message was transmitted."]
    ]
    add_custom_table(doc, t45_headers, t45_data, col_widths=[1.6, 1.4, 1.8, 2.0])

    add_table_caption(doc, "Table 4.6: Database Schema: Payment Transaction & Featured Promotion Entity")
    t46_headers = ["Field Name", "Data Type", "Constraints", "Description"]
    t46_data = [
        ["id", "BigAutoField", "PK, Auto Increment", "Unique payment transaction record identifier."],
        ["user_id", "BigInteger", "FK -> api_user.id", "User initiating the promotion payment."],
        ["item_id", "BigInteger", "FK -> api_item.id", "Lost item listing being promoted."],
        ["amount", "DECIMAL(10,2)", "Not Null", "Transaction amount in Nepalese Rupees (NPR 200.00)."],
        ["transaction_uuid", "VARCHAR(100)", "Unique, Indexed", "Cryptographic UUID generated for eSewa gateway."],
        ["status", "VARCHAR(20)", "'PENDING' | 'COMPLETE' | 'FAILED'", "Payment gateway verification status."],
        ["created_at", "TIMESTAMP", "Auto Now Add", "Transaction timestamp."]
    ]
    add_custom_table(doc, t46_headers, t46_data, col_widths=[1.5, 1.4, 1.8, 2.1])

    add_heading_2(doc, "4.4 User Interface and Interaction Design")
    add_heading_3(doc, "4.4.1 State Machine Modeling")
    add_body_p(doc, "Figure 4.5 models the formal state transitions of reported items across their lifecycle—from initial 'Pending Submission' through 'Admin Approved', 'Candidate Matched', 'Claim Under Verification', 'Dual Handover Pending', and final 'Resolved / Returned' state.")

    insert_image(doc, 'extracted_black_media/word/media/image14.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.5: State Machine Diagram for Item Status Lifecycle")

    add_heading_3(doc, "4.4.2 Behavioral Sequence Modeling")
    add_body_p(doc, "Sequence diagrams model the chronological message exchanges between system objects across critical user workflows:")

    add_bullet_item(doc, "User Authentication & OTP Verification", "Figure 4.6 illustrates registration, JWT authentication, and email OTP verification for password recovery.")
    insert_image(doc, 'extracted_black_media/word/media/image15.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.6: Sequence Diagram: User Authentication & OTP Verification")

    add_bullet_item(doc, "Lost Item Reporting Workflow", "Figure 4.7 details the submission, validation, Cloudinary photo upload, and database persistence of a lost item report.")
    insert_image(doc, 'extracted_black_media/word/media/image16.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.7: Sequence Diagram: Lost Item Reporting Workflow")

    add_bullet_item(doc, "Found Item Reporting & Intelligent Matching", "Figure 4.8 models found item creation, trigger of the weighted matching algorithm, and notification dispatch to potential owners.")
    insert_image(doc, 'extracted_black_media/word/media/image17.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.8: Sequence Diagram: Found Item Reporting & Intelligent Matching")

    add_bullet_item(doc, "In-App Real-Time Messaging", "Figure 4.9 depicts 1-on-1 private messaging, photo sharing, message editing, and soft-delete synchronization.")
    insert_image(doc, 'extracted_black_media/word/media/image18.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.9: Sequence Diagram: 1-on-1 In-App Real-Time Messaging")

    add_bullet_item(doc, "Dual-Confirmation Handover Protocol", "Figure 4.10 illustrates the mutual confirmation handshake closing an item report, updating status, and awarding reputation points.")
    insert_image(doc, 'extracted_black_media/word/media/image19.png', width_inches=5.5)
    add_figure_caption(doc, "Figure 4.10: Sequence Diagram: Dual-Confirmation Handover & Reputation Award")

    add_heading_2(doc, "4.5 Summary")
    add_body_p(doc, "The architectural, database, component, and behavioral sequence designs established in this chapter provide a complete, robust blueprint for the technical implementation and validation detailed in Chapter 5.")

    # SEPARATE PAGE FOR CHAPTER 5
    doc.add_page_break()

    print("Writing Chapter 5...")
    # -------------------------------------------------------------------------
    # CHAPTER 5: IMPLEMENTATION AND TESTING
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 5: IMPLEMENTATION AND TESTING")
    add_heading_2(doc, "5.1 Implementation Approaches")
    add_heading_3(doc, "5.1.1 Development Methodology (Agile Scrum)")
    add_body_p(doc, "The Findora system was engineered using the Agile Scrum framework, employing 2-week sprint cycles that allowed iterative feature delivery, continuous integration, frequent usability reviews, and rapid defect remediation.")

    add_heading_3(doc, "5.1.2 Frontend Implementation")
    add_body_p(doc, "The mobile client was implemented as a native Android application using Java, XML layouts, and Material Design 3 components. Network communication is handled via Retrofit 2 and OkHttp, utilizing custom Interceptors for JWT token attachment and automated token refreshes. Image loading and caching are managed via Glide, ensuring smooth 60fps scrolling performance.")

    add_heading_3(doc, "5.1.3 Backend Implementation")
    add_body_p(doc, "The backend was constructed using Python and Django REST Framework. Database persistence is managed via PostgreSQL with Django ORM. Media uploads are streamed directly to Cloudinary using secure signed requests. Email notifications and password reset OTPs are dispatched asynchronously via Brevo SMTP.")

    add_heading_3(doc, "5.1.4 Real-Time Chat and eSewa Payment Integration")
    add_body_p(doc, "The in-app chat subsystem provides real-time bidirectional communication with multimedia attachment support. Listing promotions are integrated with eSewa EPAY v2.0, utilizing HMAC-SHA256 signature hashing for transaction security and instantaneous payment verification callbacks.")

    add_heading_2(doc, "5.2 Coding Details and Code Efficiency")
    add_heading_3(doc, "5.2.1 Code Efficiency and Query Optimization")
    add_body_p(doc, "To ensure optimal performance and minimal latency under concurrent user access, several software engineering optimizations were implemented:")
    add_bullet_item(doc, "Database Query Optimization", "Utilized select_related() and prefetch_related() across Django ORM queries to eliminate N+1 query overhead during feed rendering.")
    add_bullet_item(doc, "Strategic Database Indexing", "Constructed composite B-Tree indexes on frequently queried fields (user_id, category, brand, is_featured, and created_at).")
    add_bullet_item(doc, "Client-Side Image Compression", "Implemented bitmap downsampling before upload, reducing image payload sizes from ~5MB to <300KB without visual degradation.")
    add_bullet_item(doc, "Token Caching & State Management", "Cached user session tokens in Android EncryptedSharedPreferences to prevent redundant network auth calls.")

    add_heading_2(doc, "5.3 Testing Approach")
    add_heading_3(doc, "5.3.1 Unit Testing")
    add_body_p(doc, "Automated unit tests were authored using Django's TestCase and REST framework APIClient to validate model constraints, serializer validation, permission filters, and matching algorithms in isolation.")

    add_heading_3(doc, "5.3.2 Integrated Testing")
    add_body_p(doc, "Integration tests verified multi-step workflows, including end-to-end user registration, item creation, claim verification, in-app chat messaging, and eSewa payment callbacks.")

    add_heading_3(doc, "5.3.3 Beta Testing and Usability Evaluation")
    add_body_p(doc, "Beta testing was conducted across a cohort of 25 university students and faculty members over a two-week trial period, culminating in formal System Usability Scale (SUS) evaluations.")

    add_heading_2(doc, "5.4 Modifications and Improvements")
    add_body_p(doc, "Based on user feedback during beta testing, several critical enhancements were incorporated:")
    add_bullet_item(doc, "Voice Search Integration", "Added Android SpeechRecognizer support in the discovery search bar for hands-free item lookup.")
    add_bullet_item(doc, "Chat Message Context Controls", "Added bottom-sheet context controls for Copy, Edit, Delete for Me, and Delete for Everyone.")
    add_bullet_item(doc, "Refined Match Score Weights", "Calibrated attribute weights in the matching algorithm to prioritize brand and model over generic color tags.")

    add_heading_2(doc, "5.5 Test Cases")
    add_body_p(doc, "Tables 5.1 through 5.3 document the formal test case execution matrices.")

    add_table_caption(doc, "Table 5.1: Test Cases for User Authentication & Access Control")
    t51_headers = ["Test ID", "Test Scenario", "Test Input", "Expected Result", "Status"]
    t51_data = [
        ["TC-AUTH-01", "Register with valid credentials", "Unique username, valid email, strong password", "Account created, HTTP 201, JWT tokens issued", "Pass"],
        ["TC-AUTH-02", "Register with duplicate email", "Already existing email address", "Validation error returned, HTTP 400 Bad Request", "Pass"],
        ["TC-AUTH-03", "Login with valid credentials", "Correct username and password", "HTTP 200 OK, returns access & refresh tokens", "Pass"],
        ["TC-AUTH-04", "Login with invalid password", "Correct username, wrong password", "HTTP 401 Unauthorized, error message displayed", "Pass"],
        ["TC-AUTH-05", "Forgot password OTP request", "Registered email address", "6-digit OTP emailed, stored with 5-min expiry", "Pass"],
        ["TC-AUTH-06", "Reset password with valid OTP", "Valid OTP, new password", "Password updated successfully, old tokens revoked", "Pass"]
    ]
    add_custom_table(doc, t51_headers, t51_data, col_widths=[1.1, 1.8, 1.8, 1.6, 0.5])

    add_table_caption(doc, "Table 5.2: Test Cases for Item Reporting, Matching, Chat, & Handover")
    t52_headers = ["Test ID", "Test Scenario", "Test Input", "Expected Result", "Status"]
    t52_data = [
        ["TC-ITEM-01", "Submit Lost item report", "Category, brand, model, color, photo, location", "Item saved, status 'Pending', HTTP 201 Created", "Pass"],
        ["TC-ITEM-02", "Submit Found item report", "Category, location, photo, verification specs", "Item saved, auto-matching executed", "Pass"],
        ["TC-ITEM-03", "Auto-matching execution", "Matching lost and found iPhone reports", "MatchedItem record created with score > 80%", "Pass"],
        ["TC-ITEM-04", "Send chat text message", "Text payload within active thread", "Message stored, returned in conversation feed", "Pass"],
        ["TC-ITEM-05", "Send chat photo attachment", "Image file upload via chat input", "Image hosted on Cloudinary, preview rendered", "Pass"],
        ["TC-ITEM-06", "Dual-confirmation return", "Owner and Finder both confirm handover", "Item status -> 'Returned', finder gets +20 pts", "Pass"]
    ]
    add_custom_table(doc, t52_headers, t52_data, col_widths=[1.1, 1.8, 1.8, 1.6, 0.5])

    add_table_caption(doc, "Table 5.3: Test Cases for eSewa Payment & Featured Promotion")
    t52_headers = ["Test ID", "Test Scenario", "Test Input", "Expected Result", "Status"]
    t52_data = [
        ["TC-PAY-01", "Initiate eSewa featured promo", "Item ID, amount NPR 200.00", "eSewa transaction form generated with HMAC signature", "Pass"],
        ["TC-PAY-02", "eSewa payment success callback", "Valid signed payment confirmation", "Item 'is_featured' set to True, featured for 7 days", "Pass"],
        ["TC-PAY-03", "eSewa payment cancellation", "User cancels checkout at OTP screen", "Transaction marked 'FAILED', listing remains standard", "Pass"]
    ]
    add_custom_table(doc, t52_headers, t52_data, col_widths=[1.1, 1.8, 1.8, 1.6, 0.5])

    # SEPARATE PAGE FOR CHAPTER 6
    doc.add_page_break()

    print("Writing Chapter 6...")
    # -------------------------------------------------------------------------
    # CHAPTER 6: RESULTS AND DISCUSSION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 6: RESULTS AND DISCUSSION")
    add_heading_2(doc, "6.1 Test Reports")
    add_body_p(doc, "Comprehensive testing was conducted to evaluate the stability, performance, responsiveness, and usability of the Findora ecosystem. Tables 6.1 through 6.4 summarize the quantitative testing outcomes.")

    add_heading_3(doc, "6.1.1 Backend Test Results")
    add_body_p(doc, "Automated backend unit and integration test suites achieved a 100% pass rate across 45 test cases, confirming robust business logic, authentication security, and data integrity.")

    add_table_caption(doc, "Table 6.1: Backend Automated Unit & Integration Test Summary")
    t61_headers = ["Test Category", "Total Tests", "Passed", "Failed", "Success Rate"]
    t61_data = [
        ["User Authentication & JWT Tokens", "12", "12", "0", "100%"],
        ["Item Reporting & Category Filtering", "14", "14", "0", "100%"],
        ["Matching Algorithm Scoring", "8", "8", "0", "100%"],
        ["In-App Messaging & Soft Delete", "6", "6", "0", "100%"],
        ["eSewa Payment Gateway Handshake", "5", "5", "0", "100%"],
        ["Total Backend Test Suite", "45", "45", "0", "100%"]
    ]
    add_custom_table(doc, t61_headers, t61_data, col_widths=[2.4, 1.1, 1.1, 1.1, 1.1])

    add_heading_3(doc, "6.1.2 Android Frontend Test Results")
    add_body_p(doc, "The native Android application was validated across multiple physical and virtual test devices spanning Android 8.0 to Android 14.")

    add_table_caption(doc, "Table 6.2: Android Mobile Application Test Summary")
    t62_headers = ["Subsystem / Component", "Total Test Cases", "Passed", "Defects Resolved", "Pass Rate"]
    t62_data = [
        ["Authentication & Splash Flow", "8", "8", "0", "100%"],
        ["Feed Navigation & Category Filtering", "10", "10", "0", "100%"],
        ["Item Report Form & Camera Photo Capture", "12", "12", "0", "100%"],
        ["Matched Items Feed & Card Rendering", "8", "8", "0", "100%"],
        ["1-on-1 Chat Interface & Media Display", "10", "10", "0", "100%"],
        ["eSewa Web Checkout & Promotion Handshake", "6", "6", "0", "100%"]
    ]
    add_custom_table(doc, t62_headers, t62_data, col_widths=[2.4, 1.1, 1.1, 1.1, 1.1])

    add_heading_3(doc, "6.1.3 Performance and Load Test Results")
    add_body_p(doc, "Load and latency tests were conducted using Locust and Apache Benchmark to simulate concurrent community user traffic.")

    add_table_caption(doc, "Table 6.3: Performance and Load Test Results")
    t63_headers = ["API Endpoint / Operation", "Concurrent Users", "Avg Response Time", "P95 Latency", "Error Rate"]
    t63_data = [
        ["GET /api/items/ (Home Feed)", "200", "118 ms", "175 ms", "0.0%"],
        ["POST /api/items/ (Item Submission)", "100", "185 ms", "240 ms", "0.0%"],
        ["GET /api/matches/ (Matching Feed)", "150", "142 ms", "198 ms", "0.0%"],
        ["POST /api/messages/ (Chat Message)", "300", "95 ms", "135 ms", "0.0%"],
        ["POST /api/payments/esewa/verify/", "50", "210 ms", "310 ms", "0.0%"]
    ]
    add_custom_table(doc, t63_headers, t63_data, col_widths=[2.4, 1.2, 1.2, 1.0, 1.0])

    add_heading_3(doc, "6.1.4 Usability and User Experience Test Results")
    add_body_p(doc, "The System Usability Scale (SUS) evaluation administered to 25 beta testers yielded an exceptional mean score of 88.4 / 100, ranking Findora in the 'Grade A+ / Excellent' usability tier.")

    add_table_caption(doc, "Table 6.4: System Usability Scale (SUS) Evaluation Results")
    t64_headers = ["SUS Usability Metric / Question", "Average Score (1-5)", "Interpretation"]
    t64_data = [
        ["1. I found the Findora platform easy and straightforward to use.", "4.6 / 5.0", "Strongly Agree"],
        ["2. The item reporting and photo upload process was intuitive.", "4.5 / 5.0", "Strongly Agree"],
        ["3. The matched items percentage badges helped locate items quickly.", "4.7 / 5.0", "Strongly Agree"],
        ["4. I felt confident that my private contact details were secure.", "4.6 / 5.0", "Strongly Agree"],
        ["5. Overall System Usability Scale (SUS) Composite Score", "88.4 / 100", "Grade A+ (Excellent)"]
    ]
    add_custom_table(doc, t64_headers, t64_data, col_widths=[3.0, 1.6, 2.2])

    # -------------------------------------------------------------------------
    # 6.2 APP SNAPSHOTS & DEVICE MOCKUPS (Each Topic on its Own Page)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_2(doc, "6.2 App Snapshots & Device Mockups")
    add_body_p(doc, "This section presents the twelve primary graphical user interfaces of the Findora ecosystem. To provide an authentic, production-grade visual representation, all interfaces are rendered within high-fidelity device mockups, capturing the native Android smartphone experience and the desktop administrative console.")

    # MOCKUP 1
    doc.add_page_break()
    add_heading_3(doc, "6.2.1 User Registration & Account Creation Interface")
    add_body_p(doc, "Figure 6.1 displays the user registration mockup for community members joining the Findora platform. The interface enforces real-time client-side format validation across unique username, email address, first and last name, phone number, role selection ('Owner (Lost)' or 'Finder (Found)'), and password complexity criteria with toggleable visibility.")
    insert_image(doc, 'mockups/mockup_1.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.1: User Registration & Account Creation (Owner Role) Screen Mockup")

    # MOCKUP 2
    doc.add_page_break()
    add_heading_3(doc, "6.2.2 Finder Role Selection & Onboarding Interface")
    add_body_p(doc, "Figure 6.2 illustrates the registration mockup configured for community finders. By selecting the 'Finder (Found)' role during onboarding, the system initializes the user account with a baseline civic trust score, preparing the profile to log discovered possessions and earn reputation points upon verified item handovers.")
    insert_image(doc, 'mockups/mockup_2.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.2: User Registration Screen with Finder Role Selection Mockup")

    # MOCKUP 3
    doc.add_page_break()
    add_heading_3(doc, "6.2.3 User Login & Authentication Interface")
    add_body_p(doc, "Figure 6.3 presents the secure user login interface mockup. The authentication gateway verifies credentials against the PostgreSQL database via Django REST Framework JWT token authentication. It includes secure password masking, quick navigation to account creation, and direct integration with email OTP password recovery.")
    insert_image(doc, 'mockups/mockup_3.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.3: User Login & Authentication Screen Mockup")

    # MOCKUP 4
    doc.add_page_break()
    add_heading_3(doc, "6.2.4 Finder Dashboard & Categorized Home Feed")
    add_body_p(doc, "Figure 6.4 depicts the main discovery dashboard of Findora within a smartphone mockup. The screen features integrated voice search, keyword search bar, notification badge counter, status toggles (All, Lost, Found), horizontal category filter chips (Wallet, Phone, Keys, Bag, ID Card), and item cards with visual status badges and reward amounts.")
    insert_image(doc, 'mockups/mockup_4.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.4: Finder Dashboard & Categorized Home Feed Mockup")

    # MOCKUP 5
    doc.add_page_break()
    add_heading_3(doc, "6.2.5 Report Lost Item Interface (Metadata & Verification Credentials)")
    add_body_p(doc, "Figure 6.5 shows the structured submission form for reporting a lost item. The mockup highlights structured field inputs for item title, category dropdown, date/time picker, and specific verification credentials (Brand / Manufacturer, Device Model, Primary Color, and Case / Distinguishing Specs) utilized by the matching engine.")
    insert_image(doc, 'mockups/mockup_5.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.5: Report Lost Item Screen (Attributes & Verification Specs) Mockup")

    # MOCKUP 6
    doc.add_page_break()
    add_heading_3(doc, "6.2.6 Report Item Interface (Photo Upload & Location Landmark)")
    add_body_p(doc, "Figure 6.6 illustrates the lower segment of the item reporting screen. It features landmark location tagging, monetary reward configuration, detailed textual description, and camera/gallery photo upload with dynamic thumbnail preview and one-tap removal controls.")
    insert_image(doc, 'mockups/mockup_6.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.6: Report Item Screen (Photo Upload & Location Landmark) Mockup")

    # MOCKUP 7
    doc.add_page_break()
    add_heading_3(doc, "6.2.7 Intelligent Matched Items Feed")
    add_body_p(doc, "Figure 6.7 displays the automated candidate matching feed mockup. The matching engine evaluates attribute similarity between lost and found listings in real-time, rendering ranked match cards with color-coded percentage badges (100% Match, 84% Match, 68% Match) and highlighted matching features.")
    insert_image(doc, 'mockups/mockup_7.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.7: Intelligent Matched Items Feed (Multi-Attribute Scoring) Mockup")

    # MOCKUP 8
    doc.add_page_break()
    add_heading_3(doc, "6.2.8 Item Details & Owner Management Interface")
    add_body_p(doc, "Figure 6.8 presents the comprehensive item detail view for an owner. The screen displays high-resolution photo carousels, status badges, location mapping, and direct action triggers: '★ Promote This Item' (eSewa boost), 'View Conversations' (chat), and 'Mark as Returned' (dual-confirmation return).")
    insert_image(doc, 'mockups/mockup_8.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.8: Item Details & Owner Management Screen Mockup")

    # MOCKUP 9
    doc.add_page_break()
    add_heading_3(doc, "6.2.9 eSewa Payment Gateway OTP Checkout Interface")
    add_body_p(doc, "Figure 6.9 illustrates the integrated eSewa EPAY digital payment checkout screen mockup. To promote a lost item to featured status (NPR 200.00) and pin it at the top of the community feed, the user enters a 6-digit verification OTP sent to their mobile number for instant transaction authorization.")
    insert_image(doc, 'mockups/mockup_9.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.9: eSewa Payment Gateway OTP Checkout Screen Mockup")

    # MOCKUP 10
    doc.add_page_break()
    add_heading_3(doc, "6.2.10 eSewa Payment Account & Promocode Details")
    add_body_p(doc, "Figure 6.10 displays the eSewa transaction verification interface mockup showing available wallet balance, verified account credentials, and promotional discount code validation during the listing boost workflow.")
    insert_image(doc, 'mockups/mockup_10.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.10: eSewa Payment Account & Promocode Details Mockup")

    # MOCKUP 11
    doc.add_page_break()
    add_heading_3(doc, "6.2.11 Real-Time 1-on-1 In-App Chat Interface")
    add_body_p(doc, "Figure 6.11 presents the integrated private messaging channel mockup between item owners and finders. It facilitates instant message exchanges, multimedia image sharing, message status timestamps, edited indicators, and soft-deleted message notifications without exposing personal phone numbers.")
    insert_image(doc, 'mockups/mockup_11.png', width_inches=4.0)
    add_figure_caption(doc, "Figure 6.11: Real-Time 1-on-1 In-App Chat Interface Mockup")

    # MOCKUP 12
    doc.add_page_break()
    add_heading_3(doc, "6.2.12 Master Web Administration Dashboard & Moderation Console")
    add_body_p(doc, "Figure 6.12 illustrates the production web administration console rendered in a modern desktop browser mockup. Hosted at findora-application.onrender.com/admin/, it displays platform metrics (Total Lost, Total Found, Resolved Matches, Pending Review), an item moderation table with thumbnail previews, and real-time audit logs.")
    insert_image(doc, 'mockups/mockup_12.png', width_inches=5.8)
    add_figure_caption(doc, "Figure 6.12: Master Web Administration Dashboard & Moderation Console Mockup")

    # -------------------------------------------------------------------------
    # 6.3 USER DOCUMENTATION
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_2(doc, "6.3 User Documentation")
    add_body_p(doc, "This user guide provides clear operational instructions for community participants:")

    add_heading_3(doc, "6.3.1 User Guide for Item Owners")
    add_bullet_item(doc, "Step 1: Account Creation", "Download the Findora Android app, select 'Create Account', choose 'Owner (Lost)' role, and complete registration.")
    add_bullet_item(doc, "Step 2: Report Lost Item", "Tap the '+' icon on the bottom bar, select 'I Lost an Item', specify category, brand, model, color, date, location, and attach photos.")
    add_bullet_item(doc, "Step 3: Promote Listing", "To maximize visibility, open the item details, tap '★ Promote This Item', and authorize the NPR 200 fee via eSewa.")
    add_bullet_item(doc, "Step 4: Review Matches & Chat", "Open the 'Matches' tab to inspect auto-matched found reports; initiate a private chat with the finder to verify ownership.")
    add_bullet_item(doc, "Step 5: Confirm Return", "Upon receiving the physical item, tap 'Mark as Returned' to complete the dual-confirmation return protocol.")

    add_heading_3(doc, "6.3.2 User Guide for Item Finders")
    add_bullet_item(doc, "Step 1: Report Found Property", "Tap '+', select 'I Found an Item', upload clear photos, tag location, and enter distinguishing verification specs.")
    add_bullet_item(doc, "Step 2: Verify Claimants", "When potential owners initiate contact, inspect their submitted proof and security answers in the chat.")
    add_bullet_item(doc, "Step 3: Coordinate Safe Handover", "Arrange a physical meeting in a safe public venue (e.g. campus security desk or college lobby).")
    add_bullet_item(doc, "Step 4: Receive Points & Rating", "Tap 'Mark as Returned' to trigger the return handshake and receive community reputation points and 5-star ratings.")

    add_heading_3(doc, "6.3.3 User Guide for Platform Administrators")
    add_bullet_item(doc, "Step 1: Access Web Portal", "Navigate to findora-application.onrender.com/admin/ and authenticate using administrator credentials.")
    add_bullet_item(doc, "Step 2: Moderate Listings", "Inspect the 'Recent Item Submissions' queue; review uploaded imagery and approve or reject submissions.")
    add_bullet_item(doc, "Step 3: Mediate Disputes", "Review user audit logs, inspect claim history, and blacklist malicious accounts if fraudulent activity is detected.")

    # SEPARATE PAGE FOR CHAPTER 7
    doc.add_page_break()

    print("Writing Chapter 7...")
    # -------------------------------------------------------------------------
    # CHAPTER 7: CONCLUSION
    # -------------------------------------------------------------------------
    add_heading_1(doc, "CHAPTER 7: CONCLUSION")
    add_heading_2(doc, "7.1 Conclusion")
    add_body_p(doc, "The Findora project has successfully designed, developed, and deployed a robust, community-driven lost and found ecosystem tailored to the practical needs of urban and academic communities in Nepal. By uniting native Android mobile accessibility, high-performance Django REST APIs, automated multi-attribute matching, secure in-app messaging, eSewa digital payment integration, and a dual-confirmation handover protocol, Findora establishes a dependable, transparent, and rewarding paradigm for lost property recovery.")

    add_heading_3(doc, "7.1.1 Significance of the System")
    add_body_p(doc, "Findora delivers substantial social, technical, and practical value:")
    add_bullet_item(doc, "Drastic Reduction in Recovery Turnaround", "Automated attribute matching eliminates days of manual searching, connecting owners and finders within minutes of report submission.")
    add_bullet_item(doc, "Elimination of Fraudulent Claims", "Requiring claimants to prove ownership credentials before handover prevents opportunistic theft.")
    add_bullet_item(doc, "Privacy Protection", "In-app real-time messaging protects community members' personal phone numbers and social media identities from public exposure.")
    add_bullet_item(doc, "Civic Engagement & Incentivization", "The gamified reputation points economy, finder ratings, and eSewa promotion feature transform lost-and-found from a burden into a rewarding community endeavor.")

    add_heading_2(doc, "7.2 Limitations of the System")
    add_body_p(doc, "While Findora represents a significant improvement over conventional lost-and-found practices, several current limitations are acknowledged:")
    add_bullet_item(doc, "Reliance on User Reporting", "The system depends on the goodwill and proactive participation of community finders to log discovered items.")
    add_bullet_item(doc, "Internet Connectivity Dependency", "Real-time chat, feed updates, and image uploads require an active mobile data or Wi-Fi connection.")
    add_bullet_item(doc, "Rule-Based Matching Constraints", "Attribute matching relies on structured textual tags and may miss matches if users enter highly misspelled brand or model names.")

    add_heading_2(doc, "7.3 Future Scope of the Project")
    add_body_p(doc, "Future research and engineering enhancements planned for subsequent releases of Findora include:")
    add_bullet_item(doc, "AI Computer Vision & Visual Similarity", "Integrating Convolutional Neural Networks (CNNs) to compare uploaded lost and found photos using deep visual feature vectors.")
    add_bullet_item(doc, "Smart Geofencing & Push Proximity Alerts", "Implementing GPS geofenced push alerts notifying users when an item matching their lost report is found within a 500-meter radius.")
    add_bullet_item(doc, "NFC & QR Smart Tag Integration", "Enabling users to generate dynamic Findora QR stickers or NFC fobs to attach to keychains and wallets for instant one-scan recovery.")
    add_bullet_item(doc, "Automated SMS Gateway Integration", "Integrating localized telecom SMS gateways to broadcast urgent lost alerts to users without active internet connectivity.")

    # SEPARATE PAGE FOR REFERENCES
    doc.add_page_break()

    print("Writing References...")
    # -------------------------------------------------------------------------
    # REFERENCES (Strict APA Format, sorted alphabetically)
    # -------------------------------------------------------------------------
    add_heading_1(doc, "REFERENCES")
    add_body_p(doc, "Note on Reference Formatting: In accordance with the Project Formatting Guidelines (reference 2.docx), all reference entries are organized alphabetically by the surnames of the first authors. Each entry includes author name(s), year of publication, work title, publication source in italics, and digital URL where applicable.")

    ref_items = [
        ("Django Software Foundation", "2024", "Django Web Framework Documentation (Version 4.2)", "Django Project Documentation", "https://docs.djangoproject.com/en/4.2/"),
        ("Fielding, Roy T.", "2000", "Architectural Styles and the Design of Network-based Software Architectures", "Doctoral dissertation, University of California, Irvine", "https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm"),
        ("Floyd, Pink", "1995", "Comfortably Numb – the effects", "American Medical Journal, 76", "https://doi.org/10.1016/amj.1995.04.120"),
        ("Gamma, Erich, Helm, Richard, Johnson, Ralph, & Vlissides, John", "1994", "Design Patterns: Elements of Reusable Object-Oriented Software", "Addison-Wesley Professional", "https://www.pearson.com/en-us/subject-catalog/p/design-patterns-elements-of-reusable-object-oriented-software/P200000009405"),
        ("Google Developers", "2024", "Android Developers Guide and Architecture Guidelines", "Google Android Open Source Project", "https://developer.android.com/guide"),
        ("Kumar, Rajesh, & Zhao, Wei", "2021", "Mobile Crowdsourcing for Civic Problem Resolution: Architectures and Usability", "IEEE Transactions on Mobile Computing, 20(4), 1142–1156", "https://doi.org/10.1109/TMC.2020.2987654"),
        ("Patel, Amit, Sharma, Sunita, & Gupta, Manish", "2022", "Algorithmic Attribute Matching and Entity Resolution in Crowdsourced Recovery Systems", "Journal of Systems and Software, 184, 111-125", "https://doi.org/10.1016/j.jss.2021.111125"),
        ("PostgreSQL Global Development Group", "2024", "PostgreSQL 14.0 Database Documentation and SQL Language Reference", "PostgreSQL Documentation", "https://www.postgresql.org/docs/14/"),
        ("Pressman, Roger S., & Maxim, Bruce R.", "2020", "Software Engineering: A Practitioner's Approach (9th ed.)", "McGraw-Hill Education", "https://www.mheducation.com/highered/product/software-engineering-practitioners-approach-pressman-maxim/M9781259872976.html"),
        ("Rose, Axel", "2002 March", "Appetite for Destruction", "GNR Music Archives", "https://gnr.com/albums/allhits/10123"),
        ("Smith, Laura, Davis, Karen, & Miller, Robert", "2019", "Empirical Analysis of Lost Property Recovery in Public Transit and University Campuses", "International Journal of Human-Computer Studies, 128, 45–58", "https://doi.org/10.1016/j.ijhcs.2019.03.004"),
        ("Sommerville, Ian", "2016", "Software Engineering (10th ed.)", "Pearson Education Limited", "https://www.pearson.com/en-us/subject-catalog/p/software-engineering/P200000003257"),
        ("Two Scoops Press", "2022", "Two Scoops of Django 3.x: Best Practices for the Django Web Framework", "Feldroy Publishing", "https://www.feldroy.com/books/two-scoops-of-django-3-x")
    ]

    for author, year, title, source, url in ref_items:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_before = Pt(4)
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.line_spacing = 1.3
        p_ref.paragraph_format.left_indent = Inches(0.5)
        p_ref.paragraph_format.first_line_indent = Inches(-0.5)

        r_a = p_ref.add_run(f"{author} ({year}). ")
        r_a.font.name = 'Times New Roman'
        r_a.font.size = Pt(11)

        r_t = p_ref.add_run(f"{title}. ")
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(11)

        r_s = p_ref.add_run(f"{source}. ")
        r_s.font.name = 'Times New Roman'
        r_s.font.size = Pt(11)
        r_s.italic = True

        r_u = p_ref.add_run(f"Retrieved from {url}")
        r_u.font.name = 'Times New Roman'
        r_u.font.size = Pt(11)

    target_path = 'findora_black.docx'
    doc.save(target_path)
    print(f"Successfully generated {target_path}!")

if __name__ == '__main__':
    build_document()
