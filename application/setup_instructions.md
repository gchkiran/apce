# RAG Agent with Azure Setup Instructions

## Dependencies

Install the following Python packages:

```bash
pip install azure-storage-blob==12.25.1
pip install email-validator==2.1.0
pip install flask==3.0.0
pip install flask-login==0.6.3
pip install flask-sqlalchemy==3.1.1
pip install flask-wtf==1.2.1
pip install gunicorn==23.0.0
pip install psycopg2-binary==2.9.9
pip install pypdf2==3.0.1
pip install sqlalchemy==2.0.28
pip install werkzeug==3.0.1
pip install wtforms==3.1.2
```

Or install all at once:

```bash
pip install azure-storage-blob email-validator flask flask-login flask-sqlalchemy flask-wtf gunicorn psycopg2-binary pypdf2 sqlalchemy werkzeug wtforms langchain_groq
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# PostgreSQL Configuration
PGUSER=postgres
PGPASSWORD=your_password
PGHOST=localhost
PGPORT=5432
PGDATABASE=ragagent
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ragagent

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
AZURE_BLOB_CONTAINER_NAME=documents

# Flask Configuration
SESSION_SECRET=dev_secret_key
```

## Database Setup

1. Install PostgreSQL on your local machine if you haven't already
2. Create a database named 'ragagent':
   ```bash
   createdb ragagent
   ```
   Or using PostgreSQL CLI:
   ```bash
   psql -U postgres
   CREATE DATABASE ragagent;
   ```

## Running the Application

1. Make sure your environment variables are set (either in .env file or exported in your shell)
2. Run the application:
   ```bash
   python main.py
   ```
   Or with gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

3. Access the application at http://localhost:5000

## Important Notes

- The application will use Azure Blob Storage for document uploads and storage
- If Azure Blob Storage is not properly configured, the application will fall back to local file storage
- All documents are stored with their extracted text content for searching
- The application creates a container named 'documents' in your Azure Storage account if it doesn't exist