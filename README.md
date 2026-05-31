<div align="center">
  <img src="https://img.shields.io/badge/BlindWatch-AI-06b6d4?style=for-the-badge&logo=openai&logoColor=white" alt="BlindWatch AI Logo" />
  <h1 align="center">BlindWatch AI: The Privacy-First Surveillance OS</h1>
  <p align="center">
    <strong>Enterprise-grade computer vision, dynamic threat intelligence, and zero-trust privacy compliance.</strong>
  </p>

  <p align="center">
    <a href="https://reactjs.org/">
      <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" alt="Next.js" />
    </a>
    <a href="https://fastapi.tiangolo.com/">
      <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
    </a>
    <a href="https://www.sqlalchemy.org/">
      <img src="https://img.shields.io/badge/SQLAlchemy-ORM-d71f00?style=flat-square&logo=sqlalchemy" alt="SQLAlchemy" />
    </a>
    <a href="https://ultralytics.com/">
      <img src="https://img.shields.io/badge/YOLO-Computer_Vision-00FFFF?style=flat-square&logo=ultralytics" alt="YOLO" />
    </a>
  </p>
</div>

<hr />

## 👁️ Overview

**BlindWatch AI** is a next-generation surveillance operating system designed for modern enterprises. Traditional CCTV compromises privacy for security. BlindWatch AI delivers both. By utilizing edge-based AI anonymization, the system mathematically blurs all identities *before* the video stream reaches the command center, ensuring total GDPR & CCPA compliance. 

Identities are only unlocked via a cryptographic Governance Request system that requires multi-role authorization.

### ✨ Key Features
* **Dynamic Privacy Shield**: Automated face and entity blurring using YOLO pipelines.
* **Explainable AI (XAI)**: Understand *why* an event was flagged with risk-scoring heatmaps.
* **Threat Simulator**: Sandboxed testing environment to simulate physical security incidents.
* **Cryptographic Audit Ledger**: Immutable logging of every system action and identity reveal.
* **Multi-Tenant Monolith**: Architected for edge-deployments and Render free-tier cloud hosting.

---

## 🚀 Getting Started (Working Locally)

The platform is split into a **Next.js Frontend** and a **FastAPI Python Backend**. 

### 1. Start the Python Backend
The backend powers the vision engines, database, and telemetry streams. 

```bash
# Clone the repository
git clone https://github.com/Sanjaykumaar123/cod.git
cd cod

# Create a virtual environment & install dependencies
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# Start the cloud monolith backend (Port 8000)
python -m services.render_app
```
*(The backend will automatically seed the local SQLite database with default roles on the first boot).*

### 2. Start the Next.js Frontend
In a new terminal window, start the React command dashboard:

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the Operations Center.

### 🔐 Default Login Credentials
You can access the portal using any of the following roles:
* **Admin**: `admin` / `admin123` (Full System & Governance Access)
* **Officer**: `officer` / `officer123` (Threat Monitoring & Tactical Operations)
* **Auditor**: `auditor` / `auditor123` (Compliance Oversight)

---

## ☁️ Cloud Deployment (Render & Vercel)

BlindWatch AI is fully optimized for free-tier cloud deployment using a Monolithic ASGI pattern to prevent Out-Of-Memory (OOM) crashes.

1. **Backend (Render)**: Deploy the root folder as a Python Web Service. Use the start command: `uvicorn services.render_app:app --host 0.0.0.0 --port $PORT`. 
2. **Frontend (Vercel)**: Connect your repository to Vercel. Add the following Environment Variable:
   * `NEXT_PUBLIC_API_URL` = `https://your-render-url.onrender.com`

**Executive Demo Mode:** 
Once deployed, click the **Populate Demo Data** button in the Command Actions Vault to automatically seed the cloud database with 6 camera nodes, 50 entities, and historical event logs for demonstration purposes!

---

## 🛡️ Architecture & Compliance
* **Frontend**: Next.js (App Router), TailwindCSS, Recharts, Lucide Icons.
* **Backend**: FastAPI, SQLAlchemy (SQLite/PostgreSQL), PyJWT Auth.
* **Computer Vision**: PyTorch, Ultralytics YOLO, OpenCV (Gracefully disables on constrained cloud nodes).
* **Compliance**: Strict adherence to GDPR (Article 15, 17) and CCPA through mathematical redaction.

---
<div align="center">
  <i>"Security without compromise. Privacy by design."</i>
</div>
