import boto3
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

MODEL_ID = "amazon.nova-pro-v1:0"

SCHEME_PRIORITY = ["PMAY", "PM-KISAN", "AYUSHMAN_BHARAT", "SC_ST_SCHOLARSHIP"]


SCHEME_RULES = {
    "PMAY": {
        "full_name": "Pradhan Mantri Awas Yojana",
        "rules": [
            "Applicant must not own a pucca house anywhere in India",
            "Annual household income below Rs 18 lakh",
            "BPL ration card OR income certificate showing income below Rs 3 lakh preferred",
        ],
        "benefit": "Subsidized home loan interest subsidy up to Rs 2.67 lakh",
    },
    "PM-KISAN": {
        "full_name": "Pradhan Mantri Kisan Samman Nidhi",
        "rules": [
            "Must be a farmer with cultivable land",
            "Land record OR Kisan card required",
        ],
        "benefit": "Rs 6,000 per year direct bank transfer",
    },
    "AYUSHMAN_BHARAT": {
        "full_name": "Ayushman Bharat PM Jan Arogya Yojana",
        "rules": [
            "Must belong to BPL family",
            "BPL ration card OR income certificate below Rs 2.5 lakh preferred",
        ],
        "benefit": "Rs 5 lakh health insurance coverage per family per year",
    },
    "SC_ST_SCHOLARSHIP": {
        "full_name": "Post-Matric Scholarship for SC/ST Students",
        "rules": [
            "Must belong to Scheduled Caste or Scheduled Tribe category",
            "Valid SC/ST caste certificate should be present",
            "For demo purposes, caste certificate alone is sufficient",
        ],
        "benefit": "Tuition fee support + maintenance allowance",
    },
}


def check_eligibility_with_bedrock(extracted_text: str) -> dict:
    print("\n" + "=" * 50)
    print("ELIGIBILITY SERVICE STARTING")
    print("=" * 50)

    prompt = build_eligibility_prompt(extracted_text)

    print("[ELIGIBILITY] Calling Amazon Nova Pro on Bedrock...")
    raw_response = call_bedrock(prompt)

    print("[ELIGIBILITY] Parsing Nova Pro response...")
    eligibility_result = parse_eligibility_response(raw_response)

    eligibility_result = apply_deterministic_rules(eligibility_result, extracted_text)
    eligibility_result = sync_primary_scheme(eligibility_result)

    eligibility_result["model_used"] = MODEL_ID
    eligibility_result["raw_ai_response"] = raw_response

    print("\n[ELIGIBILITY] Final Result:")
    for k, v in eligibility_result.items():
        if k != "raw_ai_response":
            print(f"  {k}: {v}")

    print("=" * 50 + "\n")
    return eligibility_result


def build_eligibility_prompt(extracted_text: str) -> str:
    scheme_rules_text = ""

    for scheme_key, scheme_info in SCHEME_RULES.items():
        rules_str = "\n".join([f"  - {r}" for r in scheme_info["rules"]])
        scheme_rules_text += f"""
### {scheme_key} ({scheme_info["full_name"]})
Eligibility Rules:
{rules_str}
Benefit: {scheme_info["benefit"]}
"""

    prompt = f"""You are a STRICT Indian government scheme eligibility officer.
Analyze the applicant documents and return only JSON.

## DOCUMENT PURPOSE RULES
AADHAAR CARD = identity verification only.
RATION CARD = BPL / income proof.
INCOME CERTIFICATE = income proof.
CASTE CERTIFICATE = caste proof.
LAND RECORD / KISAN CARD = farmer proof.

## ELIGIBILITY DECISION RULES
PMAY:
Eligible if BPL ration card found OR income certificate shows income below Rs 3 lakh.

PM-KISAN:
Eligible if land record OR Kisan card is found.

AYUSHMAN_BHARAT:
Eligible if BPL ration card found OR income certificate shows income below Rs 2.5 lakh.

SC_ST_SCHOLARSHIP:
Eligible if SC/ST caste certificate is found.
For this project demo, student enrollment proof is not mandatory.

## GOVERNMENT SCHEME RULES
{scheme_rules_text}

## APPLICANT DOCUMENTS
{extracted_text[:10000]}

## STRICT INSTRUCTIONS
1. Use Aadhaar only for identity fields.
2. Use ration card/income certificate for PMAY and Ayushman Bharat.
3. Use Kisan card/land record for PM-KISAN.
4. Use caste certificate for SC/ST Scholarship.
5. If caste is SC or ST, mark SC_ST_SCHOLARSHIP eligible.
6. Return ONLY pure JSON. No markdown.

## RETURN EXACTLY THIS JSON STRUCTURE
{{
  "eligible": true,
  "scheme": "SC_ST_SCHOLARSHIP",
  "all_schemes": {{
    "PMAY": {{
      "eligible": false,
      "reason": "No ration card or income certificate found",
      "confidence": 95
    }},
    "PM-KISAN": {{
      "eligible": false,
      "reason": "No land record or Kisan card found",
      "confidence": 95
    }},
    "AYUSHMAN_BHARAT": {{
      "eligible": false,
      "reason": "No BPL ration card or income certificate found",
      "confidence": 95
    }},
    "SC_ST_SCHOLARSHIP": {{
      "eligible": true,
      "reason": "SC/ST caste certificate detected",
      "confidence": 95
    }}
  }},
  "applicant_details": {{
    "name": "",
    "dob": "",
    "age": "",
    "gender": "",
    "state": "",
    "district": "",
    "pincode": "",
    "aadhaar": "",
    "father_name": "",
    "mobile": "",
    "annual_income": "",
    "caste_category": "",
    "is_bpl": false,
    "is_farmer": false,
    "is_student": false,
    "has_pucca_house": false,
    "bank_name": "",
    "bank_account": "",
    "ifsc": "",
    "ration_card": "",
    "family_size": "",
    "document_types_found": []
  }},
  "primary_eligible_scheme": null,
  "total_eligible_count": 0,
  "summary": ""
}}"""

    return prompt


def call_bedrock(prompt: str) -> str:
    try:
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {
                "temperature": 0.1,
                "topP": 0.9,
                "maxTokens": 2000,
            },
        }

        print(f"[ELIGIBILITY] Sending request to {MODEL_ID}...")

        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        raw_text = response_body["output"]["message"]["content"][0]["text"]

        print(f"[ELIGIBILITY] Nova Pro responded ({len(raw_text)} chars)")
        return raw_text

    except Exception as e:
        print(f"[ELIGIBILITY] Bedrock call failed: {e}")
        return get_fallback_response()


def parse_eligibility_response(raw_response: str) -> dict:
    try:
        result = json.loads(raw_response.strip())
        print("[ELIGIBILITY] JSON parsed successfully")
        return normalize_result(result)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
            return normalize_result(result)
    except Exception:
        pass

    try:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            return normalize_result(result)
    except Exception:
        pass

    print("[ELIGIBILITY] Using fallback parser")
    return parse_by_keywords(raw_response)


def normalize_result(result: dict) -> dict:
    if "all_schemes" not in result:
        result["all_schemes"] = {}

    for scheme in SCHEME_PRIORITY:
        if scheme not in result["all_schemes"]:
            result["all_schemes"][scheme] = {
                "eligible": False,
                "reason": "Could not determine from available documents",
                "confidence": 50,
            }

    if "applicant_details" not in result:
        result["applicant_details"] = {}

    defaults = {
        "name": "",
        "dob": "",
        "age": "",
        "gender": "",
        "state": "",
        "district": "",
        "pincode": "",
        "mobile": "",
        "aadhaar": "",
        "father_name": "",
        "annual_income": "",
        "caste_category": "",
        "is_bpl": False,
        "is_farmer": False,
        "is_student": False,
        "has_pucca_house": False,
        "bank_name": "",
        "bank_account": "",
        "ifsc": "",
        "ration_card": "",
        "family_size": "",
        "document_types_found": [],
    }

    for key, default in defaults.items():
        if key not in result["applicant_details"]:
            result["applicant_details"][key] = default

    return sync_primary_scheme(result)


def apply_deterministic_rules(result: dict, extracted_text: str) -> dict:
    text = extracted_text.lower()
    applicant = result.get("applicant_details", {})

    caste = str(applicant.get("caste_category", "")).upper().strip()

    caste_detected = (
        caste in ["SC", "ST", "SCHEDULED CASTE", "SCHEDULED TRIBE"]
        or "category: scheduled caste" in text
        or "scheduled caste" in text
        or "scheduled tribe" in text
        or re.search(r"\bcategory\s*:\s*sc\b", text, re.IGNORECASE)
        or re.search(r"\bcaste\s*:\s*sc\b", text, re.IGNORECASE)
        or re.search(r"\bcategory\s*:\s*st\b", text, re.IGNORECASE)
        or re.search(r"\bcaste\s*:\s*st\b", text, re.IGNORECASE)
    )

    if caste_detected:
        result["all_schemes"]["SC_ST_SCHOLARSHIP"] = {
            "eligible": True,
            "reason": "SC/ST caste certificate detected",
            "confidence": 98,
        }

        if not applicant.get("caste_category"):
            applicant["caste_category"] = "SC"

        result["summary"] = "SC/ST caste certificate detected. Applicant is eligible for SC/ST Scholarship."

    result["applicant_details"] = applicant
    return result


def sync_primary_scheme(data: dict) -> dict:
    all_schemes = data.get("all_schemes", {})

    eligible_keys = [
        k for k in SCHEME_PRIORITY
        if all_schemes.get(k, {}).get("eligible", False)
    ]

    data["total_eligible_count"] = len(eligible_keys)
    data["eligible_scheme_keys"] = eligible_keys
    data["eligible"] = len(eligible_keys) > 0
    data["primary_eligible_scheme"] = eligible_keys[0] if eligible_keys else None
    data["scheme"] = data["primary_eligible_scheme"] or None

    return data


def parse_by_keywords(text: str) -> dict:
    result = {
        "eligible": False,
        "scheme": None,
        "all_schemes": {
            "PMAY": {
                "eligible": False,
                "reason": "Could not parse AI response",
                "confidence": 0,
            },
            "PM-KISAN": {
                "eligible": False,
                "reason": "Could not parse AI response",
                "confidence": 0,
            },
            "AYUSHMAN_BHARAT": {
                "eligible": False,
                "reason": "Could not parse AI response",
                "confidence": 0,
            },
            "SC_ST_SCHOLARSHIP": {
                "eligible": False,
                "reason": "Could not parse AI response",
                "confidence": 0,
            },
        },
        "applicant_details": {},
        "primary_eligible_scheme": None,
        "total_eligible_count": 0,
        "summary": "Could not determine eligibility",
    }

    return normalize_result(result)


def get_fallback_response() -> str:
    fallback = {
        "eligible": False,
        "scheme": None,
        "all_schemes": {
            "PMAY": {
                "eligible": False,
                "reason": "Bedrock unavailable — please retry",
                "confidence": 0,
            },
            "PM-KISAN": {
                "eligible": False,
                "reason": "Bedrock unavailable — please retry",
                "confidence": 0,
            },
            "AYUSHMAN_BHARAT": {
                "eligible": False,
                "reason": "Bedrock unavailable — please retry",
                "confidence": 0,
            },
            "SC_ST_SCHOLARSHIP": {
                "eligible": False,
                "reason": "Bedrock unavailable — please retry",
                "confidence": 0,
            },
        },
        "applicant_details": {},
        "primary_eligible_scheme": None,
        "total_eligible_count": 0,
        "summary": "Could not reach Bedrock — please retry",
    }

    return json.dumps(fallback)


def get_eligible_scheme_keys(eligibility_data: dict) -> list:
    all_schemes = eligibility_data.get("all_schemes", {})
    return [
        k for k in SCHEME_PRIORITY
        if all_schemes.get(k, {}).get("eligible", False)
    ]


def get_applicant_details(eligibility_data: dict) -> dict:
    return eligibility_data.get("applicant_details", {})