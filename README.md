# 🏛️ Adhikar Agent

### AI-Powered Government Scheme Eligibility & Application Automation Platform

Adhikar Agent is an intelligent multimodal AI system that simplifies access to government welfare schemes by automatically analyzing citizen documents, determining scheme eligibility, and generating pre-filled application forms.

The platform leverages OCR, Generative AI, and document automation to reduce bureaucratic complexity and bridge the gap between citizens and government services.

---

##  Project Overview

Millions of eligible citizens fail to receive government benefits due to complex eligibility criteria, lengthy paperwork, lack of awareness, and dependency on intermediaries.

Adhikar Agent addresses these challenges through AI-driven automation by enabling users to:

✅ Upload government documents

✅ Extract structured information automatically

✅ Determine eligibility for welfare schemes

✅ Generate pre-filled application forms

✅ Reduce manual effort and processing time

---

## 🎯 Problem Statement

Accessing government welfare schemes remains difficult for many citizens because:

* Eligibility requirements are often difficult to understand
* Application procedures are lengthy and complex
* Citizens rely on agents and intermediaries
* Manual form filling is error-prone
* Awareness about available schemes is limited

These challenges result in eligible beneficiaries being excluded from welfare programs.

---

## 💡 Solution

Adhikar Agent uses Artificial Intelligence and Document Understanding to automate the complete workflow.

### Workflow

```text
Citizen Uploads Documents
            │
            ▼
      AWS Textract OCR
            │
            ▼
 Structured Information Extraction
            │
            ▼
 Amazon Nova Pro (Generative AI)
            │
            ▼
 Eligibility Analysis Engine
            │
            ▼
 Auto-Filled PDF Generation
            │
            ▼
 Download Ready Application Form
```

---

## ✨ Key Features

### 📄 Intelligent Document Processing

Supports extraction from:

* Aadhaar Card
* Income Certificate
* Caste Certificate
* Ration Card
* PDF Documents
* Scanned Images

### 🔒 Privacy Protection

* Aadhaar Number Masking
* Sensitive Data Protection
* Secure AI Processing Pipeline
* Privacy-Aware Document Handling

### 🤖 AI-Powered Eligibility Analysis

Automatically evaluates eligibility for:

* PMAY (Pradhan Mantri Awas Yojana)
* PM-KISAN
* Ayushman Bharat
* SC/ST Scholarship Schemes

### 📑 Automated Application Generation

* Pre-filled Government Forms
* Downloadable PDF Output
* Reduced Manual Effort
* Faster Application Process

---

## 🛠️ Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* FastAPI

### Artificial Intelligence

* Amazon Bedrock
* Amazon Nova Pro
* Prompt Engineering

### OCR & Document Intelligence

* AWS Textract

### PDF Automation

* ReportLab
* PyMuPDF

### Cloud Infrastructure

* AWS Cloud Services

---

## 📂 Project Structure

```text
Adhikar-Agent/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── services/
│   │   ├── ocr_service.py
│   │   ├── eligibility_service.py
│   │   └── pdf_service.py
│   └── templates/
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   └── emblem.png
│
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/shrivastavasonal62-oss/Adhikar-Agent-1.git
```

### Backend Setup

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_REGION=us-east-1
```

### Run Backend

```bash
python main.py
```

### Run Frontend

```bash
cd frontend

python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

---

## 📸 Application Screenshots

### Document Upload Interface

<img width="932" height="434" alt="image" src="https://github.com/user-attachments/assets/f6c26f15-d399-4fc3-b97f-8733073bc3ae" />

---

### AI Processing Pipeline

<img width="901" height="427" alt="image" src="https://github.com/user-attachments/assets/6cefb8ec-54e5-4ef1-9f94-18675b70718d" />

---

### Eligibility Analysis Results

<img width="899" height="431" alt="image" src="https://github.com/user-attachments/assets/136e5d12-e9ec-4081-bd47-3a34b16e242c" />

---

### Auto-Filled Application Form

<img width="370" height="408" alt="image" src="https://github.com/user-attachments/assets/86e9ce21-42f9-48d0-b288-0c095f1122fb" />

---

## 🎯 Real-World Impact

Adhikar Agent aims to:

* Improve accessibility to welfare schemes
* Reduce paperwork and administrative burden
* Minimize dependency on intermediaries
* Increase scheme awareness among citizens
* Accelerate application processing

---

## 🔮 Future Enhancements

* Support for 50+ Government Schemes
* Multi-Language Support
* Mobile Application
* Voice-Based Assistance
* OCR for Regional Languages
* Direct Government Portal Integration
* Citizen Eligibility Dashboard
* Real-Time Application Tracking

---

## 👨‍💻 Author

### Sonal Shrivastava

B.Tech Computer Science Engineering

Areas of Interest:

* Artificial Intelligence
* Generative AI
* Machine Learning
* Cloud Computing
* Software Development

GitHub:
https://github.com/shrivastavasonal62-oss

LinkedIn:
(Add Your LinkedIn Profile)

---

## ⭐ Support

If you found this project useful, consider giving it a star ⭐ on GitHub.
