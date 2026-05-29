# Run this once: python create_template.py
import fitz
import os

os.makedirs("templates", exist_ok=True)

doc = fitz.open()
page = doc.new_page(width=595, height=842)  # A4 size

# Header
page.insert_text((50, 50), "PRADHAN MANTRI AWAS YOJANA (PMAY)", fontsize=16, color=(0,0,0))
page.insert_text((50, 75), "APPLICATION FORM", fontsize=13, color=(0,0,0))
page.insert_text((50, 95), "─" * 60, fontsize=8, color=(0,0,0))

# Field Labels
fields = [
    (50, 140, "Applicant Name        :"),
    (50, 180, "Age                   :"),
    (50, 220, "Annual Income         :"),
    (50, 260, "Caste Category        :"),
    (50, 300, "State                 :"),
    (50, 340, "BPL Status            :"),
    (50, 380, "Scheme                :"),
    (50, 420, "Eligibility Status    :"),
    (50, 460, "Eligibility Reason    :"),
    (50, 500, "Application Date      :"),
]

for x, y, label in fields:
    page.insert_text((x, y), label, fontsize=11, color=(0.3, 0.3, 0.3))

page.insert_text((50, 820), "Government of India | Ministry of Housing & Urban Affairs", fontsize=8, color=(0.5,0.5,0.5))

doc.save("templates/blank_form.pdf")
doc.close()
print("✅ templates/blank_form.pdf created!")
