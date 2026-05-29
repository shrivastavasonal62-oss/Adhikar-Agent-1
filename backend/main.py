from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

from services.ocr_service import process_documents
from services.eligibility_service import check_eligibility_with_bedrock
from services.pdf_service import auto_fill_pdf

app = FastAPI(title="Adhikar-Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Eligible-Schemes",
        "X-Eligibility-Data",
        "X-Applicant-Name",
        "X-Applicant-State",
        "X-Applicant-Income",
        "X-Applicant-BPL",
        "X-Applicant-Caste",
    ],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

os.makedirs(BASE_DIR / "outputs", exist_ok=True)
os.makedirs(BASE_DIR / "templates", exist_ok=True)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.post("/process-documents")
async def process_documents_endpoint(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 files allowed")

    print(f"\n{'=' * 50}")
    print(f"NEW REQUEST — {len(files)} file(s) received")
    print(f"{'=' * 50}")

    image_bytes_list = []

    for f in files:
        content = await f.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"File {f.filename} is empty")

        image_bytes_list.append(content)
        print(f"[MAIN] File received: {f.filename} ({len(content)} bytes)")

    print("\n[MAIN] Starting OCR pipeline...")

    try:
        ocr_result = process_documents(image_bytes_list)

        extracted_text = ocr_result["extracted_text"]
        structured_fields = ocr_result.get("structured_fields", {})
        doc_types = ocr_result.get("document_types", [])

        print(f"[MAIN] OCR complete. Doc types: {doc_types}")

        if "AADHAAR" not in doc_types:
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid Aadhaar Card.",
            )

        blocked_docs = ["PAN_CARD", "VOTER_ID", "UNKNOWN"]

        for doc in doc_types:
            if doc in blocked_docs:
                raise HTTPException(
                    status_code=400,
                    detail=f"{doc} is not accepted for scheme verification.",
                )

        print("[MAIN] Document validation passed.")

    except HTTPException:
        raise

    except Exception as e:
        print(f"[MAIN] OCR failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}",
        )

    print("\n[MAIN] Starting eligibility check...")

    try:
        combined_input = f"""
STRUCTURED FIELDS (pre-extracted):
{structured_fields}

FULL DOCUMENT TEXT:
{extracted_text}
"""

        eligibility_data = check_eligibility_with_bedrock(combined_input)

        all_schemes = eligibility_data.get("all_schemes", {})
        scheme_priority = [
            "PMAY",
            "PM-KISAN",
            "AYUSHMAN_BHARAT",
            "SC_ST_SCHOLARSHIP",
        ]

        primary = None

        for key in scheme_priority:
            if all_schemes.get(key, {}).get("eligible"):
                primary = key
                break

        eligibility_data["primary_eligible_scheme"] = primary
        print(f"[MAIN] Primary scheme set to: {primary}")

    except Exception as e:
        print(f"[MAIN] Eligibility check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Eligibility check failed: {str(e)}",
        )

    print("\n[MAIN] Generating PDF...")

    try:
        output_filename = BASE_DIR / "outputs" / f"application_{uuid.uuid4().hex[:8]}.pdf"
        template_path = BASE_DIR / "templates" / "pmay_form.pdf"

        auto_fill_pdf(str(template_path), str(output_filename), eligibility_data)
        print(f"[MAIN] PDF generated: {output_filename}")

    except Exception as e:
        print(f"[MAIN] PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}",
        )

    from services.eligibility_service import get_eligible_scheme_keys

    eligible_schemes = get_eligible_scheme_keys(eligibility_data)
    applicant = eligibility_data.get("applicant_details", {})

    headers = {
        "X-Eligible-Schemes": ",".join(eligible_schemes),
        "X-Applicant-Name": str(applicant.get("name", "")),
        "X-Applicant-State": str(applicant.get("state", "")),
        "X-Applicant-Income": str(applicant.get("annual_income", "")),
        "X-Applicant-BPL": str(applicant.get("is_bpl", "")),
        "X-Applicant-Caste": str(applicant.get("caste_category", "")),
    }

    print(f"\n[MAIN] Request complete. Eligible schemes: {eligible_schemes}")
    print(f"{'=' * 50}\n")

    return FileResponse(
        path=str(output_filename),
        media_type="application/pdf",
        filename="Adhikar_Application_Form.pdf",
        headers=headers,
    )


@app.get("/")
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"

    if index_path.exists():
        return FileResponse(index_path)

    return {
        "status": "running",
        "service": "Adhikar-Agent API",
        "version": "1.0.0",
        "endpoints": ["/process-documents", "/health", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "aws_region": os.getenv("AWS_REGION", "us-east-1")}


def map_scheme_to_key(scheme_name: str) -> str:
    s = scheme_name.upper()

    if "PMAY" in s or "AWAS" in s:
        return "PMAY"

    if "KISAN" in s or "FARMER" in s:
        return "PM-KISAN"

    if "AYUSHMAN" in s or "HEALTH" in s:
        return "AYUSHMAN_BHARAT"

    if "SCHOLAR" in s or "SC" in s:
        return "SC_ST_SCHOLARSHIP"

    return "PMAY"


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )