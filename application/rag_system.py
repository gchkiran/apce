import os
import logging
from document_manager import DocumentManager
from flask import current_app

# Import langchain components
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

class RAGSystem:
    def __init__(self):
        self.document_manager = DocumentManager()
        
        # Initialize Groq LLM
        self.llm = None
        try:
            # Check if GROQ_API_KEY is available
            if os.environ.get("GROQ_API_KEY"):
                logger.info("Initializing GROQ LLM...")
                self.llm = ChatGroq(
                    api_key=os.environ.get("GROQ_API_KEY"),
                    model_name=
                    "meta-llama/llama-4-scout-17b-16e-instruct"
                )
                logger.info("GROQ LLM initialized successfully")
            else:
                logger.warning(
                    "GROQ_API_KEY not found in environment variables")
        except Exception as e:
            logger.error(f"Error initializing GROQ LLM: {str(e)}")
    
    def get_answer(self, query, user_id, document_id=None):
        """
        Get an answer to a query using a Retrieval-Augmented Generation approach
        
        Args:
            query (str): The user's question
            user_id (int): The user ID for document filtering
            document_id (str, optional): Specific document ID if the query is for a particular document
            
        Returns:
            str: The generated answer
        """
        try:
            # Search for relevant documents
            search_results = self.document_manager.search_documents(
                query=query,
                user_id=user_id,
                document_id=document_id,
                top=3
            )
            
            if not search_results:
                return "I couldn't find any relevant information in your documents to answer this question."
            
            # Separate primary document and cited papers
            primary_content = ""
            cited_contents = []
            for result in search_results:
                if not result.get("is_citation", False):
                    primary_content = result["content"]  # Full text for primary document
                else:
                    cited_contents.append({
                        "title": result["title"],
                        "content": result["content"]  # Query-relevant excerpt
                    })
            
            # Combine context: primary document (full) + cited papers (relevant)
            context_parts = [f"Primary Document:\n{primary_content}"]
            for cited in cited_contents:
                context_parts.append(f"Cited Paper ({cited['title']}):\n{cited['content']}")
            context = "\n\n".join(context_parts)
            
            # Check if LLM is available
            if self.llm:
                current_app.logger.info("Using GROQ LLM for RAG response")
                return self._generate_llm_response(query, context, primary_content, cited_contents)
            else:
                # Fall back to simple response if LLM isn't available
                current_app.logger.warning("Falling back to simple response - GROQ LLM not available")
                return self._generate_simple_response(query, context)
        
        except Exception as e:
            current_app.logger.error(f"Error in get_answer: {str(e)}")
            return f"I encountered an error while trying to answer your question: {str(e)}"
    
    def _generate_llm_response(self, query, context, primary_content, cited_contents):
        """
        Generate a response using the GROQ LLM with provided context, prioritizing the primary document.
        
        Args:
            query (str): The user's question
            context (str): Combined context (primary + cited papers)
            primary_content (str): Full text of the primary document
            cited_contents (list): List of cited papers with titles and relevant content
        """
        try:
            # Estimate token count (1 token ≈ 4 characters)
            def estimate_tokens(text):
                return len(text) // 4 + 1

            # Define token limits
            MAX_TOKENS = 30000
            RESERVED_TOKENS = 1500  # For prompt, query, and response
            MAX_CONTEXT_TOKENS = MAX_TOKENS - RESERVED_TOKENS

            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=20000,  # ~5,000 tokens, smaller to fit primary + cited
                chunk_overlap=500
            )

            # Check context size
            context_tokens = estimate_tokens(context)
            if context_tokens > MAX_CONTEXT_TOKENS:
                current_app.logger.info(f"Context exceeds {MAX_CONTEXT_TOKENS} tokens: {context_tokens}")
                
                # Prioritize primary document
                primary_tokens = estimate_tokens(primary_content)
                if primary_tokens >= MAX_CONTEXT_TOKENS:
                    # Split primary document if too large
                    primary_chunks = text_splitter.split_text(primary_content)
                    primary_content = primary_chunks[0]  # Take first chunk
                    current_app.logger.info("Truncated primary document to first chunk")
                    cited_contents = []  # No room for cited papers
                else:
                    # Fit primary document, trim cited papers
                    remaining_tokens = MAX_CONTEXT_TOKENS - primary_tokens
                    
                    # Rank cited papers by relevance
                    def score_chunk(chunk, query):
                        score = 0
                        query_words = re.findall(r'\w+', query.lower())
                        chunk_lower = chunk.lower()
                        for word in query_words:
                            if word in chunk_lower:
                                score += chunk_lower.count(word)
                        return score

                    ranked_cited = []
                    for cited in cited_contents:
                        score = score_chunk(cited["content"], query)
                        ranked_cited.append((cited, score))
                    ranked_cited.sort(key=lambda x: x[1], reverse=True)

                    # Select cited content to fit remaining tokens
                    selected_cited = []
                    total_cited_tokens = 0
                    for cited, _ in ranked_cited:
                        cited_tokens = estimate_tokens(cited["content"])
                        if total_cited_tokens + cited_tokens <= remaining_tokens:
                            selected_cited.append(cited)
                            total_cited_tokens += cited_tokens
                        else:
                            break

                    # Rebuild context
                    context_parts = [f"Primary Document:\n{primary_content}"]
                    for cited in selected_cited:
                        context_parts.append(f"Cited Paper ({cited['title']}):\n{cited['content']}")
                    context = "\n\n".join(context_parts)
                
                current_app.logger.info(f"Final context tokens: {estimate_tokens(context)}")

            # Create prompt template
            prompt = ChatPromptTemplate.from_template("""
                You are a renowned professor with decades of experience in academic research, skilled at explaining complex concepts to non-experts. Your task is to answer the user's question based primarily on the full text of the primary research paper provided in the context, supplemented by relevant excerpts from cited papers. The primary document is the main source of information, while cited papers provide supporting details, especially for questions about how the current paper builds on past work.

                CONTEXT:
                {context}

                USER QUESTION:
                {query}

                When answering:
                - Base your answer primarily on the primary document, using its full text to provide comprehensive and accurate information.
                - Use the cited papers' excerpts to supplement your answer, particularly when explaining how the current paper builds on or relates to previous work.
                - Explain concepts as you would to a curious student with no prior knowledge of the field, using simple language and analogies where helpful.
                - If the question relates to contributions from past work, summarize the relevant cited papers' contributions based on the provided excerpts.
                - If the answer is not contained in the context, say: "I don't have enough information in the provided documents to answer this question."
                - Do not use external knowledge or make up information. Base your answer solely on the provided context.
                - Keep your response concise, informative, and directly related to the question.
            """)

            # Create chain
            chain = LLMChain(llm=self.llm, prompt=prompt)

            # Run the chain
            response = chain.invoke({
                "context": context,
                "query": query
            })

            current_app.logger.info("Generated response from GROQ LLM")
            return response['text']

        except Exception as e:
            current_app.logger.error(f"Error in _generate_llm_response: {str(e)}")
            return f"I encountered an error while generating a response with the LLM: {str(e)}"

    def _generate_simple_response(self, query, context):
        """
        Generate a simple response based on the context
        This is a fallback method if the LLM-based generation fails
        """
        try:
            # Log the query for debugging
            current_app.logger.info(f"Query: {query}")
            
            # Simple response based on basic context extraction
            query_lower = query.lower()
            
            # Find a sentence containing the query
            sentences = context.split('.')
            relevant_sentences = []
            
            for sentence in sentences:
                if query_lower in sentence.lower():
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return f"Here's what I found in your document:\n\n{'. '.join(relevant_sentences)}."
            
            # If no direct match found, return a generic response with the context
            return f"Based on your document, here's the relevant information:\n\n{context[:500]}..."
            
        except Exception as e:
            current_app.logger.error(f"Error generating answer: {e}")
            return "I encountered an error while trying to generate an answer. The document content is: " + context[:200] + "..."
