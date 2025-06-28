
# Academic Paper Citation Explorer (APCE)

Academic Paper Citation Explorer (APCE) is a cloud-native, retrieval-augmented generation (RAG) system that allows users to upload academic papers (PDFs), extract and explore citations, and interact with AI-powered summaries and Q&A features. The system integrates secure user authentication, Azure Blob Storage for document management, PostgreSQL for user and document metadata, and a simple UI built with Flask and Bootstrap.

---

# Architecture Overview

- Frontend: Flask (Jinja2 templates) + Bootstrap CSS
- Backend: Python + Flask
- Database: PostgreSQL (for user, document, and chat session metadata)
- Cloud Storage: Azure Blob Storage
- LLM + RAG: Python-based semantic document search & summarization
- Infrastructure-as-Code: Terraform for deploying Azure resources

---

# Prerequisites

Before getting started, ensure you have the following:

- Python 3.9+
- PostgreSQL (local or managed)
- Azure Storage Account (Blob)
- Azure App Service setup (optional for local testing)
- Terraform (for infrastructure provisioning)
- Git (to clone the repository)

---

# Installation & Setup

## 1. Extract the zip file


## 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Update the following variables:

```env
SECRET_KEY=your-secret-key
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
POSTGRES_URL=your-db-host
POSTGRES_USER=your-db-username
POSTGRES_PW=your-db-password
POSTGRES_DB=your-db-name
```

## 5. Run Environment Check (Optional)

```bash
python check_environment.py
```

## 6. Start the Application

```bash
python main.py
```

Visit `http://localhost:5000` in your browser.

---

#  Azure Cloud Deployment

- Backend hosted on Azure App Service
- Documents stored in Azure Blob Storage
- PostgreSQL managed locally or via Azure PostgreSQL
- Network security managed via Azure VNet
- Deployment infrastructure is defined using Terraform (in `/apce-infra`)

To deploy via Terraform:

```bash
cd apce-infra
terraform init
terraform apply
```

---

# Key File Structure

```
├── main.py                   # Entry point
├── app.py                   # Flask app factory
├── routes.py                # Core routing
├── auth.py                  # Authentication
├── document_manager.py      # Uploads, parsing
├── rag_system.py            # Citation summarization and Q&A
├── models.py                # Database models
├── templates/               # Jinja2 frontend templates
├── static/                  # CSS & images
├── uploads/                 # Temporary local file storage
├── config.py                # Environment config
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
```

---

# Database Schema

- `User`: Stores user credentials and profile info
- `Document`: Metadata for uploaded PDFs
- `ChatSession`: Associated with user and document
- `ChatMessage`: Message content within each session

---

#  Future Enhancements

- Azure AI Search with vector embeddings
- Chat session streaming and live summarization
- Citation network clustering across multiple papers
- Advanced user role management and analytics

---

# Live Demo

Deployed version:  
🔗 [https://apce-webapp.azurewebsites.net/dashboard](https://apce-webapp.azurewebsites.net/dashboard)

---

##  Acknowledgments

Built as part of the Master’s Cloud Computing Project  
Georgia State University — 2025  
Team Members:  
- Chandra Kiran Guntupalli  
- Chandra Sai Reddy Donthireddy  
- Shishir Kumar Vallapuneni  
