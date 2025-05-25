#!/usr/bin/env python3
# setup_semantic_search.py - Complete standalone semantic search setup with .env support
# Usage: python setup_semantic_search.py

import os
import sys
import json
from typing import Dict, List, Any

def load_env_file():
    """Load environment variables from .env file"""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(f"⚠️ {env_file} file not found in current directory")
        return False
    
    print(f"📁 Loading environment variables from {env_file}")
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key.strip()] = value
                    
                    # Don't print API keys for security
                    if 'API_KEY' in key.upper() or 'SECRET' in key.upper():
                        print(f"   ✅ Loaded {key}")
                    else:
                        print(f"   ✅ Loaded {key}={value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 WEAVIATE SEMANTIC SEARCH SETUP")
    print("=" * 60)
    print()
    
    try:
        # Step 0: Load .env file
        load_env_file()
        
        # Step 1: Check requirements
        if not check_requirements():
            return False
        
        # Step 2: Connect to Weaviate
        client = connect_to_weaviate()
        if not client:
            return False
        
        # Step 3: Check current setup
        if not check_current_setup(client):
            return False
        
        # Step 4: Setup semantic search
        if setup_semantic_search(client):
            print()
            print("🎉 SEMANTIC SEARCH SETUP COMPLETE!")
            print("Your legal documents now support semantic search!")
            print()
            print("Next steps:")
            print("1. Restart your Streamlit app")
            print("2. Try asking: 'What are business formation requirements?'")
            print("3. Enjoy semantic similarity matching!")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_requirements():
    """Check if all requirements are met"""
    print("📦 Checking requirements...")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OpenAI API key not found")
        print()
        print("💡 Solutions:")
        print("1. Check your .env file contains: OPENAI_API_KEY=your-key-here")
        print("2. Or set it manually: set OPENAI_API_KEY=your-key-here")
        print("3. Make sure .env file is in the same directory as this script")
        print()
        
        # Try to show what's in the .env file (without showing sensitive values)
        if os.path.exists(".env"):
            print("📄 Current .env file contents:")
            try:
                with open(".env", 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key = line.split('=')[0]
                                print(f"   {key}=...")
                            else:
                                print(f"   {line}")
            except Exception as e:
                print(f"   Error reading .env: {e}")
        else:
            print("📄 No .env file found in current directory")
        
        return False
    
    print("✅ OpenAI API key found")
    
    # Check imports
    try:
        from market_reports.rag_enhanced import get_weaviate_client
        print("✅ Weaviate client import successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct project directory")
        return False

def connect_to_weaviate():
    """Connect to Weaviate"""
    print("\n🔗 Connecting to Weaviate...")
    
    try:
        from market_reports.rag_enhanced import get_weaviate_client
        client = get_weaviate_client()
        
        if not client:
            print("❌ Could not connect to Weaviate")
            print("💡 Make sure Weaviate is running on http://localhost:8080")
            return None
        
        # Test connection
        is_ready = client.is_ready()
        if not is_ready:
            print("❌ Weaviate is not ready")
            return None
        
        print("✅ Connected to Weaviate successfully")
        return client
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def check_current_setup(client):
    """Check current Weaviate setup"""
    print("\n📋 Checking current setup...")
    
    try:
        # Get schema
        schema = client.schema.get()
        classes = schema.get("classes", [])
        
        # Find LegalDocument class
        legal_class = None
        for cls in classes:
            if cls["class"] == "LegalDocument":
                legal_class = cls
                break
        
        if not legal_class:
            print("❌ LegalDocument class not found")
            print("💡 Make sure your legal documents are loaded in Weaviate")
            return False
        
        print("✅ Found LegalDocument class")
        
        # Check document count
        try:
            count_result = client.query.aggregate("LegalDocument").with_meta_count().do()
            if count_result and "data" in count_result:
                agg_data = count_result["data"]["Aggregate"].get("LegalDocument", [])
                if agg_data and "meta" in agg_data[0]:
                    doc_count = agg_data[0]["meta"]["count"]
                    print(f"✅ Found {doc_count:,} legal documents")
                    
                    if doc_count == 0:
                        print("⚠️ No documents found - semantic search will be empty")
                        return False
        except Exception as e:
            print(f"⚠️ Could not count documents: {e}")
        
        # Check current vectorizer
        current_vectorizer = legal_class.get("vectorizer", "none")
        print(f"📊 Current vectorizer: {current_vectorizer}")
        
        if current_vectorizer == "text2vec-openai":
            print("✅ Semantic search already configured!")
            return test_semantic_search(client)
        elif current_vectorizer == "none":
            print("⚠️ No vectorizer configured - need to set up semantic search")
            return True
        else:
            print(f"⚠️ Different vectorizer configured: {current_vectorizer}")
            print("💡 Will attempt to update to text2vec-openai")
            return True
        
    except Exception as e:
        print(f"❌ Error checking setup: {e}")
        return False

def setup_semantic_search(client):
    """Set up semantic search"""
    print("\n🔧 Setting up semantic search...")
    
    try:
        # Get current schema
        schema = client.schema.get()
        legal_class = None
        
        for cls in schema.get("classes", []):
            if cls["class"] == "LegalDocument":
                legal_class = cls
                break
        
        current_vectorizer = legal_class.get("vectorizer", "none")
        
        if current_vectorizer == "text2vec-openai":
            print("✅ Semantic search already configured")
            return test_semantic_search(client)
        
        print("🔄 Updating LegalDocument class with semantic search...")
        
        # Method 1: Try to update existing class
        try:
            print("   Attempting to add vectorizer to existing class...")
            
            # Create updated class definition
            updated_class = {
                "class": "LegalDocument",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                }
            }
            
            # Try to update the class
            client.schema.update_config("LegalDocument", updated_class)
            print("   ✅ Successfully updated class with vectorizer")
            
            # Wait for vectorization to complete
            print("   ⏳ Waiting for vectorization to complete...")
            import time
            time.sleep(5)
            
            return test_semantic_search(client)
            
        except Exception as update_error:
            print(f"   ❌ Could not update existing class: {update_error}")
            print("   💡 This is normal - Weaviate often requires class recreation")
            
            # Method 2: Recreate class (safer but requires data backup)
            return recreate_class_with_vectorizer(client)
    
    except Exception as e:
        print(f"❌ Error setting up semantic search: {e}")
        return False

def recreate_class_with_vectorizer(client):
    """Recreate the class with vectorizer (backup and restore data)"""
    print("🔄 Recreating class with semantic search...")
    
    try:
        # User confirmation
        print("⚠️ WARNING: This will temporarily delete and recreate your LegalDocument class")
        print("   Your documents will be backed up and restored, but this is a significant operation.")
        print()
        response = input("Continue? (y/N): ").strip().lower()
        
        if response != 'y' and response != 'yes':
            print("❌ Operation cancelled by user")
            return False
        
        # Step 1: Backup data
        print("   📦 Backing up existing documents...")
        
        backup_data = []
        
        # Get all documents
        try:
            all_props = [
                "content", "documentTitle", "documentType", "filename", 
                "pageNumber", "chunkIndex", "section", "jurisdiction", 
                "practiceArea", "processingDate", "totalPages", "wordCount", 
                "fileSize", "filePath", "summary", "keyTerms"
            ]
            
            result = (
                client.query
                .get("LegalDocument", all_props)
                .with_limit(2000)  # Adjust if you have more documents
                .do()
            )
            
            if result and "data" in result and "Get" in result["data"]:
                backup_data = result["data"]["Get"].get("LegalDocument", [])
                print(f"   ✅ Backed up {len(backup_data)} documents")
            else:
                print("   ⚠️ No documents found to backup")
                
        except Exception as backup_error:
            print(f"   ❌ Backup failed: {backup_error}")
            print("   💡 Proceeding without backup - data may be lost")
        
        # Step 2: Delete existing class
        print("   🗑️ Deleting existing class...")
        client.schema.delete_class("LegalDocument")
        print("   ✅ Class deleted")
        
        # Step 3: Create new class with vectorizer
        print("   🆕 Creating new class with semantic search...")
        
        new_class = {
            "class": "LegalDocument",
            "description": "Legal documents with semantic search",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {"name": "content", "dataType": ["text"], "description": "Document content"},
                {"name": "documentTitle", "dataType": ["string"], "description": "Document title"},
                {"name": "documentType", "dataType": ["string"], "description": "Document type"},
                {"name": "filename", "dataType": ["string"], "description": "Filename"},
                {"name": "pageNumber", "dataType": ["int"], "description": "Page number"},
                {"name": "chunkIndex", "dataType": ["int"], "description": "Chunk index"},
                {"name": "section", "dataType": ["string"], "description": "Document section"},
                {"name": "jurisdiction", "dataType": ["string"], "description": "Jurisdiction"},
                {"name": "practiceArea", "dataType": ["string"], "description": "Practice area"},
                {"name": "processingDate", "dataType": ["string"], "description": "Processing date"},
                {"name": "totalPages", "dataType": ["int"], "description": "Total pages"},
                {"name": "wordCount", "dataType": ["int"], "description": "Word count"},
                {"name": "fileSize", "dataType": ["int"], "description": "File size"},
                {"name": "filePath", "dataType": ["string"], "description": "File path"},
                {"name": "summary", "dataType": ["text"], "description": "Summary"},
                {"name": "keyTerms", "dataType": ["string[]"], "description": "Key terms"}
            ]
        }
        
        client.schema.create_class(new_class)
        print("   ✅ New class created with semantic search")
        
        # Step 4: Restore data
        if backup_data:
            print(f"   📤 Restoring {len(backup_data)} documents...")
            
            with client.batch as batch:
                batch.batch_size = 50
                
                for doc in backup_data:
                    # Clean document (remove any Weaviate metadata)
                    clean_doc = {k: v for k, v in doc.items() if not k.startswith("_")}
                    
                    batch.add_data_object(
                        data_object=clean_doc,
                        class_name="LegalDocument"
                    )
            
            print("   ✅ Documents restored with vector embeddings")
        else:
            print("   ⚠️ No data to restore")
        
        # Step 5: Wait for vectorization
        print("   ⏳ Waiting for OpenAI vectorization to complete...")
        import time
        time.sleep(10)  # Give time for OpenAI to vectorize the documents
        
        # Step 6: Test semantic search
        print("   🧪 Testing semantic search...")
        return test_semantic_search(client)
        
    except Exception as e:
        print(f"   ❌ Error recreating class: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_semantic_search(client):
    """Test semantic search functionality"""
    print("\n🧪 Testing semantic search...")
    
    try:
        # Test nearText search
        result = (
            client.query
            .get("LegalDocument", ["content", "documentTitle", "documentType"])
            .with_near_text({"concepts": ["business formation Saudi Arabia"]})
            .with_limit(3)
            .do()
        )
        
        if result and "data" in result and "Get" in result["data"]:
            docs = result["data"]["Get"].get("LegalDocument", [])
            
            if docs:
                print(f"✅ Semantic search working! Found {len(docs)} relevant documents")
                
                for i, doc in enumerate(docs, 1):
                    title = doc.get("documentTitle", "No title")[:50]
                    doc_type = doc.get("documentType", "Unknown")
                    print(f"   {i}. {title}... (Type: {doc_type})")
                
                return True
            else:
                print("❌ Semantic search returned no results")
                return False
        else:
            print("❌ Semantic search query failed")
            return False
            
    except Exception as e:
        print(f"❌ Semantic search test error: {e}")
        
        # Try to understand the error
        if "nearText" in str(e):
            print("💡 nearText not available - vectorizer might not be properly configured")
        elif "concepts" in str(e):
            print("💡 Query format issue - check Weaviate version compatibility")
        
        return False

if __name__ == "__main__":
    print("Starting semantic search setup...")
    success = main()
    
    if success:
        print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("Restart your Streamlit app to use semantic search.")
    else:
        print("\n❌ Setup failed. Check the errors above.")
        print("You can still use keyword-based search.")
    
    print("\nPress Enter to exit...")
    input()