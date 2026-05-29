import boto3
import re
import os
from PIL import Image
import io
import fitz  # PyMuPDF
from dotenv import load_dotenv

load_dotenv()

textract = boto3.client(
    'textract',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

DOCUMENT_PURPOSE = {
    'AADHAAR': 'IDENTITY_ONLY',
    'VOTER_ID': 'IDENTITY_ONLY',
    'PAN_CARD': 'IDENTITY_ONLY',
    'RATION_CARD': 'ELIGIBILITY_PROOF',
    'INCOME_CERTIFICATE': 'ELIGIBILITY_PROOF',
    'CASTE_CERTIFICATE': 'ELIGIBILITY_PROOF',
    'KISAN_CARD': 'ELIGIBILITY_PROOF',
    'AYUSHMAN_CARD': 'ELIGIBILITY_PROOF',
    'SCHOLARSHIP_FORM': 'ELIGIBILITY_PROOF',
    'UNKNOWN': 'UNKNOWN'
}

DOCUMENT_SCHEME_MAP = {
    'AADHAAR': [],
    'VOTER_ID': [],
    'PAN_CARD': [],
    'RATION_CARD': ['PMAY', 'AYUSHMAN_BHARAT'],
    'INCOME_CERTIFICATE': ['PMAY', 'AYUSHMAN_BHARAT'],
    'CASTE_CERTIFICATE': ['SC_ST_SCHOLARSHIP'],
    'KISAN_CARD': ['PM-KISAN'],
    'AYUSHMAN_CARD': ['AYUSHMAN_BHARAT'],
    'SCHOLARSHIP_FORM': ['SC_ST_SCHOLARSHIP'],
    'UNKNOWN': []
}


def is_pdf(file_bytes: bytes) -> bool:
    return file_bytes[:4] == b"%PDF"


def pdf_to_images(pdf_bytes: bytes) -> list:
    images = []

    try:
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)

        print(f"[OCR] PDF converted to {len(images)} image page(s)")
        return images

    except Exception as e:
        print(f"[OCR] PDF conversion failed: {e}")
        return []


def expand_uploaded_files(uploaded_files: list) -> list:
    expanded_files = []

    for idx, file_bytes in enumerate(uploaded_files):
        if is_pdf(file_bytes):
            print(f"[OCR] File {idx + 1} detected as PDF")
            pdf_pages = pdf_to_images(file_bytes)

            if pdf_pages:
                expanded_files.extend(pdf_pages)
            else:
                print("[OCR] PDF had no readable pages")
        else:
            expanded_files.append(file_bytes)

    return expanded_files


def extract_text_from_images(image_files: list) -> dict:
    image_files = expand_uploaded_files(image_files)

    all_text = []
    all_doc_types = []
    all_key_values = {}
    eligible_proofs = []

    for idx, image_bytes in enumerate(image_files):
        print(f"\n[OCR] Processing image/page {idx + 1} of {len(image_files)}...")

        processed_bytes = preprocess_image(image_bytes)
        raw_text = detect_text(processed_bytes)
        key_values = analyze_document(processed_bytes)
        all_key_values.update(key_values)

        doc_type = detect_document_type(raw_text)
        all_doc_types.append(doc_type)

        purpose = DOCUMENT_PURPOSE.get(doc_type, 'UNKNOWN')
        schemes = DOCUMENT_SCHEME_MAP.get(doc_type, [])
        eligible_proofs.extend(schemes)

        print(f"[OCR] Document {idx + 1} detected as: {doc_type}")
        print(f"[OCR] Purpose: {purpose}")
        print(f"[OCR] Supports schemes: {schemes if schemes else 'None (identity only)'}")
        print(f"[OCR] Extracted {len(raw_text.split())} words")

        all_text.append(
            f"[DOCUMENT {idx + 1} - TYPE: {doc_type} - PURPOSE: {purpose}]\n{raw_text}"
        )

    combined_text = "\n\n".join(all_text)
    masked_text = mask_aadhaar(combined_text)

    proof_summary = build_proof_summary(all_doc_types, eligible_proofs)
    final_text = proof_summary + "\n\n" + masked_text

    print(f"\n[OCR] Total documents processed : {len(image_files)}")
    print(f"[OCR] Document types found      : {all_doc_types}")
    print(f"[OCR] Eligible proofs found for : {list(set(eligible_proofs))}")
    print(f"[OCR] Aadhaar masked            : YES")

    return {
        "extracted_text": final_text,
        "raw_text": combined_text,
        "document_types": all_doc_types,
        "primary_doc_type": get_primary_doc_type(all_doc_types),
        "key_values": all_key_values,
        "eligible_proofs": list(set(eligible_proofs))
    }


def build_proof_summary(doc_types: list, eligible_proofs: list) -> str:
    identity_docs = [d for d in doc_types if DOCUMENT_PURPOSE.get(d) == 'IDENTITY_ONLY']
    proof_docs = [d for d in doc_types if DOCUMENT_PURPOSE.get(d) == 'ELIGIBILITY_PROOF']
    unique_proofs = list(set(eligible_proofs))

    summary = "=" * 60 + "\n"
    summary += "DOCUMENT ANALYSIS SUMMARY (for eligibility checking)\n"
    summary += "=" * 60 + "\n"
    summary += f"Identity Documents   : {', '.join(identity_docs) if identity_docs else 'None'}\n"
    summary += f"Eligibility Proofs   : {', '.join(proof_docs) if proof_docs else 'None — only identity docs found'}\n"
    summary += f"Schemes Supported    : {', '.join(unique_proofs) if unique_proofs else 'NONE'}\n\n"

    if not proof_docs:
        summary += "⚠️  WARNING: Only identity documents uploaded.\n"
        summary += "    Aadhaar/Voter ID alone CANNOT determine scheme eligibility.\n"
        summary += "    All schemes should be marked NOT ELIGIBLE.\n"
    else:
        summary += "✅ Eligibility proof documents found.\n"
        summary += f"    Use these to determine eligibility for: {', '.join(unique_proofs)}\n"

    summary += "=" * 60
    return summary


def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes))

        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        max_size = 2500
        if img.width > max_size or img.height > max_size:
            ratio = min(max_size / img.width, max_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            print(f"[OCR] Image resized to {new_size}")

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        return output.getvalue()

    except Exception as e:
        print(f"[OCR] Preprocessing error: {e} — using original bytes")
        return image_bytes


def detect_text(image_bytes: bytes) -> str:
    try:
        response = textract.detect_document_text(
            Document={'Bytes': image_bytes}
        )

        lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '').strip()
                confidence = block.get('Confidence', 0)

                if text and confidence > 60:
                    lines.append(text)

        extracted = '\n'.join(lines)
        print(f"[OCR] Textract DetectText: {len(lines)} lines extracted")
        return extracted

    except Exception as e:
        print(f"[OCR] DetectText error: {e}")
        return ""


def analyze_document(image_bytes: bytes) -> dict:
    try:
        response = textract.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=['FORMS']
        )

        key_values = {}
        blocks = response.get('Blocks', [])
        block_map = {b['Id']: b for b in blocks}

        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                key_text = get_text_from_block(block, block_map)
                value_block = get_value_block(block, block_map)

                if value_block:
                    value_text = get_text_from_block(value_block, block_map)

                    if key_text and value_text:
                        key_values[key_text.strip()] = value_text.strip()

        print(f"[OCR] AnalyzeDocument: {len(key_values)} key-value pairs found")
        return key_values

    except Exception as e:
        print(f"[OCR] AnalyzeDocument error (non-fatal): {e}")
        return {}


def get_value_block(key_block: dict, block_map: dict) -> dict:
    for rel in key_block.get('Relationships', []):
        if rel['Type'] == 'VALUE':
            for val_id in rel['Ids']:
                return block_map.get(val_id)
    return None


def get_text_from_block(block: dict, block_map: dict) -> str:
    text = ''

    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for child_id in rel['Ids']:
                child = block_map.get(child_id)

                if child and child['BlockType'] == 'WORD':
                    text += child.get('Text', '') + ' '

    return text.strip()


def detect_document_type(text: str) -> str:
    text_lower = text.lower()

    scores = {
        'AADHAAR': 0,
        'VOTER_ID': 0,
        'RATION_CARD': 0,
        'CASTE_CERTIFICATE': 0,
        'INCOME_CERTIFICATE': 0,
        'KISAN_CARD': 0,
        'AYUSHMAN_CARD': 0,
        'SCHOLARSHIP_FORM': 0,
        'PAN_CARD': 0,
        'UNKNOWN': 0
    }

    for kw in ['aadhaar', 'aadhar', 'uidai', 'unique identification', 'आधार', 'enrolment no']:
        if kw in text_lower:
            scores['AADHAAR'] += 3

    if re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', text):
        scores['AADHAAR'] += 5

    for kw in ['election commission', 'voter', 'epic', 'electoral photo', 'मतदाता']:
        if kw in text_lower:
            scores['VOTER_ID'] += 3

    for kw in [
        'ration card', 'ration', 'bpl', 'apl', 'nfsa', 'national food security',
        'public distribution', 'राशन', 'खाद्य', 'state civil supplies',
        'below poverty line', 'antyodaya', 'aay'
    ]:
        if kw in text_lower:
            scores['RATION_CARD'] += 3 if kw in ['ration card', 'bpl', 'nfsa', 'below poverty line'] else 2

    for kw in [
        'caste certificate', 'scheduled caste', 'scheduled tribe', 'obc certificate',
        'other backward class', 'जाति प्रमाण', 'sc certificate', 'st certificate',
        'backward class', 'caste category', 'sub-caste'
    ]:
        if kw in text_lower:
            scores['CASTE_CERTIFICATE'] += 3 if kw in ['caste certificate', 'scheduled caste', 'scheduled tribe'] else 2

    for kw in [
        'income certificate', 'annual income', 'family income', 'आय प्रमाण',
        'income proof', 'yearly income', 'monthly income', 'salary certificate',
        'आय प्रमाण पत्र', 'income rs', 'income ₹'
    ]:
        if kw in text_lower:
            scores['INCOME_CERTIFICATE'] += 3

    for kw in [
        'kisan', 'farmer', 'agriculture', 'land record', 'khasra', 'khatauni',
        'pm-kisan', 'किसान', 'खेत', 'cultivable', 'land holder'
    ]:
        if kw in text_lower:
            scores['KISAN_CARD'] += 2 if kw in ['kisan', 'pm-kisan', 'khasra', 'land record'] else 1

    for kw in ['ayushman', 'pmjay', 'jan arogya', 'health card', 'आयुष्मान']:
        if kw in text_lower:
            scores['AYUSHMAN_CARD'] += 3

    for kw in ['scholarship', 'post matric', 'post-matric', 'छात्रवृत्ति']:
        if kw in text_lower:
            scores['SCHOLARSHIP_FORM'] += 3

    for kw in ['income tax', 'permanent account number', 'pan card', 'आयकर']:
        if kw in text_lower:
            scores['PAN_CARD'] += 2

    best_type = max(scores, key=scores.get)

    return 'UNKNOWN' if scores[best_type] == 0 else best_type


def get_primary_doc_type(doc_types: list) -> str:
    priority = [
        'RATION_CARD',
        'INCOME_CERTIFICATE',
        'CASTE_CERTIFICATE',
        'KISAN_CARD',
        'AYUSHMAN_CARD',
        'SCHOLARSHIP_FORM',
        'AADHAAR',
        'VOTER_ID',
        'PAN_CARD'
    ]

    for p in priority:
        if p in doc_types:
            return p

    return doc_types[0] if doc_types else 'UNKNOWN'


def mask_aadhaar(text: str) -> str:
    text = re.sub(
        r'(?i)(aadhaar|aadhar|आधार|uidai)\s*(?:no|number|संख्या|#)?\s*[:\.]?\s*'
        r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
        lambda m: m.group(1) + ': XXXX-XXXX-' + re.sub(r'[\s\-]', '', m.group(2))[8:],
        text
    )

    text = re.sub(
        r'\b(\d{4})\s(\d{4})\s(\d{4})\b',
        r'XXXX XXXX \3',
        text
    )

    text = re.sub(
        r'(?i)(?<=aadhaar\s)(\d{4}-\d{4}-\d{4})',
        lambda m: 'XXXX-XXXX-' + m.group(1)[10:],
        text
    )

    return text


def mask_12digit(match):
    num = match.group(0)

    if len(num) == 12 and num.isdigit():
        return f"XXXX-XXXX-{num[8:]}"

    return num


def extract_structured_fields(text: str, key_values: dict) -> dict:
    fields = {
        "name": None,
        "dob": None,
        "gender": None,
        "address": None,
        "state": None,
        "pincode": None,
        "income": None,
        "caste": None,
        "is_bpl": False,
        "is_farmer": False,
        "is_student": False,
    }

    text_lower = text.lower()

    skip_words = {
        'father', 'mother', 'husband', 'wife', 'son', 'daughter',
        'name', 'male', 'female', 'unknown', 'guardian', 'parent',
        'head', 'holder', 'applicant', 'shri', 'smt', 'kumar',
        'address', 'date', 'birth', 'gender', 'india', 'government'
    }

    name_patterns = [
        r'(?:^|\n)\s*(?:name|नाम)\s*[:\-]\s*([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+){1,3})',
        r'(?:head of household|card holder|मुकिया|cardholder)\s*[:/]?\s*:?\s*([A-Za-z\u0900-\u097F ]{3,40})',
        r'(?<![\'s\s])(?:^|\n)\s*(?:name|नाम)\s*[:/]\s*([A-Za-z\u0900-\u097F ]{3,40})(?!\s*:)',
    ]

    for pattern in name_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            candidate = match.group(1).strip()
            candidate = re.sub(r'\s+', ' ', candidate)
            words = candidate.lower().split()

            if len(candidate) < 3:
                continue

            if any(w in skip_words for w in words):
                continue

            if candidate.isdigit():
                continue

            fields['name'] = candidate
            break

        if fields.get('name'):
            break

    if not fields.get('name'):
        for k, v in key_values.items():
            k_lower = k.lower().strip()

            if k_lower in ('name', 'नाम'):
                candidate = v.strip()
                words = candidate.lower().split()

                if len(candidate) > 2 and not any(w in skip_words for w in words):
                    fields['name'] = candidate
                    break

    for pattern in [
        r'(?:dob|date of birth|जन्म)\s*[:\-]?\s*(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4})',
        r'(?:dob|date of birth|जन्म)\s*[:\-]?\s*(\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})',
        r'\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b'
    ]:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            fields['dob'] = match.group(1)
            break

    if re.search(r'\b(male|पुरुष|MALE)\b', text, re.IGNORECASE):
        fields['gender'] = 'Male'
    elif re.search(r'\b(female|महिला|स्त्री|FEMALE)\b', text, re.IGNORECASE):
        fields['gender'] = 'Female'

    indian_states = [
        'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
        'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
        'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
        'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu',
        'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal',
        'delhi', 'jammu', 'kashmir', 'ladakh', 'andaman', 'chandigarh',
        'dadra', 'lakshadweep', 'puducherry'
    ]

    for state in indian_states:
        if state in text_lower:
            fields['state'] = state.title()
            break

    match = re.search(r'\b([1-9][0-9]{5})\b', text)

    if match:
        fields['pincode'] = match.group(1)

    for pattern in [
        r'(?:income|आय|salary)\s*[:\-]?\s*(?:rs\.?|₹|inr)?\s*([\d,]+)',
        r'(?:rs\.?|₹)\s*([\d,]+)\s*(?:per annum|p\.a\.|yearly|annual)',
        r'annual\s+income\s*[:\-]?\s*(?:rs\.?|₹)?\s*([\d,]+)'
    ]:
        match = re.search(pattern, text_lower)

        if match:
            income_str = match.group(1).replace(',', '')

            if income_str.isdigit():
                fields['income'] = int(income_str)
                break

    if re.search(r'\b(scheduled caste|sc)\b', text_lower):
        fields['caste'] = 'SC'
    elif re.search(r'\b(scheduled tribe|st)\b', text_lower):
        fields['caste'] = 'ST'
    elif re.search(r'\b(other backward|obc)\b', text_lower):
        fields['caste'] = 'OBC'
    elif re.search(r'\b(general|unreserved)\b', text_lower):
        fields['caste'] = 'General'

    if re.search(r'\b(bpl|below poverty|गरीबी रेखा|aay|antyodaya|nfsa|apl)\b', text_lower):
        fields['is_bpl'] = True

    if re.search(r'\b(farmer|kisan|agriculture|खेती|किसान|land holder|khasra)\b', text_lower):
        fields['is_farmer'] = True

    if re.search(r'\b(student|college|university|school|class|grade|छात्र|enrollment)\b', text_lower):
        fields['is_student'] = True

    fields = {k: v for k, v in fields.items() if v is not None}

    print(f"[OCR] Structured fields extracted: {list(fields.keys())}")
    return fields


def process_documents(image_files: list) -> dict:
    print("\n" + "=" * 50)
    print("OCR PIPELINE STARTING")
    print("=" * 50)

    ocr_result = extract_text_from_images(image_files)

    structured = extract_structured_fields(
        ocr_result['raw_text'],
        ocr_result['key_values']
    )

    ocr_result['structured_fields'] = structured

    print("\n" + "=" * 50)
    print("OCR PIPELINE COMPLETE")
    print(f"Primary doc type  : {ocr_result['primary_doc_type']}")
    print(f"Document types    : {ocr_result['document_types']}")
    print(f"Eligible proofs   : {ocr_result.get('eligible_proofs', [])}")
    print(f"Structured fields : {structured}")
    print("=" * 50 + "\n")

    return ocr_result