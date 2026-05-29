import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

print("=" * 50)
print("ADHIKAR-AGENT BACKEND TEST")
print("=" * 50)

# ─────────────────────────────────────────
# TEST 1: AWS CREDENTIALS
# ─────────────────────────────────────────
print("\n[TEST 1] Checking AWS credentials...")
if AWS_KEY and AWS_SECRET:
    print(f"  ✅ Access Key found: {AWS_KEY[:8]}...")
    print(f"  ✅ Region: {AWS_REGION}")
else:
    print("  ❌ AWS credentials not found in .env file")
    print("  Fix: Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to .env")
    exit()

# ─────────────────────────────────────────
# TEST 2: TEXTRACT CONNECTION
# ─────────────────────────────────────────
print("\n[TEST 2] Testing AWS Textract connection...")
try:
    textract = boto3.client(
        'textract',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET
    )

    # Create a tiny dummy white image to test Textract
    import struct, zlib

    def create_test_image():
        # Minimal valid 1x1 white PNG
        def png_chunk(name, data):
            c = zlib.crc32(name + data) & 0xffffffff
            return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
        
        header = b'\x89PNG\r\n\x1a\n'
        ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
        idat = png_chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
        iend = png_chunk(b'IEND', b'')
        return header + ihdr + idat + iend

    test_image = create_test_image()
    response = textract.detect_document_text(Document={'Bytes': test_image})
    print("  ✅ Textract is CONNECTED and WORKING")
    print(f"  ✅ Response received — blocks: {len(response.get('Blocks', []))}")

except Exception as e:
    print(f"  ❌ Textract FAILED: {str(e)}")
    print("  Fix: Check IAM has AmazonTextractFullAccess policy")

# ─────────────────────────────────────────
# TEST 3: TEXTRACT ON A REAL IMAGE
# ─────────────────────────────────────────
print("\n[TEST 3] Testing Textract on a real sample image...")
try:
    # Create a simple test image with text using PIL if available
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Name: Ramesh Kumar", fill='black')
        draw.text((10, 40), "Date of Birth: 01/01/1985", fill='black')
        draw.text((10, 70), "State: Maharashtra", fill='black')
        draw.text((10, 100), "Income: 85000", fill='black')

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        response = textract.detect_document_text(Document={'Bytes': img_bytes})
        extracted_lines = [b['Text'] for b in response.get('Blocks', []) if b['BlockType'] == 'LINE']
        print("  ✅ Textract extracted text from image:")
        for line in extracted_lines:
            print(f"     → {line}")

    except ImportError:
        print("  ⚠️  PIL not installed — skipping image text test")
        print("  Run: pip install Pillow")

except Exception as e:
    print(f"  ❌ Real image test FAILED: {str(e)}")

# ─────────────────────────────────────────
# TEST 4: NOVA PRO CONNECTION
# ─────────────────────────────────────────
print("\n[TEST 4] Testing Amazon Nova Pro connection...")
try:
    bedrock = boto3.client(
        'bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET
    )

    response = bedrock.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Reply with just the word: WORKING"}]
                }
            ],
            "inferenceConfig": {"maxTokens": 10, "temperature": 0.1}
        })
    )

    result = json.loads(response['body'].read())
    reply = result['output']['message']['content'][0]['text']
    print(f"  ✅ Nova Pro is CONNECTED and WORKING")
    print(f"  ✅ Model replied: {reply}")

except Exception as e:
    print(f"  ❌ Nova Pro FAILED: {str(e)}")
    print("  Fix: Check IAM has AmazonBedrockFullAccess policy")

# ─────────────────────────────────────────
# TEST 5: FULL PIPELINE TEST
# ─────────────────────────────────────────
print("\n[TEST 5] Testing full pipeline (Textract → Nova → JSON)...")
try:
    sample_text = """
    Name: Ramesh Kumar
    Date of Birth: 01/01/1985
    State: Maharashtra
    Annual Income: 95000
    Caste: OBC
    BPL Status: Yes
    Address: 45 Gandhi Nagar, Mumbai
    Aadhaar: XXXX-XXXX-5678
    """

    response = bedrock.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": f"""Extract details from this document and output ONLY valid JSON:
{{
  "name": "",
  "age": "",
  "income": "",
  "caste": "",
  "state": "",
  "is_bpl": true or false,
  "eligible": true or false,
  "scheme": "PMAY"
}}

Document:
{sample_text}"""}]
                }
            ],
            "inferenceConfig": {"maxTokens": 500, "temperature": 0.1}
        })
    )

    result = json.loads(response['body'].read())
    ai_output = result['output']['message']['content'][0]['text']

    json_start = ai_output.find('{')
    json_end = ai_output.rfind('}') + 1
    parsed = json.loads(ai_output[json_start:json_end])

    print("  ✅ Full pipeline WORKING")
    print("  ✅ Nova extracted this JSON:")
    print(json.dumps(parsed, indent=4))

except Exception as e:
    print(f"  ❌ Pipeline test FAILED: {str(e)}")

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
print("\n" + "=" * 50)
print("TEST COMPLETE — Fix any ❌ above before running demo")
print("=" * 50)
