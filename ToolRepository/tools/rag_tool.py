import os
import chromadb # Native ChromaDB client
from langchain_openai import OpenAIEmbeddings # For embedding the query
from agents import tool
from typing import List, Dict, Any
import json # For potentially serializing results if complex

@tool()
async def query_rag_context(collection_name: str, question: str, k: int = 3) -> List[Dict[str, Any]]:
    """Query a specified ChromaDB collection using the native client and return the top-k most relevant document chunks.

    Args:
        collection_name: The name of the ChromaDB collection to query.
        question: The question/query to find relevant documents for.
        k: The number of top relevant document chunks to return (default is 3).

    Returns:
        A list of dictionaries, where each dictionary contains 'document' (text chunk), 'metadata',
        and 'distance' of a relevant document chunk. Returns an empty list or list with error if issues occur.
    """
    try:
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set (needed for query embedding).")
            return [{"error": "OPENAI_API_KEY not set."}]

        persist_directory_base = "./chroma_db_collections"  # Must match ingestion base path
        collection_persist_path = os.path.join(persist_directory_base, collection_name)

        if not os.path.exists(collection_persist_path):
            return [{"error": f"ChromaDB collection '{collection_name}' persistence directory not found at '{collection_persist_path}'. Ensure documents were ingested first."}]

        # Initialize Chroma Persistent Client pointing to the specific collection's persisted path
        client = chromadb.PersistentClient(path=collection_persist_path)
        
        try:
            collection = client.get_collection(name=collection_name)
        except ValueError as ve:
            # This can happen if the collection doesn't exist in the client's path
            print(f"Error getting collection '{collection_name}': {ve}")
            return [{"error": f"Could not get ChromaDB collection '{collection_name}'. It might not exist at the path or there was an issue initializing it."}]
        except Exception as e_coll:
            print(f"Unexpected error getting collection '{collection_name}': {e_coll}")
            return [{"error": f"Unexpected error accessing collection '{collection_name}': {str(e_coll)}"}]

        # Embed the query text using the same method as ingestion
        # (Assuming OpenAIEmbeddings was used, if Chroma used its own, this needs alignment)
        embedding_function = OpenAIEmbeddings()
        query_embedding = embedding_function.embed_query(question)

        print(f"Querying native ChromaDB collection '{collection_name}' for: '{question}' with k={k}")
        
        results = collection.query(
            query_embeddings=[query_embedding], # Native client uses query_embeddings
            n_results=k,
            include=["documents", "metadatas", "distances"]  # Specify what to include
        )
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return [] # Return empty list if no documents found

        # Reformat results into a list of dictionaries as expected by the previous tool version
        # The native client returns results['documents'], results['metadatas'], results['ids'], results['distances'] as lists of lists.
        # Each inner list corresponds to a query_embedding (we only have one).
        formatted_results = []
        num_results = len(results['ids'][0])
        for i in range(num_results):
            formatted_results.append({
                "document": results['documents'][0][i] if results['documents'] and results['documents'][0] else None,
                "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else None,
                "id": results['ids'][0][i] # Include the chunk ID as well
            })
        
        return formatted_results

    except ImportError as ie:
        print(f"RAG Tool Import Error: {ie}")
        return [{"error": f"A required library for RAG is not installed: {ie}. Check chromadb, langchain_openai."}]
    except Exception as e:
        print(f"RAG Tool Error: {e}")
        import traceback
        traceback.print_exc() # For more detailed error logging during development
        return [{"error": f"RAG error for collection '{collection_name}' with question '{question}': {str(e)}"}] 