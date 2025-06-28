# Useful Commands

This document contains useful commands for managing and developing the RAG Agent application.

## Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Install dependencies
pip install -r requirements.txt

# Freeze dependencies
pip freeze > requirements.txt
```

## PostgreSQL Commands

```bash
# Connect to PostgreSQL
psql -U postgres

# List databases
\l

# Connect to ragagent database
\c ragagent

# List tables
\dt

# Describe a table
\d users

# Backup database
pg_dump -U postgres ragagent > backup.sql

# Restore database
psql -U postgres ragagent < backup.sql

# Exit PostgreSQL CLI
\q
```

## Flask Commands

```bash
# Run the application
python main.py

# Run with gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app

# Development mode with auto-reload
FLASK_APP=main.py FLASK_ENV=development flask run
```

## Azure Blob Storage Commands

```bash
# List all blobs in a container using Azure CLI
az storage blob list --container-name documents --connection-string "your_connection_string" --output table

# Upload a file to Azure Blob Storage using Azure CLI
az storage blob upload --container-name documents --file local_file.pdf --name remote_name.pdf --connection-string "your_connection_string"

# Download a blob from Azure Blob Storage using Azure CLI
az storage blob download --container-name documents --name remote_name.pdf --file local_file.pdf --connection-string "your_connection_string"

# Delete a blob from Azure Blob Storage using Azure CLI
az storage blob delete --container-name documents --name remote_name.pdf --connection-string "your_connection_string"
```

## Docker (If you decide to containerize)

```bash
# Build Docker image
docker build -t rag-agent .

# Run Docker container
docker run -d -p 5000:5000 --name rag-agent-container rag-agent

# View logs
docker logs rag-agent-container

# Stop container
docker stop rag-agent-container

# Remove container
docker rm rag-agent-container
```

## Git Commands

```bash
# Check status
git status

# Create a new branch
git checkout -b feature/new-feature

# Add changes
git add .

# Commit changes
git commit -m "Add new feature"

# Push changes
git push origin feature/new-feature

# Pull changes
git pull origin main
```

## Testing

```bash
# Install pytest
pip install pytest

# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

## Maintenance

```bash
# Clear cache and temp files
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Check for security vulnerabilities
pip install safety
safety check
```