#!/usr/bin/env python3
"""
Check if all the required dependencies and environment variables are set up correctly.
Run this script before starting the application to verify your setup.
"""
import os
import sys
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Required packages
REQUIRED_PACKAGES = [
    'azure.storage.blob',
    'email_validator',
    'flask',
    'flask_login',
    'flask_sqlalchemy',
    'flask_wtf',
    'gunicorn',
    'psycopg2',
    'PyPDF2',
    'sqlalchemy',
    'werkzeug',
    'wtforms',
]

# Required environment variables
REQUIRED_ENV_VARS = [
    'PGUSER',
    'PGPASSWORD',
    'PGHOST',
    'PGPORT',
    'PGDATABASE',
    'DATABASE_URL',
    'AZURE_STORAGE_CONNECTION_STRING',
    'AZURE_BLOB_CONTAINER_NAME',
    'SESSION_SECRET',
]

def check_packages():
    """Check if all required packages are installed."""
    logger.info("Checking required packages...")
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        # Convert from import format to package name if needed
        package_name = package.split('.')[0]
        if package_name == 'PyPDF2':
            package_name = 'pypdf2'  # Special case for PyPDF2
            
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error("Missing packages: %s", ', '.join(missing_packages))
        logger.info("Install them using: pip install %s", ' '.join(missing_packages))
        return False
    
    logger.info("All required packages are installed.")
    return True

def check_env_vars():
    """Check if all required environment variables are set."""
    logger.info("Checking environment variables...")
    
    # Check if .env file exists and load it
    if os.path.exists('.env'):
        logger.info("Found .env file, attempting to load variables...")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if var not in os.environ or not os.environ[var]:
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("Missing environment variables: %s", ', '.join(missing_vars))
        logger.info("Add them to your .env file or export them in your shell.")
        return False
    
    logger.info("All required environment variables are set.")
    return True

def check_database():
    """Check if the database is accessible."""
    logger.info("Checking database connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            host=os.environ.get('PGHOST'),
            port=os.environ.get('PGPORT'),
            database=os.environ.get('PGDATABASE')
        )
        conn.close()
        logger.info("Database connection successful.")
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return False

def check_azure_blob():
    """Check if Azure Blob Storage is accessible."""
    logger.info("Checking Azure Blob Storage connection...")
    try:
        from azure.storage.blob import BlobServiceClient
        conn_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.environ.get('AZURE_BLOB_CONTAINER_NAME')
        
        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        
        # Get a client to reference the container
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check if the container exists
        try:
            container_client.get_container_properties()
            logger.info(f"Container '{container_name}' exists.")
        except Exception:
            logger.warning(f"Container '{container_name}' does not exist. It will be created when the app runs.")
        
        logger.info("Azure Blob Storage connection successful.")
        return True
    except Exception as e:
        logger.error("Azure Blob Storage connection failed: %s", e)
        logger.warning("The app will fall back to local storage if Azure Blob Storage is not available.")
        return False

def main():
    """Run all checks."""
    packages_ok = check_packages()
    env_vars_ok = check_env_vars()
    database_ok = check_database() if env_vars_ok else False
    azure_ok = check_azure_blob() if env_vars_ok else False
    
    if all([packages_ok, env_vars_ok, database_ok]):
        logger.info("Environment checks passed! Your system is ready to run the application.")
        if not azure_ok:
            logger.warning("Azure Blob Storage is not properly configured. The app will use local storage.")
        return 0
    else:
        logger.error("Environment checks failed. Please fix the issues before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main())