import os
from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Document, ChatSession, ChatMessage
from document_manager import DocumentManager
from rag_system import RAGSystem

# Initialize document manager and RAG system
document_manager = DocumentManager()
rag_system = RAGSystem()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's documents
    documents = Document.query.filter_by(user_id=current_user.id).filter(Document.parent_document_id.is_(None)).order_by(Document.uploaded_at.desc()).all()
    
    # Get user's chat sessions
    chat_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                          documents=documents, 
                          chat_sessions=chat_sessions)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    if request.method == 'POST':
        # Check if file part exists
        if 'document' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['document']
        title = request.form.get('title', file.filename)
        
        # If user does not select file, browser submits an empty file
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Check if it's a PDF file
        if file and file.filename.lower().endswith('.pdf'):
            try:
                # Upload to Azure Blob Storage
                blob_name, blob_url, citation_docs = document_manager.upload_document(
                    file=file,
                    title=title,
                    user_id=current_user.id, 
                    rag_system= rag_system
                )
                
                # Save document info to database
                new_document = Document(
                    title=title,
                    filename=secure_filename(file.filename),
                    blob_url=blob_url,
                    user_id=current_user.id,
                    parent_document_id=None
                )
                db.session.add(new_document)
                db.session.flush()

                for citation_doc in citation_docs:
                    citation_doc.parent_document_id = new_document.id

                db.session.commit()
                
                app.logger.info(f"Document stored in database with ID: {new_document.id}")
                flash('Document uploaded successfully to Azure Blob Storage!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                app.logger.error(f"Upload error: {str(e)}")
                flash(f'Error uploading document: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Only PDF files are allowed', 'warning')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/document/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if user owns the document
    if document.user_id != current_user.id:
        abort(403)
    
    try:
        # Delete from Azure Blob Storage and Azure AI Search
        document_manager.delete_document(
            blob_name=document.blob_url.split('/')[-1],
            user_id=current_user.id
        )
        
        # Delete associated chat sessions
        chat_sessions = ChatSession.query.filter_by(document_id=document.id).all()
        for session in chat_sessions:
            db.session.delete(session)
        
        # Delete document from database
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        flash(f'Error deleting document: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/chat/new/<int:document_id>', methods=['GET', 'POST'])
@login_required
def new_chat_session(document_id):
    # Check if document exists and belongs to user
    document = Document.query.get_or_404(document_id)
    if document.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title', f"Chat about {document.title}")
        
        # Create new chat session
        new_session = ChatSession(
            title=title,
            user_id=current_user.id,
            document_id=document_id
        )
        db.session.add(new_session)
        db.session.commit()
        
        return redirect(url_for('chat', session_id=new_session.id))
    
    return render_template('new_chat.html', document=document)

@app.route('/chat/<int:session_id>')
@login_required
def chat(session_id):
    # Check if chat session exists and belongs to user
    chat_session = ChatSession.query.get_or_404(session_id)
    if chat_session.user_id != current_user.id:
        abort(403)
    
    # Get document associated with chat
    document = Document.query.get(chat_session.document_id)
    
    # Get messages in this chat session
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat.html', 
                          session=chat_session, 
                          document=document, 
                          messages=messages)

@app.route('/chat/<int:session_id>/send', methods=['POST'])
@login_required
def send_message(session_id):
    # Check if chat session exists and belongs to user
    chat_session = ChatSession.query.get_or_404(session_id)
    if chat_session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Save user message to database
    user_msg = ChatMessage(
        content=user_message,
        is_user=True,
        session_id=session_id
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # # Get response from RAG system
    # document = Document.query.get(chat_session.document_id)
    
    # # Convert blob URL to document ID format expected by document_manager
    # document_id = document.blob_url.split('/')[-1]
    
    rag_response = rag_system.get_answer(
        query=user_message,
        user_id=current_user.id,
        document_id=chat_session.document_id
    )
    
    # Save AI response to database
    ai_msg = ChatMessage(
        content=rag_response,
        is_user=False,
        session_id=session_id
    )
    db.session.add(ai_msg)
    db.session.commit()
    
    return jsonify({
        'user_message': {
            'id': user_msg.id,
            'content': user_msg.content,
            'timestamp': user_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        },
        'ai_response': {
            'id': ai_msg.id,
            'content': ai_msg.content,
            'timestamp': ai_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/chat/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_chat_session(session_id):
    # Check if chat session exists and belongs to user
    chat_session = ChatSession.query.get_or_404(session_id)
    if chat_session.user_id != current_user.id:
        abort(403)
    
    try:
        # Delete chat session and all associated messages
        db.session.delete(chat_session)
        db.session.commit()
        flash('Chat session deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Delete chat error: {str(e)}")
        flash(f'Error deleting chat session: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))
