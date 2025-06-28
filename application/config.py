import os

from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration
POSTGRES_USER = os.environ.get('PGUSER')
POSTGRES_PASSWORD = os.environ.get('PGPASSWORD')
POSTGRES_HOST = os.environ.get('PGHOST')
POSTGRES_PORT = os.environ.get('PGPORT')
POSTGRES_DB = os.environ.get('PGDATABASE')
DATABASE_URL = os.environ.get('DATABASE_URL')

# Upload Configuration (for local fallback if needed)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_BLOB_CONTAINER_NAME = os.environ.get('AZURE_BLOB_CONTAINER_NAME')

# Flask Configuration
SESSION_SECRET = os.environ.get('SESSION_SECRET')
