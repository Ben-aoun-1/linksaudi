import os
import json
import time
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Handle optional dependencies gracefully
WEAVIATE_AVAILABLE = False
try:
    import weaviate
    WEAVIATE_AVAILABLE = True
    print("Successfully imported weaviate-client")
except ImportError:
    print("Warning: weaviate-client not installed. Try: pip install weaviate-client")
    WEAVIATE_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: openai not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Get credentials from environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients only if dependencies are available
openai_client = None
embedding_model = None

# Fix: Check if OPENAI_API_KEY is actually valid (not just exists)
if OPENAI_AVAILABLE and OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI client initialized successfully")
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        openai_client = None

# Initialize fallback embedding model
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Initialized fallback embedding model: all-MiniLM-L6-v2")
    except Exception as e:
        print(f"Error initializing sentence transformer: {e}")
        embedding_model = None

class EmbeddingEngine:
    """Hybrid embedding engine with OpenAI primary and local fallback"""
    
    def __init__(self):
        self.openai_client = openai_client
        self.local_model = embedding_model
        self.cache = {}  # Simple in-memory cache
        self.use_openai = openai_client is not None
        self.embedding_model = "text-embedding-3-small"  # Default OpenAI model
        self.dimensions = 1536  # Default dimensions
        
        print(f"Embedding engine initialized:")
        print(f"  - OpenAI available: {self.use_openai}")
        print(f"  - Local fallback available: {self.local_model is not None}")
    
    def set_openai_model(self, model_name: str, dimensions: int = None):
        """Set the OpenAI embedding model to use"""
        self.embedding_model = model_name
        if dimensions:
            self.dimensions = dimensions
        print(f"Set OpenAI model to: {model_name} with {self.dimensions if dimensions else 'default'} dimensions")
    
    def encode(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        Generate embeddings for text using OpenAI or local fallback
        """
        if not text or not text.strip():
            print("Empty text provided for embedding")
            return None
            
        if use_cache and text in self.cache:
            return self.cache[text]
        
        # Try OpenAI first
        if self.use_openai:
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    dimensions=self.dimensions
                )
                embedding = response.data[0].embedding
                
                # Cache the result
                if use_cache:
                    self.cache[text] = embedding
                
                return embedding
                
            except Exception as e:
                print(f"OpenAI embedding failed: {e}")
                print("Falling back to local model...")
        
        # Fallback to local model
        if self.local_model:
            try:
                embedding = self.local_model.encode(text).tolist()
                if use_cache:
                    self.cache[text] = embedding
                return embedding
            except Exception as e:
                print(f"Local embedding failed: {e}")
                return None
        
        print("No embedding method available")
        return None
    
    def encode_batch(self, texts: List[str], batch_size: int = 100) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently
        """
        if not texts:
            return []
            
        embeddings = []
        
        # Process in batches for OpenAI
        if self.use_openai:
            try:
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    
                    # Filter out empty texts
                    filtered_batch = [text for text in batch if text and text.strip()]
                    if not filtered_batch:
                        continue
                    
                    # Check cache first
                    batch_embeddings = []
                    uncached_texts = []
                    uncached_indices = []
                    
                    for j, text in enumerate(filtered_batch):
                        if text in self.cache:
                            batch_embeddings.append(self.cache[text])
                        else:
                            batch_embeddings.append(None)
                            uncached_texts.append(text)
                            uncached_indices.append(j)
                    
                    # Get embeddings for uncached texts
                    if uncached_texts:
                        response = self.openai_client.embeddings.create(
                            model=self.embedding_model,
                            input=uncached_texts,
                            dimensions=self.dimensions
                        )
                        
                        # Fill in the uncached embeddings
                        for idx, embedding_data in enumerate(response.data):
                            original_idx = uncached_indices[idx]
                            embedding = embedding_data.embedding
                            batch_embeddings[original_idx] = embedding
                            # Cache the result
                            self.cache[uncached_texts[idx]] = embedding
                    
                    embeddings.extend(batch_embeddings)
                
                return embeddings
                
            except Exception as e:
                print(f"OpenAI batch embedding failed: {e}")
                print("Falling back to local model...")
        
        # Fallback to local model
        if self.local_model:
            try:
                # Filter out empty texts
                filtered_texts = [text for text in texts if text and text.strip()]
                if not filtered_texts:
                    return []
                    
                # Local models handle batching differently
                local_embeddings = self.local_model.encode(filtered_texts)
                return [emb.tolist() for emb in local_embeddings]
            except Exception as e:
                print(f"Local batch embedding failed: {e}")
                return None
        
        print("No embedding method available for batch processing")
        return None

# Initialize the global embedding engine
embedding_engine = EmbeddingEngine()

def get_weaviate_client():
    """Connect to Weaviate with enhanced error handling"""
    if not WEAVIATE_AVAILABLE:
        raise ImportError("Weaviate client not available. Please install with: pip install weaviate-client")
    
    if not WEAVIATE_URL or not WEAVIATE_API_KEY:
        raise ValueError("Weaviate URL and API key must be set in .env file")
    
    # Implement retry logic with exponential backoff
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Try different client initialization methods depending on version
            try:
                # Try newer client initialization
                client = weaviate.Client(
                    url=WEAVIATE_URL,
                    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
                    timeout_config=(30, 120),
                    additional_headers={
                        "X-LinkSaudi-Client": "Market-Intelligence-Platform/1.0"
                    }
                )
            except Exception:
                # Fallback to simpler client initialization
                client = weaviate.Client(
                    url=WEAVIATE_URL,
                    additional_headers={
                        "Authorization": f"Bearer {WEAVIATE_API_KEY}",
                        "X-LinkSaudi-Client": "Market-Intelligence-Platform/1.0"
                    }
                )
            
            # Test connection
            try:
                client.schema.get()
            except:
                # Try alternative connection test
                client.is_ready()
            
            return client
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = retry_delay * (2 ** attempt)
                print(f"Connection attempt {attempt+1} failed: {e}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                # Final attempt failed
                print(f"Failed to connect to Weaviate after {max_retries} attempts: {e}")
                raise ConnectionError(f"Unable to connect to Weaviate: {e}")

def basic_search(query_text: str, limit: int = 5) -> List[Dict]:
    """Simple search without vector similarity"""
    if not WEAVIATE_AVAILABLE:
        print("Weaviate not available, returning empty results")
        return []
    
    try:
        client = get_weaviate_client()
        
        # Use BM25 search instead of vector search
        query_result = (
            client.query
            .get("MarketReportText", ["content", "filename", "reportTitle", "reportDate", "section", "page"])
            .with_bm25(query=query_text)
            .with_limit(limit)
            .do()
        )
        
        results = []
        
        # Handle different response formats
        data = None
        if "data" in query_result:
            if "Get" in query_result["data"] and "MarketReportText" in query_result["data"]["Get"]:
                data = query_result["data"]["Get"]["MarketReportText"]
            elif "MarketReportText" in query_result["data"]:
                data = query_result["data"]["MarketReportText"]
        
        if data and isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    results.append({
                        "content": item.get("content", ""),
                        "filename": item.get("filename", ""),
                        "title": item.get("reportTitle", ""),
                        "date": item.get("reportDate", ""),
                        "section": item.get("section", ""),
                        "page": item.get("page", 0),
                        "type": "text"
                    })
        
        return results
    except Exception as e:
        print(f"Basic search error: {e}")
        return []

def vector_search(query_text: str, limit: int = 5) -> List[Dict]:
    """Vector-based semantic search using the hybrid embedding engine"""
    if not WEAVIATE_AVAILABLE:
        print("Weaviate not available - falling back to basic search")
        return basic_search(query_text, limit)
    
    try:
        client = get_weaviate_client()
        
        # Generate embedding using the hybrid engine
        print(f"Generating embedding for: {query_text[:50]}...")
        query_embedding = embedding_engine.encode(query_text)
        
        if not query_embedding:
            print("Failed to generate embedding - falling back to basic search")
            return basic_search(query_text, limit)
        
        print(f"Generated embedding with {len(query_embedding)} dimensions")
        
        # Execute the vector search query
        print("Executing vector search...")
        query_result = (
            client.query
            .get("MarketReportText", ["content", "filename", "reportTitle", "reportDate", "section", "page"])
            .with_near_vector({"vector": query_embedding})
            .with_limit(limit)
            .do()
        )
        
        print(f"Query result type: {type(query_result)}")
        print(f"Query result keys: {list(query_result.keys()) if query_result else 'None'}")
        
        results = []
        
        # Handle the response parsing more robustly
        if query_result and isinstance(query_result, dict):
            # Check for data key
            if "data" in query_result:
                data = query_result["data"]
                print(f"Data keys: {list(data.keys()) if data else 'None'}")
                
                # Check for Get key (v3/v4 compatibility)
                if "Get" in data and isinstance(data["Get"], dict):
                    get_data = data["Get"]
                    print(f"Get keys: {list(get_data.keys()) if get_data else 'None'}")
                    
                    # Check for MarketReportText
                    if "MarketReportText" in get_data:
                        items = get_data["MarketReportText"]
                        print(f"Found {len(items) if items else 0} items in MarketReportText")
                        
                        if items and isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    results.append({
                                        "content": item.get("content", ""),
                                        "filename": item.get("filename", ""),
                                        "title": item.get("reportTitle", ""),
                                        "date": item.get("reportDate", ""),
                                        "section": item.get("section", ""),
                                        "page": item.get("page", 0),
                                        "type": "text"
                                    })
                        else:
                            print("No items found or items is not a list")
                    else:
                        print(f"MarketReportText not found in Get. Available: {list(get_data.keys())}")
                else:
                    print("Get key not found or not a dict in data")
            else:
                print("No data key in query result")
        else:
            print("Query result is None or not a dict")
        
        print(f"Returning {len(results)} results")
        return results
        
    except Exception as e:
        print(f"Vector search error: {e}")
        import traceback
        traceback.print_exc()
        # Fall back to basic search
        return basic_search(query_text, limit)

def semantic_search(query: str, limit: int = 5) -> List[Dict]:
    """Combined search approach with hybrid embedding"""
    if not query or not query.strip():
        print("Empty query provided")
        return []
    
    # Try vector search first
    vector_results = vector_search(query, limit)
    
    # If vector search fails, fall back to basic search
    if not vector_results:
        print("Vector search returned no results, trying basic search")
        return basic_search(query, limit)
    
    return vector_results

def generate_rag_response(query: str, context_limit: int = 5) -> str:
    """Generate a RAG response using OpenAI and Weaviate"""
    
    if not openai_client:
        return "OpenAI client not available. Please check your API key and ensure the openai package is installed."
    
    # Get relevant documents from Weaviate
    search_results = semantic_search(query, limit=context_limit)
    
    if not search_results:
        return "I couldn't find relevant information to answer your question. Please try a different query or provide more context."
    
    # Format the context for the prompt
    context = "\n\n".join([f"Document {i+1}:\nTitle: {doc.get('title', 'Untitled')}\nSection: {doc.get('section', 'N/A')}\nContent: {doc.get('content', 'No content')}" 
                          for i, doc in enumerate(search_results)])
    
    # Create the prompt
    prompt = f"""
    You are an expert market analyst specializing in Saudi Arabian markets. Answer the following question based on the provided context.
    
    Question: {query}
    
    Context:
    {context}
    
    Provide a detailed, informative response based solely on the information in the context. If the context doesn't contain enough information to answer the question fully, acknowledge the limitations of the available information. Use a professional, analytical tone suitable for investment reports.
    """
    
    try:
        # Generate response using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert market analyst specializing in Saudi Arabian markets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"I encountered an error while generating a response: {str(e)}"

def generate_multimodal_rag_response(query: str, context_limit: int = 5, image_limit: int = 2) -> Dict:
    """Generate a RAG response with both text and image results"""
    
    # Get relevant text results
    text_results = semantic_search(query, context_limit)
    
    if not text_results:
        return {
            "response": "I couldn't find relevant information to answer your question. Please try a different query or provide more context.",
            "text_results": [],
            "image_results": []
        }
    
    # Format the context for the prompt
    context = "\n\n".join([f"Document {i+1}:\nTitle: {doc.get('title', 'Untitled')}\nSection: {doc.get('section', 'N/A')}\nContent: {doc.get('content', 'No content')}" 
                          for i, doc in enumerate(text_results)])
    
    # Create the prompt
    prompt = f"""
    You are an expert market analyst specializing in Saudi Arabian markets. Answer the following question based on the provided context.
    
    Question: {query}
    
    Context:
    {context}
    
    Provide a detailed, informative response based solely on the information in the context. If the context doesn't contain enough information to answer the question fully, acknowledge the limitations of the available information. Use a professional, analytical tone suitable for investment reports.
    """
    
    if not openai_client:
        return {
            "response": "OpenAI client not available. Please check your API key and ensure the openai package is installed.",
            "text_results": text_results,
            "image_results": []
        }
    
    try:
        # Generate response using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert market analyst specializing in Saudi Arabian markets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Return the response along with the retrieved results
        return {
            "response": response_text,
            "text_results": text_results,
            "image_results": []  # Image processing disabled for now
        }
    except Exception as e:
        print(f"Error generating response: {e}")
        error_message = f"I encountered an error while generating a response: {str(e)}"
        return {
            "response": error_message,
            "text_results": text_results,
            "image_results": []
        }

# Utility functions for configuration
def configure_openai_embeddings(model: str = "text-embedding-3-small", dimensions: int = 1536):
    """Configure the OpenAI embedding model and dimensions"""
    global embedding_engine
    embedding_engine.set_openai_model(model, dimensions)

def get_embedding_info():
    """Get information about the current embedding configuration"""
    return {
        "openai_available": embedding_engine.use_openai,
        "local_fallback_available": embedding_engine.local_model is not None,
        "current_model": embedding_engine.embedding_model if embedding_engine.use_openai else "Local fallback",
        "dimensions": embedding_engine.dimensions if embedding_engine.use_openai else "384 (local)",
        "cache_size": len(embedding_engine.cache)
    }

# File handling functions
def detect_file_encoding(filename: str) -> str:
    """Detect the encoding of a file"""
    try:
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
        try:
            with open(filename, 'rb') as f:
                for line in f:
                    detector.feed(line)
                    if detector.done:
                        break
                detector.close()
            
            return detector.result['encoding'] or 'utf-8'
        except Exception as e:
            print(f"Error detecting encoding: {e}")
            return 'utf-8'  # Default to UTF-8 on error
    except ImportError:
        return 'utf-8'

def read_file_with_encoding(filename: str) -> Optional[str]:
    """Read a file with automatic encoding detection"""
    try:
        # Try to detect encoding
        encoding = detect_file_encoding(filename)
        
        # Try to read with detected encoding
        try:
            with open(filename, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # If that fails, try UTF-8
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, fall back to latin-1 which should always work
                with open(filename, 'r', encoding='latin-1') as f:
                    return f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None

def write_file_with_encoding(filename: str, content: str) -> bool:
    """Write content to a file with UTF-8 encoding"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write with UTF-8 encoding
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error writing file {filename}: {e}")
        return False

if __name__ == "__main__":
    # Example usage and testing
    try:
        # Test embedding engine
        print("Testing embedding engine...")
        test_text = "Saudi Arabia technology market analysis"
        embedding = embedding_engine.encode(test_text)
        if embedding:
            print(f"Successfully generated embedding with {len(embedding)} dimensions")
        else:
            print("Failed to generate embedding")
        
        # Test configuration
        print("\nEmbedding configuration:")
        info = get_embedding_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test Weaviate connection if available
        if WEAVIATE_AVAILABLE:
            try:
                client = get_weaviate_client()
                print("Successfully connected to Weaviate!")
            except Exception as e:
                print(f"Error connecting to Weaviate: {e}")
        
    except Exception as e:
        print(f"Error during testing: {e}")