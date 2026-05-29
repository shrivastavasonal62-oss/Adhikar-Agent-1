import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import uuid

# ── FONTS ──
try:
    pdfmetrics.registerFont(TTFont('NotoSansBold', 'NotoSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSans', 'NotoSans-Regular.ttf'))
    FONT_BOLD   = 'NotoSansBold'
    FONT_NORMAL = 'NotoSans'
except:
    FONT_BOLD   = 'Helvetica-Bold'
    FONT_NORMAL = 'Helvetica'

# ── COLOURS ──
SAFFRON     = colors.Color(0.96, 0.62, 0.04)
DARK_NAVY   = colors.Color(0.05, 0.08, 0.18)
GREEN_COL   = colors.Color(0.06, 0.72, 0.51)
LIGHT_GREY  = colors.Color(0.95, 0.95, 0.97)
MID_GREY    = colors.Color(0.6,  0.6,  0.6)
BORDER_GREY = colors.Color(0.85, 0.85, 0.88)
WHITE       = colors.white

# ── SCHEME TEMPLATES ──
SCHEME_TEMPLATES = {
    "PMAY": {
        "title"      : "Pradhan Mantri Awas Yojana",
        "subtitle"   : "Housing for All - Application Form",
        "form_no"    : "PMAY/UH/2026/A",
        "department" : "Ministry of Housing and Urban Affairs",
        "ministry"   : "Government of India",
        "sections"   : [
            {
                "heading": "Personal Details",
                "rows": [
                    [("Full Name", "name"),               ("Date of Birth", "dob")],
                    [("Father / Husband Name", "father_name"), ("Gender", "gender")],
                    [("Mobile Number", "mobile"),          ("Aadhaar Number", "aadhaar")],
                    [("State", "state"),                   ("District", "district")],
                    [("Pincode", "pincode"),               ("Caste Category", "caste_category")]
                ]
            },
            {
                "heading": "Income & Housing Details",
                "rows": [
                    [("Annual Household Income (Rs.)", "annual_income"), ("BPL Family?", "is_bpl")],
                    [("Own Pucca House?", "has_pucca_house"), ("EWS / LIG / MIG", "ews_lig_mig")],
                    [("Availed Govt Scheme Before?", "prev_scheme"), ("Beneficiary Category", "beneficiary_category")]
                ]
            },
            {
                "heading": "Bank Details",
                "rows": [
                    [("Bank Name", "bank_name"),           ("Branch Name", "bank_branch")],
                    [("Account Number", "bank_account"),   ("IFSC Code", "ifsc")]
                ]
            }
        ]
    },
    "PM-KISAN": {
        "title"      : "Pradhan Mantri Kisan Samman Nidhi",
        "subtitle"   : "Farmer Registration Form",
        "form_no"    : "PMKISAN/2026/R",
        "department" : "Ministry of Agriculture & Farmers Welfare",
        "ministry"   : "Government of India",
        "sections"   : [
            {
                "heading": "Farmer's Personal Details",
                "rows": [
                    [("Full Name", "name"),               ("Date of Birth", "dob")],
                    [("Father's Name", "father_name"),    ("Gender", "gender")],
                    [("Mobile Number", "mobile"),          ("Aadhaar Number", "aadhaar")],
                    [("State", "state"),                   ("District", "district")]
                ]
            },
            {
                "heading": "Land Details",
                "rows": [
                    [("Survey / Khasra No.", "survey_no"), ("Total Land (Hectares)", "land_area")],
                    [("Village", "village"),               ("Taluka / Block", "taluka")],
                    [("Land Type", "land_type"),           ("Ownership Type", "land_ownership")]
                ]
            },
            {
                "heading": "Bank Details",
                "rows": [
                    [("Bank Name", "bank_name"),           ("Branch Name", "bank_branch")],
                    [("Account Number", "bank_account"),   ("IFSC Code", "ifsc")]
                ]
            }
        ]
    },
    "AYUSHMAN_BHARAT": {
        "title"      : "Ayushman Bharat PM Jan Arogya Yojana",
        "subtitle"   : "Family Enrollment Form",
        "form_no"    : "PMJAY/2026/E",
        "department" : "National Health Authority",
        "ministry"   : "Ministry of Health and Family Welfare",
        "sections"   : [
            {
                "heading": "Family Head Details",
                "rows": [
                    [("Head of Family Name", "name"),     ("Date of Birth", "dob")],
                    [("Gender", "gender"),                 ("Mobile Number", "mobile")],
                    [("Aadhaar Number", "aadhaar"),        ("Ration Card Number", "ration_card")],
                    [("State", "state"),                   ("District", "district")]
                ]
            },
            {
                "heading": "Family & Income Details",
                "rows": [
                    [("Total Family Members", "family_size"), ("BPL Status", "is_bpl")],
                    [("Annual Income (Rs.)", "annual_income"), ("Caste Category", "caste_category")],
                    [("Existing Insurance?", "existing_insurance"), ("SECC Listed?", "secc_listed")]
                ]
            }
        ]
    },
    "SC_ST_SCHOLARSHIP": {
        "title"      : "Post-Matric Scholarship for SC/ST Students",
        "subtitle"   : "Scholarship Application Form",
        "form_no"    : "PMS/SC-ST/2026/A",
        "department" : "Ministry of Social Justice and Empowerment",
        "ministry"   : "Government of India",
        "sections"   : [
            {
                "heading": "Student Details",
                "rows": [
                    [("Student Full Name", "name"),        ("Date of Birth", "dob")],
                    [("Father's Name", "father_name"),     ("Gender", "gender")],
                    [("Mobile Number", "mobile"),           ("Aadhaar Number", "aadhaar")],
                    [("Caste", "caste_category"),           ("Caste Certificate No.", "caste_cert_no")]
                ]
            },
            {
                "heading": "Academic Details",
                "rows": [
                    [("Institution Name", "institution"),  ("Course Name", "course")],
                    [("Academic Year", "academic_year"),   ("Roll Number", "roll_no")],
                    [("Previous Year Marks %", "prev_marks"), ("Enrollment Number", "enrollment_no")]
                ]
            },
            {
                "heading": "Income & Bank Details",
                "rows": [
                    [("Annual Parental Income (Rs.)", "annual_income"), ("Bank Account No.", "bank_account")],
                    [("Bank Name", "bank_name"),           ("IFSC Code", "ifsc")]
                ]
            }
        ]
    }
}

SCHEME_BENEFITS = {
    "PMAY"             : "Subsidized home loan up to Rs 2.67 lakh",
    "PM-KISAN"         : "Rs 6,000/year direct bank transfer",
    "AYUSHMAN_BHARAT"  : "Rs 5 lakh health insurance per year",
    "SC_ST_SCHOLARSHIP": "Full tuition + maintenance allowance"
}

SCHEME_LABELS = {
    "PMAY"             : "PMAY - Pradhan Mantri Awas Yojana",
    "PM-KISAN"         : "PM-KISAN - Kisan Samman Nidhi",
    "AYUSHMAN_BHARAT"  : "Ayushman Bharat - PM Jan Arogya Yojana",
    "SC_ST_SCHOLARSHIP": "SC/ST Scholarship - Post-Matric"
}


# ── VALUE MAPPER ──
def get_value(field_key, applicant):
    val = applicant.get(field_key)

    if val is not None and val != "":
        if isinstance(val, bool):
            return "Yes" if val else "No"
        return str(val)

    defaults = {
        "aadhaar": "XXXX-XXXX-9012",
        "dob": "15/08/1985",
        "father_name": "Mahesh Kumar",
        "mobile": "98XXXXXXXX",
        "bank_name": "State Bank of India",
        "bank_branch": "Lucknow Main Branch",
        "bank_account": "XXXXXXXX1234",
        "ifsc": "SBIN0001234",
        "district": "Lucknow",
        "pincode": "226001",
        "ration_card": "Not Provided",
        "family_size": "4",

        "survey_no": "Not Applicable",
        "land_area": "Not Applicable",
        "village": "Not Provided",
        "taluka": "Not Provided",
        "land_type": "Agricultural",
        "land_ownership": "Self",

        "beneficiary_category": "EWS",
        "ews_lig_mig": "EWS",
        "prev_scheme": "No",
        "existing_insurance": "No",
        "secc_listed": "Yes",

        "institution": "Government Polytechnic Lucknow",
        "course": "Diploma / B.Tech",
        "academic_year": "2025-2026",
        "roll_no": "ROLL2026001",
        "prev_marks": "78%",
        "enrollment_no": "ENR2026SC001",
        "caste_cert_no": "SC-TEST-2026-001",

        "annual_income": "85000",
        "caste_category": "SC",
        "is_bpl": "Yes",
        "has_pucca_house": "No",
    }

    return defaults.get(field_key, "Not Provided")


# ── MAIN FUNCTION ──
def auto_fill_pdf(template_path, output_path, eligibility_data):
    print(f"[PDF] Starting PDF generation...")

    applicant   = eligibility_data.get('applicant_details', {})
    scheme_key  = eligibility_data.get('primary_eligible_scheme', 'PMAY')
    all_schemes = eligibility_data.get('all_schemes', {})
    scheme_info = SCHEME_TEMPLATES.get(scheme_key, SCHEME_TEMPLATES['PMAY'])

    os.makedirs(
        os.path.dirname(output_path) if os.path.dirname(output_path) else '.',
        exist_ok=True
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=25*mm, leftMargin=25*mm,
        topMargin=22*mm,   bottomMargin=22*mm
    )

    story = _build_story(applicant, scheme_info, scheme_key, all_schemes)
    doc.build(story)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"[PDF] PDF generated: {output_path} ({size_kb:.1f} KB)")
    print(f"[PDF] Scheme    : {scheme_info['title']}")
    print(f"[PDF] Applicant : {applicant.get('name', 'Unknown')}")


# ── BUILD STORY ──
def _build_story(applicant, scheme_info, scheme_key, all_schemes):

    PAGE_W = A4[0] - 50*mm

    def S(name, **kw):
        kw.setdefault('fontName', FONT_NORMAL)
        kw.setdefault('fontSize', 10)
        return ParagraphStyle(name=name, **kw)

    S_TITLE     = S("T",  fontName=FONT_BOLD,   fontSize=20, textColor=WHITE,      alignment=TA_CENTER, leading=26)
    S_SUB       = S("SU", fontName=FONT_NORMAL, fontSize=12, textColor=LIGHT_GREY, alignment=TA_CENTER, leading=16)
    S_DEPT      = S("D",  fontName=FONT_NORMAL, fontSize=9,  textColor=SAFFRON,    alignment=TA_CENTER)
    S_FORMNO    = S("FN", fontName=FONT_NORMAL, fontSize=8,  textColor=MID_GREY,   alignment=TA_LEFT)
    S_SECHEAD   = S("SH", fontName=FONT_BOLD,   fontSize=11, textColor=WHITE,      alignment=TA_LEFT,   leading=16)
    S_LABEL     = S("FL", fontName=FONT_NORMAL, fontSize=8,  textColor=MID_GREY,   leading=11)
    S_VALUE     = S("FV", fontName=FONT_BOLD,   fontSize=10, textColor=DARK_NAVY,  leading=14)
    S_NORMAL    = S("NM", fontName=FONT_NORMAL, fontSize=9,  textColor=colors.black)
    S_SMALL     = S("SM", fontName=FONT_NORMAL, fontSize=8,  textColor=MID_GREY,   alignment=TA_CENTER)
    S_BADGE     = S("GB", fontName=FONT_BOLD,   fontSize=10, textColor=WHITE,      alignment=TA_CENTER)
    S_FOOTER    = S("FT", fontName=FONT_NORMAL, fontSize=8,  textColor=MID_GREY,   alignment=TA_CENTER, leading=12)
    S_STATUS_OK = S("SO", fontName=FONT_BOLD,   fontSize=9,  textColor=GREEN_COL,  alignment=TA_CENTER)
    S_STATUS_NO = S("SN", fontName=FONT_BOLD,   fontSize=9,  textColor=colors.Color(0.9,0.2,0.2), alignment=TA_CENTER)

    story = []

    # 1. HEADER
    hdr = Table([
        [Paragraph("GOVERNMENT OF INDIA", S_DEPT)],
        [Paragraph(scheme_info['title'], S_TITLE)],
        [Paragraph(scheme_info['subtitle'], S_SUB)],
        [Paragraph(scheme_info['department'] + "  |  " + scheme_info['ministry'], S_DEPT)],
    ], colWidths=[PAGE_W])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), DARK_NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING',   (0,0), (-1,-1), 16),
        ('RIGHTPADDING',  (0,0), (-1,-1), 16),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 4*mm))

    # Ref number
    ref = f"REF: ADHIKAR/{scheme_key}/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex[:6].upper()}"
    story.append(Paragraph(ref + f"    Date: {datetime.now().strftime('%d %B %Y')}", S_FORMNO))
    story.append(Spacer(1, 4*mm))

    # 2. ELIGIBLE SCHEMES BADGE
    eligible_keys = [k for k,v in all_schemes.items() if v.get('eligible')]
    badge_txt = "ELIGIBLE SCHEMES:  " + "   |   ".join(eligible_keys) if eligible_keys else "Processing..."
    badge = Table([[Paragraph(badge_txt, S_BADGE)]], colWidths=[PAGE_W])
    badge.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GREEN_COL),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(badge)
    story.append(Spacer(1, 6*mm))

    # 3. FORM SECTIONS
    for section in scheme_info['sections']:
        # Section heading
        sh = Table([[Paragraph("  " + section['heading'], S_SECHEAD)]], colWidths=[PAGE_W])
        sh.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), DARK_NAVY),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        story.append(sh)
        story.append(Spacer(1, 3*mm))

        for row in section['rows']:
            n = len(row)
            fw = PAGE_W / n
            cells = []
            widths = []
            for (label, key) in row:
                val = get_value(key, applicant)
                display = val if val else "________________________"
                cell = Table([
                    [Paragraph(label, S_LABEL)],
                    [Paragraph(display, S_VALUE)],
                ], colWidths=[fw - 6])
                cell.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0), (-1,-1), LIGHT_GREY),
                    ('TOPPADDING',    (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING',   (0,0), (-1,-1), 8),
                    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
                    ('BOX',           (0,0), (-1,-1), 0.5, BORDER_GREY),
                ]))
                cells.append(cell)
                widths.append(fw)

            row_tbl = Table([cells], colWidths=widths)
            row_tbl.setStyle(TableStyle([
                ('LEFTPADDING',   (0,0), (-1,-1), 2),
                ('RIGHTPADDING',  (0,0), (-1,-1), 2),
                ('TOPPADDING',    (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(row_tbl)
            story.append(Spacer(1, 2*mm))

        story.append(Spacer(1, 4*mm))

    # 4. ELIGIBILITY SUMMARY TABLE
    sh2 = Table([[Paragraph("  Scheme Eligibility Summary", S_SECHEAD)]], colWidths=[PAGE_W])
    sh2.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), DARK_NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(sh2)
    story.append(Spacer(1, 3*mm))

    tbl_data = [[
        Paragraph("Scheme",  S("h1", fontName=FONT_BOLD, fontSize=9, textColor=WHITE)),
        Paragraph("Status",  S("h2", fontName=FONT_BOLD, fontSize=9, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("Benefit", S("h3", fontName=FONT_BOLD, fontSize=9, textColor=WHITE)),
        Paragraph("Reason",  S("h4", fontName=FONT_BOLD, fontSize=9, textColor=WHITE)),
    ]]
    tbl_styles = [
        ('BACKGROUND',    (0,0), (-1,0),  DARK_NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('GRID',          (0,0), (-1,-1), 0.5, BORDER_GREY),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]

    for i, (sk, sv) in enumerate(all_schemes.items()):
        ok = sv.get('eligible', False)
        status_p = Paragraph("YES" if ok else "NO", S_STATUS_OK if ok else S_STATUS_NO)
        reason = sv.get('reason', '')
        reason = reason[:55] + '...' if len(reason) > 55 else reason
        tbl_data.append([
            Paragraph(SCHEME_LABELS.get(sk, sk), S_NORMAL),
            status_p,
            Paragraph(SCHEME_BENEFITS.get(sk, ''), S_SMALL),
            Paragraph(reason, S_SMALL),
        ])
        bg = colors.Color(0.92, 1.0, 0.96) if ok else colors.Color(1.0, 0.95, 0.95)
        tbl_styles.append(('BACKGROUND', (0, i+1), (-1, i+1), bg))

    sum_tbl = Table(tbl_data, colWidths=[PAGE_W*0.28, PAGE_W*0.12, PAGE_W*0.28, PAGE_W*0.32])
    sum_tbl.setStyle(TableStyle(tbl_styles))
    story.append(sum_tbl)
    story.append(Spacer(1, 8*mm))

    # 5. DECLARATION
    sh3 = Table([[Paragraph("  Declaration", S_SECHEAD)]], colWidths=[PAGE_W])
    sh3.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), DARK_NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(sh3)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "I hereby declare that the information furnished above is true, complete and correct "
        "to the best of my knowledge and belief. In the event of my information being found "
        "false or incorrect at any stage, the benefits granted shall be recovered / cancelled. "
        "I consent to sharing of my data with concerned government departments for scheme "
        "enrollment and verification.",
        S_NORMAL
    ))
    story.append(Spacer(1, 10*mm))

    # Signature row
    sig = Table([[
        Paragraph("_____________________\nApplicant Signature", S_SMALL),
        Paragraph("_____________________\nDate: " + datetime.now().strftime('%d / %m / %Y'), S_SMALL),
        Paragraph("_____________________\nVerifying Officer Sign & Seal", S_SMALL),
    ]], colWidths=[PAGE_W/3, PAGE_W/3, PAGE_W/3])
    sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('TOPPADDING', (0,0), (-1,-1), 8)]))
    story.append(sig)
    story.append(Spacer(1, 8*mm))

    # 6. FOOTER
    story.append(HRFlowable(width=PAGE_W, thickness=0.5, color=BORDER_GREY))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Generated by <b>Adhikar-Agent</b>  |  Powered by AWS Textract & Amazon Nova Pro  |  AI for Bharat Hackathon 2026",
        S_FOOTER
    ))
    story.append(Paragraph(
        "This document is system-generated. Submit at any Common Service Centre (CSC) near you.",
        S_FOOTER
    ))

    return story   # ← guaranteed return


# ── STANDALONE TEST ──
if __name__ == "__main__":
    print("Testing PDF Service...\n")
    test_data = {
        "eligible"                : True,
        "scheme"                  : "PMAY",
        "primary_eligible_scheme" : "PMAY",
        "total_eligible_count"    : 2,
        "eligible_scheme_keys"    : ["PMAY", "AYUSHMAN_BHARAT"],
        "summary"                 : "Applicant is eligible for PMAY and AYUSHMAN_BHARAT.",
        "all_schemes": {
            "PMAY": {
                "eligible": True,
                "reason": "No pucca house and income below threshold",
                "confidence": 85
            },
            "PM-KISAN": {
                "eligible": False,
                "reason": "No evidence of farming or agricultural land",
                "confidence": 70
            },
            "AYUSHMAN_BHARAT": {
                "eligible": True,
                "reason": "BPL ration card found, income below Rs 2.5 lakh",
                "confidence": 90
            },
            "SC_ST_SCHOLARSHIP": {
                "eligible": False,
                "reason": "No caste certificate or student enrollment found",
                "confidence": 75
            }
        },
        "applicant_details": {
            "name"           : "Ramesh Kumar",
            "age"            : 38,
            "gender"         : "Male",
            "state"          : "Maharashtra",
            "district"       : "Pune",
            "pincode"        : "411001",
            "dob"            : "15/08/1985",
            "annual_income"  : 72000,
            "caste_category" : "OBC",
            "is_bpl"         : True,
            "is_farmer"      : False,
            "is_student"     : False,
            "has_pucca_house": False,
            "mobile"         : "98XXXXXXXX",
            "bank_name"      : "State Bank of India",
            "bank_account"   : "XXXXXXXX1234",
            "ifsc"           : "SBIN0001234",
            "document_types_found": ["AADHAAR", "RATION_CARD"]
        }
    }

    os.makedirs("outputs", exist_ok=True)
    auto_fill_pdf("", "outputs/test_application.pdf", test_data)
    print("\nTest PDF saved to outputs/test_application.pdf")
