# Local Development Guide

This guide provides step-by-step instructions for setting up and running the RAG Agent application on your local machine.

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd rag-agent
```

## Step 2: Set Up Python Environment

It's recommended to use a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install azure-storage-blob email-validator flask flask-login flask-sqlalchemy flask-wtf gunicorn psycopg2-binary pypdf2 sqlalchemy werkzeug wtforms
```

## Step 4: Set Up PostgreSQL Database

1. Install PostgreSQL if you haven't already:
   - [Windows](https://www.postgresql.org/download/windows/)
   - [macOS](https://www.postgresql.org/download/macosx/)
   - [Linux](https://www.postgresql.org/download/linux/)

2. Create a database:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # Create a database
   CREATE DATABASE ragagent;
   
   # Exit PostgreSQL
   \q
   ```

## Step 5: Set Up Azure Blob Storage

1. Sign into the [Azure Portal](https://portal.azure.com/)
2. Create a Storage Account if you don't have one already
3. In your Storage Account, navigate to "Access keys" and copy one of the connection strings

## Step 6: Configure Environment Variables

1. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
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
   SESSION_SECRET=your_secret_key_for_flask_sessions
   ```

## Step 7: Verify Your Setup

Run the environment check script:

```bash
python check_environment.py
```

This will verify that all dependencies and configurations are set up correctly.

## Step 8: Run the Application

```bash
python main.py
```

The application should now be running at: http://localhost:5000

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running: 
  ```bash
  # On Windows
  net start postgresql

  # On macOS
  brew services start postgresql

  # On Linux
  sudo service postgresql start
  ```

- Check your database credentials in the `.env` file
- Make sure the user has privileges to create tables:
  ```sql
  GRANT ALL PRIVILEGES ON DATABASE ragagent TO postgres;
  ```

### Azure Blob Storage Issues

- Verify your Azure Storage connection string
- Ensure your Azure account has sufficient permissions
- The container "documents" will be created automatically if it doesn't exist

### Module Import Errors

If you encounter import errors, make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Application Errors

- Check the console for error messages
- If the application crashes, try running with debug mode:
  ```bash
  # Edit main.py to include debug=True
  app.run(host='0.0.0.0', port=5000, debug=True)
  ```

## Development Tips

### Working with Templates

- Templates are located in the `templates` directory
- Changes to templates are reflected immediately (no restart needed)

### Database Migrations

This project doesn't use a migration system, but if you make changes to models:

1. Update the models in `models.py`
2. Restart the application - tables will be created or updated

### Adding New Dependencies

If you add new dependencies, remember to:

1. Install them with pip
2. Add them to your local documentation for others

## Testing

To test document upload functionality:
1. Register an account
2. Log in
3. Upload a PDF file
4. Create a chat session with the document
5. Ask questions about the document content