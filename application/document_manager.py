import os
import uuid
import io
import logging
from datetime import datetime
import tempfile
from models import Document
import requests
import re
from app import db
import fitz 
from io import BytesIO
import PyPDF2
from werkzeug.utils import secure_filename
from flask import current_app
from azure.storage.blob import BlobServiceClient, ContentSettings
from config import AZURE_STORAGE_CONNECTION_STRING, AZURE_BLOB_CONTAINER_NAME

# Set up logger
logger = logging.getLogger(__name__)

class DocumentManager:

    def __init__(self):
        """Initialize Azure Blob Storage connection"""
        # Azure Blob Storage setup
        self.connection_string = AZURE_STORAGE_CONNECTION_STRING
        self.container_name = AZURE_BLOB_CONTAINER_NAME

        # Create fallback local directory just in case
        self.uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(self.uploads_dir, exist_ok=True)

        # Initialize the blob service client
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name)

            # Initialize only on first use, not during global instantiation
            self.container_initialized = False
            logger.info(f"DocumentManager initialized with Azure Blob Storage")
        except Exception as e:
            logger.error(f"Error initializing Azure Blob Storage: {e}")
            self.blob_service_client = None
            self.container_client = None

    def container_exists(self):
        """Check if the Azure blob container exists"""
        try:
            if not self.container_initialized:
                self.container_client.get_container_properties()
                self.container_initialized = True
                logger.info("Container exists in Azure")
            return True
        except Exception as e:
            logger.warning(f"Container does not exist: {e}")
            return False

    def upload_document(self, file, title, user_id, rag_system):
        """Upload a document to Azure Blob Storage"""
        try:
            # Check if Azure connection is available
            if self.blob_service_client is None:
                raise Exception(
                    "Azure Blob Storage is not properly configured")

            # Make sure the container exists
            if not self.container_initialized:
                # Ensure container exists
                if not self.container_exists():
                    self.container_client.create_container()
                    logger.info(
                        f"Created Azure container: {self.container_name}")

            # Generate unique filename
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            safe_filename = secure_filename(file.filename)
            blob_name = f"{user_id}/{current_time}_{unique_id}_{safe_filename}"

            # Set content settings for the blob
            content_settings = ContentSettings(content_type=file.content_type)

            # Get blob client and upload the file
            blob_client = self.container_client.get_blob_client(blob_name)

            # Reset file pointer to beginning
            file.seek(0)

            # Upload to Azure
            blob_client.upload_blob(file,
                                    content_settings=content_settings,
                                    overwrite=True)

            # Get the URL for the blob
            blob_url = blob_client.url

            # Extract text from PDF for searching
            file.seek(0)
            text_content = self._extract_text_from_pdf(file)

            # Also upload the text content as a separate blob for searching
            text_blob_name = f"{blob_name}.txt"
            text_blob_client = self.container_client.get_blob_client(
                text_blob_name)
            text_blob_client.upload_blob(
                io.BytesIO(text_content.encode('utf-8')),
                content_settings=ContentSettings(content_type='text/plain'),
                overwrite=True)

            logger.info(f"Document uploaded to Azure: {blob_name}")

            # Extract citations using RAG system
            citation_titles = self._extract_citation_titles(text_content, rag_system)
            citation_docs = []
            
            # Process citations and store them
            for citation_title in citation_titles:
                try:
                    # Search for citation metadata and PDF using Semantic Scholar API
                    citation_metadata = self._search_citation(citation_title)
                    if citation_metadata and 'openAccessPdf' in citation_metadata:
                        # Download the PDF
                        pdf_file = self._download_pdf(citation_metadata)
                        if pdf_file:
                            # Upload citation PDF to Azure Blob Storage
                            citation_blob_name, citation_blob_url = self._upload_citation_pdf(
                                pdf_file, user_id, citation_title
                            )
                            
                            # Save citation document to database
                            citation_doc = Document(
                                title=citation_metadata.get('title', citation_title)[:100],
                                filename=f"{citation_blob_name}",
                                blob_url=citation_blob_url,
                                user_id=user_id,
                                parent_document_id=None  # Will be set after original document is saved
                            )
                            db.session.add(citation_doc)
                            citation_docs.append(citation_doc)
                except Exception as e:
                    logger.error(f"Error processing citation '{citation_title}': {str(e)}")
                    continue

            return blob_name, blob_url, citation_docs

        except Exception as e:
            logger.error(f"Azure upload error: {e}")
            raise
        
    def _extract_citation_titles(self, text_content, rag_system):
        """Extract citation paper titles using the RAG system"""
        try:
            query = "List the titles of papers cited in the references section of the document."
            response = rag_system._generate_llm_response(query, text_content)
            
             # Parse response and remove digits from titles
            titles = [
                re.sub(r'\d', '', line.strip())  # Remove all digits
                for line in response.split('\n') 
                if line.strip()
            ]
            # Parse response to extract titles (assuming response is a list or newline-separated)
            print(response.split('\n'))
            titles = [title.strip() for title in titles if title.strip()]
            return titles[:20]  # Limit to 10 citations to avoid overwhelming the system
        except Exception as e:
            current_app.logger.error(f"Citation extraction error: {e}")
            return []
        

    def _search_citation(self, citation_title):
        """Search for citation metadata and PDF using Semantic Scholar API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search/match",
                params={
                    "query": citation_title,
                    "fields": "openAccessPdf,title",
                    "openAccessPdf": "true"
                },
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                paper = data['data'][0]
                return {
                    'title': paper.get('title'),
                    'openAccessPdf': paper.get('openAccessPdf', {}).get('url') if paper.get('openAccessPdf') else None,

                }
            return None
        except Exception as e:
            current_app.logger.error(f"Semantic Scholar API error: {e}")
            return None
        

    def _download_pdf(self, metadata):
        """Download a PDF from a URL, skipping restricted access statuses"""
        pdf_url = metadata.get('openAccessPdf')
        status = metadata.get('openAccessPdfStatus')
        if not pdf_url:
            logger.info(f"No PDF URL provided in metadata")
            return None
        if status == 'BRONZE':
            logger.info(f"Skipping BRONZE open-access PDF at {pdf_url}")
            return None
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.semanticscholar.org/',
                'Accept': 'application/pdf'
            }
            response = requests.get(pdf_url, headers=headers, stream=True, allow_redirects=True, timeout=10)
            response.raise_for_status()
            if 'application/pdf' not in response.headers.get('Content-Type', ''):
                logger.error(f"URL {pdf_url} did not return a PDF; Content-Type: {response.headers.get('Content-Type')}")
                return None
            return io.BytesIO(response.content)
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error downloading PDF from {pdf_url}: {e}, Status: {response.status_code}, Response: {response.text[:200]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading PDF from {pdf_url}: {e}")
            return None

    def _upload_citation_pdf(self, pdf_file, user_id, citation_title):
        """Upload a citation PDF to Azure Blob Storage"""
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(f"{citation_title[:50]}.pdf")
        blob_name = f"{user_id}/citations/{current_time}_{unique_id}_{safe_filename}"
        
        pdf_file.seek(0)
        text_content = self._extract_text_from_pdf(pdf_file)

        # Upload text content as a separate blob
        text_blob_name = f"{blob_name}.txt"
        text_blob_client = self.container_client.get_blob_client(text_blob_name)
        text_blob_client.upload_blob(
            io.BytesIO(text_content.encode('utf-8')),
            content_settings=ContentSettings(content_type='text/plain'),
            overwrite=True
        )

        # Get the URL for the PDF blob
        blob_url = text_blob_client.url

        logger.info(f"Cited document uploaded to Azure: {blob_name}")
        return blob_name, blob_url
    
    
    def _extract_text_from_pdf(self, file):
        """Extract text from a PDF file"""
        try:
            # Read the file into memory
            file.seek(0)
            pdf_data = file.read()
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=BytesIO(pdf_data), filetype="pdf")
            text_content = ""
            
            # Extract text from each page
            for page in pdf_document:
                text_content += page.get_text("text") + "\n"
            
            pdf_document.close()
            
            # Validate extracted text
            if not text_content.strip():
                logger.warning("No text extracted from PDF")
                return ""
            
            logger.info(f"Extracted {len(text_content)} characters from PDF")
            return text_content
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""

    # def search_documents(self, query, user_id, document_id=None, top=5):
    #     """Search documents using simple text matching in Azure Blob Storage"""
    #     results = []

    #     try:
    #         # List blobs in the user's directory
    #         prefix = f"{user_id}/"

    #         if document_id:
    #             # If document_id is specified, only search that document
    #             text_blob_name = f"{document_id}.txt"
    #             blob_client = self.container_client.get_blob_client(
    #                 prefix + text_blob_name)

    #             # Check if the blob exists
    #             try:
    #                 download_stream = blob_client.download_blob()
    #                 text_content = download_stream.readall().decode('latin-1')
    #                 logger.debug(f"Text content: {text_content[:100]}")

    #                 # Get the original blob name (without .txt)
    #                 blob_name = text_blob_name[:-4]
    #                 original_blob_client = self.container_client.get_blob_client(
    #                     blob_name)

    #                 results.append({
    #                     "id":
    #                     f"{document_id}_chunk_0",
    #                     "blob_url":
    #                     original_blob_client.url,
    #                     "filename":
    #                     blob_name.split('/')[-1],
    #                     "title":
    #                     blob_name.split('/')[-1],
    #                     "user_id":
    #                     str(user_id),
    #                     "content":
    #                     self._get_context_around_query(text_content, query),
    #                     "document_id":
    #                     document_id
    #                 })
    #             except Exception as e:
    #                 logger.error(
    #                     f"Error downloading blob {text_blob_name}: {e}")
    #         else:
    #             # Search all text blobs for the user
    #             text_blobs = list(
    #                 self.container_client.list_blobs(name_starts_with=prefix))
    #             text_blobs = [
    #                 blob for blob in text_blobs if blob.name.endswith('.txt')
    #             ]

    #             # Limit to top N files
    #             for text_blob in text_blobs[:top]:
    #                 try:
    #                     blob_client = self.container_client.get_blob_client(
    #                         text_blob.name)
    #                     download_stream = blob_client.download_blob()
    #                     text_content = download_stream.readall().decode(
    #                         'utf-8')

    #                     # Get the original blob name (without .txt)
    #                     blob_name = text_blob.name[:-4]
    #                     original_blob_client = self.container_client.get_blob_client(
    #                         blob_name)

    #                     results.append({
    #                         "id":
    #                         f"{blob_name}_chunk_0",
    #                         "blob_url":
    #                         original_blob_client.url,
    #                         "filename":
    #                         blob_name.split('/')[-1],
    #                         "title":
    #                         blob_name.split('/')[-1],
    #                         "user_id":
    #                         str(user_id),
    #                         "content":
    #                         self._get_context_around_query(
    #                             text_content, query),
    #                         "document_id":
    #                         blob_name
    #                     })
    #                 except Exception as e:
    #                     logger.error(
    #                         f"Error processing blob {text_blob.name}: {e}")

    #     except Exception as e:
    #         logger.error(f"Azure search error: {e}")
    #     print(results)
    #     return results

    def search_documents(self, query, user_id, document_id=None, top=5):
        """Search documents and their citations using simple text matching in Azure Blob Storage"""
        results = []

        try:
            # List blobs in the user's directory
            prefix = f"{user_id}/"

            if document_id:
                # If document_id is specified, search the primary document and its citations
                document = Document.query.get(document_id)
                text_blob_name = f"{document.blob_url.split('/')[-1]}.txt"
                blob_client = self.container_client.get_blob_client(prefix + text_blob_name)

                # Retrieve primary document content
                try:
                    download_stream = blob_client.download_blob()
                    text_content = download_stream.readall().decode('latin-1')
                    # Get the original blob name (without .txt)
                    blob_name = text_blob_name[:-4]
                    original_blob_client = self.container_client.get_blob_client(blob_name)

                    results.append({
                        "id": f"{document_id}_chunk_0",
                        "blob_url": original_blob_client.url,
                        "filename": blob_name.split('/')[-1],
                        "title": blob_name.split('/')[-1],
                        "user_id": str(user_id),
                        "content": self._get_context_around_query(text_content, query),
                        "document_id": document_id,
                        "is_citation": False
                    })
                except Exception as e:
                    logger.error(f"Error downloading primary blob {text_blob_name}: {e}")

                # Retrieve cited documents from the database
                cited_documents = Document.query.filter_by(parent_document_id=document_id, user_id=user_id).all()
                print(cited_documents)
                for cited_doc in cited_documents[:top]:
                    try:
                        cited_blob_name = f"{cited_doc.filename}.txt"
                        cited_blob_client = self.container_client.get_blob_client(cited_blob_name)
                        download_stream = cited_blob_client.download_blob()
                        cited_text_content = download_stream.readall().decode('latin-1')

                        # Get the original blob name for the cited document
                        cited_original_blob_name = cited_blob_name[:-4]
                        cited_original_blob_client = self.container_client.get_blob_client(cited_original_blob_name)

                        results.append({
                            "id": f"{cited_doc.filename}_chunk_0",
                            "blob_url": cited_original_blob_client.url,
                            "filename": cited_original_blob_name.split('/')[-1],
                            "title": cited_doc.title,
                            "user_id": str(user_id),
                            "content": self._get_context_around_query(cited_text_content, query),
                            "document_id": cited_doc.filename,
                            "is_citation": True
                        })
                    except Exception as e:
                        logger.error(f"Error downloading cited blob {cited_blob_name}: {e}")
            else:
                # Search all text blobs for the user, including citations
                text_blobs = list(self.container_client.list_blobs(name_starts_with=prefix))
                text_blobs = [blob for blob in text_blobs if blob.name.endswith('.txt')]

                # Get all documents for the user to check for citations
                user_documents = Document.query.filter_by(user_id=user_id).all()
                document_map = {doc.filename: doc for doc in user_documents}

                # Limit to top N files
                for text_blob in text_blobs[:top]:
                    try:
                        blob_client = self.container_client.get_blob_client(text_blob.name)
                        download_stream = blob_client.download_blob()
                        text_content = download_stream.readall().decode('utf-8')

                        # Get the original blob name (without .txt)
                        blob_name = text_blob.name[:-4]
                        original_blob_client = self.container_client.get_blob_client(blob_name)

                        # Check if this is a cited document
                        is_citation = document_map.get(blob_name, Document()).parent_document_id is not None

                        results.append({
                            "id": f"{blob_name}_chunk_0",
                            "blob_url": original_blob_client.url,
                            "filename": blob_name.split('/')[-1],
                            "title": document_map.get(blob_name, Document()).title or blob_name.split('/')[-1],
                            "user_id": str(user_id),
                            "content": self._get_context_around_query(text_content, query),
                            "document_id": blob_name,
                            "is_citation": is_citation
                        })
                    except Exception as e:
                        logger.error(f"Error processing blob {text_blob.name}: {e}")

        except Exception as e:
            logger.error(f"Azure search error: {e}")
        logger.info(f"Search results: {len(results)} documents found")
        return results


    def _get_context_around_query(self, content, query, context_size=500):
        """Get text context around the search query"""
        lower_content = content.lower()
        lower_query = query.lower()

        # If query not found, return beginning of content
        return content

    def delete_document(self, blob_name, user_id):
        """Delete a document from Azure Blob Storage"""
        try:
            # Ensure the blob belongs to this user
            if not blob_name.startswith(f"{user_id}/"):
                current_app.logger.warning(
                    f"Unauthorized attempt to delete blob {blob_name} by user {user_id}"
                )
                return False

            # Delete the PDF blob
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()

            # Delete the text blob
            text_blob_name = f"{blob_name}.txt"
            text_blob_client = self.container_client.get_blob_client(
                text_blob_name)
            text_blob_client.delete_blob()

            current_app.logger.info(
                f"Document {blob_name} deleted for user {user_id}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting blob {blob_name}: {e}")
            return False
