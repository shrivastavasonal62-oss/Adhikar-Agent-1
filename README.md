Adhikar Agent
(AI-Powered Government Scheme Eligibility & Application Automation System)

Adhikar Agent helps citizens identify their eligibility for government welfare schemes by simply uploading their documents. The system uses OCR and Generative AI to extract information, analyze eligibility, and automatically generate pre-filled application forms.

**Problem Statement**

Millions of eligible citizens fail to receive government benefits because:
* Eligibility criteria are difficult to understand
* Application processes are complex
* Citizens rely on middlemen and agents
* Manual form filling is time-consuming
* Awareness of available schemes is limited

Adhikar Agent solves these challenges using AI-driven automation.

**Features**

Intelligent Document Processing
* Aadhaar Card OCR
* Income Certificate OCR
* Ration Card OCR
* Caste Certificate OCR
* PDF and Image Support

Privacy Protection
* Aadhaar masking before AI processing
* Sensitive information protection
* Secure document handling

AI Eligibility Analysis
Checks eligibility for:
* PMAY (Pradhan Mantri Awas Yojana)
* PM-KISAN
* Ayushman Bharat
* SC/ST Scholarship

Automated Application Generation
* Auto-filled application forms
* Downloadable PDF output
* Reduced manual effort


System Architecture

User Uploads Documents

↓

AWS Textract OCR

↓

Structured Data Extraction

↓

Amazon Nova Pro (Bedrock)

↓

Eligibility Analysis

↓

PDF Auto-Fill Engine

↓

Download Application Form




**Tech Stack**

Frontend
* HTML5
* CSS3
* JavaScript

Backend
* Python
* FastAPI

AWS Services
* AWS Textract
* Amazon Bedrock
* Amazon Nova Pro

PDF Processing
* ReportLab
* PyMuPDF



**Project Structure**

backend/

├── main.py

├── requirements.txt

├── services/

│ ├── ocr_service.py

│ ├── eligibility_service.py

│ └── pdf_service.py

└── templates/



frontend/

├── index.html

├── styles.css

├── script.js

└── emblem.png


**Installation**

Clone Repository
git clone https://github.com/shrivastavasonal62-oss/Adhikar-Agent-1.git

**Backend Setup**

cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt


**Configure Environment Variables**

Create a .env file:

AWS_ACCESS_KEY_ID=YOUR_KEY

AWS_SECRET_ACCESS_KEY=YOUR_SECRET

AWS_REGION=us-east-1

**Run Backend**

python main.py

Run Frontend

cd frontend

python -m http.server 5500
Open:
http://127.0.0.1:5500

**Screenshots**

<img width="932" height="434" alt="image" src="https://github.com/user-attachments/assets/f6c26f15-d399-4fc3-b97f-8733073bc3ae" />


**AI Processing Terminal**

<img width="901" height="427" alt="image" src="https://github.com/user-attachments/assets/6cefb8ec-54e5-4ef1-9f94-18675b70718d" />


**Eligibility Results**

<img width="899" height="431" alt="image" src="https://github.com/user-attachments/assets/136e5d12-e9ec-4081-bd47-3a34b16e242c" />


**Auto-Filled Application Form**

<img width="370" height="408" alt="image" src="https://github.com/user-attachments/assets/86e9ce21-42f9-48d0-b288-0c095f1122fb" />



**Future Enhancements**

* Support for 50+ Government Schemes
* Multi-language Support
* Mobile Application
* Voice-based Assistance
* Direct Government Portal Integration

---

