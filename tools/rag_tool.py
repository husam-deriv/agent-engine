# rag_corpus_ingestion_native_chroma.py
# (This code is for your friend - it's not directly integrated into the agent tools yet)

import os
import chromadb # Native ChromaDB client
from langchain_openai import OpenAIEmbeddings # Still use LangChain for embeddings if preferred
import json
import certifi
from agents import function_tool


@function_tool
def rag_collection_query(collection_name: str, user_query: str):
    """Access and retrieve information from vector database collections, enabling an AI Agent to perform semantic search across previously embedded document collections and return the most relevant results to supplement its knowledge or answer domain-specific questions; Args: collection_name (str): name of the collection to query, user_query (str): the search query; Returns: dict: query results containing matched documents, metadata, and relevance scores."""
    
    base_persist_dir = "backend/my_chroma_data_multisource"
    
    # --- Example Usage: ---
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable.")
        print("And ensure 'docling' is installed: pip install docling")
    else:
        # --- Setup for example ---
        sample_base_file_path = "backend/rag_files_sample" # Example base path
        os.makedirs(sample_base_file_path, exist_ok=True)
        
        # Strip file extension if it exists in collection name
        if "." in collection_name:
            collection_name_for_sample = os.path.splitext(collection_name)[0]
        else:
            collection_name_for_sample = collection_name
       
    # --- Test Querying directly with native chromadb client ---
    print("\nTesting direct query to the collection...")
    try:
        client = chromadb.PersistentClient(path=base_persist_dir)
        # Ensure the collection exists before trying to get it
        if collection_name_for_sample not in [c.name for c in client.list_collections()]:
            # Try with or without file extension
            if "." in collection_name:
                # Try without extension
                collection_name_without_ext = os.path.splitext(collection_name)[0]
                if collection_name_without_ext in [c.name for c in client.list_collections()]:
                    collection_name_for_sample = collection_name_without_ext
                else:
                    print(f"Collection {collection_name} not found. Skipping query test.")
                    return {"error": f"Collection {collection_name} not found"}
            else:
                print(f"Collection {collection_name_for_sample} not found. Skipping query test.")
                return {"error": f"Collection {collection_name_for_sample} not found"}
        
        collection_to_query = client.get_collection(name=collection_name_for_sample)
        
        query_text = user_query
        lc_embedder = OpenAIEmbeddings(model="text-embedding-3-large")
        query_embedding = lc_embedder.embed_query(query_text)

        results = collection_to_query.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=['documents', 'metadatas', 'distances'] 
        )
        print("\nDirect Chroma Query Results:")
        print(json.dumps(results, indent=2))

        return results
        
    except Exception as e:
        print(f"Error during direct query test: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

    print(certifi.where())