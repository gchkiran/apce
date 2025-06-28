# 📚 Academic Paper Citation Explorer (APCE)

![Deployed](https://img.shields.io/badge/status-deployed-brightgreen)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Azure](https://img.shields.io/badge/cloud-Azure-blue)
![Flask](https://img.shields.io/badge/framework-Flask-orange)

**Academic Paper Citation Explorer (APCE)** is a cloud-native, AI-powered research assistant that streamlines citation exploration for academic PDFs. Leveraging **Retrieval-Augmented Generation (RAG)** and Microsoft Azure, APCE enables researchers to upload papers, automatically extract and summarize citations, explore them through graph visualizations, and ask contextual questions—making literature reviews faster and more intuitive.

Developed as part of a master’s project at Georgia State University, APCE combines intelligent document processing, semantic search, and a scalable cloud-native backend.

---

## 🚀 Live Demo

🔴 **Temporarily Unavailable**  
Due to the expiration of the student Azure credit, the live demo is currently offline.  
We plan to restore access soon via alternative hosting or updated cloud credits.

Former link (inactive):  
🔗 [https://apce-webapp.azurewebsites.net/dashboard](https://apce-webapp.azurewebsites.net/dashboard)

---

## 🧠 Features

- 📄 **PDF Upload & Citation Extraction**  
  Automatically detects and extracts citations from academic papers using NLP and structured parsing.

- 🧠 **AI-Powered Summaries & Q&A**  
  Uses large language models (LLMs) with semantic search to summarize citations and answer user questions like _"Why was this reference included?"_

- ☁️ **Cloud-Native Infrastructure**  
  Built and deployed on Microsoft Azure with App Service, Blob Storage, PostgreSQL, and secured virtual networks.

- ⚙️ **Infrastructure as Code**  
  Fully managed with Terraform for scalable and repeatable deployments.

---

## 🏗️ Architecture Overview

| Component | Stack |
|----------|-------|
| Frontend | Flask + Jinja2 + Bootstrap |
| Backend  | Python + Flask |
| Database | PostgreSQL |
| Storage  | Azure Blob Storage |
| Cloud Platform | Azure App Service, Azure VNet, Azure Network Watcher |
| DevOps | Terraform (IaC) |
| AI | LLMs with Retrieval-Augmented Generation (RAG) |

---

## 🔧 Installation & Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Azure Storage Account
- Terraform
- Git

### 1. Clone and Set Up Project

```bash
git clone https://github.com/your-username/apce.git
cd apce
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Update the `.env` file:

```env
SECRET_KEY=your-secret-key
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
POSTGRES_URL=your-db-host
POSTGRES_USER=your-db-username
POSTGRES_PW=your-db-password
POSTGRES_DB=your-db-name
```

### 3. Run Locally

```bash
python main.py
```

Visit `http://localhost:5000` in your browser.

---

## ☁️ Azure Deployment (Terraform)

```bash
cd apce-infra
terraform init
terraform apply
```

Deployed components:
- Azure App Service
- Azure Blob Storage
- Azure VNet
- PostgreSQL (local or Azure)

---

## 📁 Project Structure

```
├── main.py                   # Entry point
├── app.py                    # Flask app factory
├── routes.py                 # Core routing
├── auth.py                   # Authentication
├── document_manager.py       # Uploads, parsing
├── rag_system.py             # Citation summarization and Q&A
├── azure_blob_manager.py     # Azure integration
├── models.py                 # DB schema
├── templates/                # Jinja2 frontend templates
├── static/                   # CSS, assets
├── uploads/                 # Temporary storage
├── apce-infra/              # Terraform scripts
├── config.py                 # Env configs
```

---

## 📊 Results & Evaluation

- ✅ **>90% accuracy** in citation extraction from structured PDFs.
- 🧠 **LLM responses** were rated as highly relevant in testing, enabling faster comprehension of references.
- ⚡ **1–2 sec average** query response time.

---

## 📉 Cloud Cost Summary

- 💸 **Total Cost (April 19–25, 2025)**: **$4.25**
- 🚀 100% of cost from Azure App Service (backend)
- Blob storage, VNet, and other services remained within free/student-tier limits.

---

## 🔍 Limitations & Trade-offs

- Limited to Azure Student Subscription (no premium instances or HA databases).
- Current version uses Azure-hosted PostgreSQL is planned.
- Summaries may oversimplify highly technical material — user discretion advised.

---

## 🔮 Future Enhancements

- Vector search via Azure AI Search
- Multi-paper citation clustering
- Role-based access and analytics dashboard
- Real-time LLM streaming for Q&A
- Enhanced document management and search filters

---

## 👨‍💻 Authors

Developed as part of the Master’s Cloud Computing Project at **Georgia State University — 2025**

- **Chandra Kiran Guntupalli**  
  [LinkedIn](https://www.linkedin.com/in/gchandrakiran) · cguntupalli1@student.gsu.edu

---

## 📑 References

1. Lewis et al. (2020) – Retrieval-Augmented Generation  
2. PyMuPDF Documentation – [fitz](https://pymupdf.readthedocs.io)  
3. Devlin et al. (2019) – BERT  
4. Langchain – [https://www.langchain.com/](https://www.langchain.com/)  
5. Groq Docs – [https://console.groq.com/docs/models](https://console.groq.com/docs/models)

---