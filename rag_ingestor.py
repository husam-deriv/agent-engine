# rag_corpus_ingestion_native_chroma.py
# (This code is for your friend - it's not directly integrated into the agent tools yet)

import os
import chromadb # Native ChromaDB client
from langchain_openai import OpenAIEmbeddings # Still use LangChain for embeddings if preferred
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document # For creating Document objects if not already
import uuid # For generating unique IDs for chunks if not provided
import json
from docling.document_converter import DocumentConverter # Added import
import urllib.parse # For URL checking
import certifi

# --- Database Interaction (Placeholder - to be implemented with your SQLite setup) ---
# (Same as before)
def log_document_to_sql(doc_name, collection_name, uploader_id, description, file_path, file_size, mime_type, visibility_scope, target_group_id, target_vertical_id, target_company_id, embedding_model_name, chunk_size, chunk_overlap, status="COMPLETED"):
    print(f"[SQL LOG] Document: {doc_name}, Collection: {collection_name}, Status: {status}, File Path: {file_path}, Size: {file_size}")
    pass

def process_and_embed_documents_native_chroma(
    file_sources: list[str], # Changed from document_contents and document_ids
    collection_name: str,
    document_metadatas_override: list[dict] | None = None, # Optional: if you want to provide specific metadata per source
    embedding_model_name: str = "text-embedding-3-large", # "text-embedding-ada-002",
    chunk_size: int = 2000,
    chunk_overlap: int = 400,
    persist_directory_base: str = "./chroma_db_collections",
    base_file_path_prefix: str = "backend/rag_files/" # New parameter for local files
):
    """
    Processes documents from file sources (local paths or URLs), extracts content using DocumentConverter,
    creates embeddings using OpenAIEmbeddings, and stores them in a ChromaDB collection.
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set (needed for OpenAIEmbeddings).")
        return False
    if not file_sources:
        print("Error: file_sources list cannot be empty.")
        return False
    if document_metadatas_override and len(document_metadatas_override) != len(file_sources):
        print("Error: If document_metadatas_override is provided, it must have the same length as file_sources.")
        return False

    print(f"Initializing RAG corpus processing for collection: {collection_name} using native chromadb client.")
    converter = DocumentConverter()
    
    all_document_contents = []
    all_document_ids = []
    all_original_metadatas = [] # To store metadata for each original document

    print("Processing file sources...")
    for i, source_path_or_url in enumerate(file_sources):
        try:
            # Determine if it's a URL or a local file
            is_url = source_path_or_url.startswith("http://") or source_path_or_url.startswith("https://")
            full_source_path = source_path_or_url if is_url else os.path.join(base_file_path_prefix, source_path_or_url)

            print(f"Processing source ({'URL' if is_url else 'Local File'}): {full_source_path}")
            
            if not is_url and not os.path.exists(full_source_path):
                print(f"Warning: Local file not found: {full_source_path}. Skipping.")
                continue

            doc_content_extracted = ""
            content_mime_type = "text/markdown" # Default for DocumentConverter

            if not is_url and full_source_path.lower().endswith(".txt"):
                print(f"Reading local .txt file: {full_source_path}")
                with open(full_source_path, 'r', encoding='utf-8') as f:
                    doc_content_extracted = f.read()
                content_mime_type = "text/plain"
            else:
                print(f"Using DocumentConverter for: {full_source_path}")
                conversion_result = converter.convert(full_source_path)
                doc_content_extracted = conversion_result.document.export_to_markdown()
            
            if not doc_content_extracted.strip():
                print(f"Warning: No content extracted from {full_source_path}. Skipping.")
                continue

            all_document_contents.append(doc_content_extracted)
            # Use the source path/URL as the document ID or derive from it
            doc_id = os.path.basename(source_path_or_url) if not is_url else urllib.parse.quote_plus(source_path_or_url)
            all_document_ids.append(doc_id)
            
            # Prepare metadata for this document
            current_doc_meta = {
                "source": source_path_or_url,
                "processed_path": full_source_path,
                "is_url": is_url,
                "original_file_size": len(doc_content_extracted), # Approx size of extracted content
                "content_mime_type": content_mime_type
            }
            if document_metadatas_override and document_metadatas_override[i]:
                current_doc_meta.update(document_metadatas_override[i])
            all_original_metadatas.append(current_doc_meta)

            print(f"Successfully processed and extracted content from: {source_path_or_url}")

        except Exception as e:
            print(f"Error processing source {source_path_or_url}: {e}. Skipping this source.")
            continue
    
    if not all_document_contents:
        print("No documents were successfully processed. Exiting.")
        return False

    try:
        # 1. Initialize Text Splitter (from LangChain as it's convenient)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

        all_chunk_texts = []
        all_chunk_metadatas = []
        all_chunk_ids = [] # Chroma requires unique IDs for each chunk

        print("Splitting documents into chunks...")
        for i, doc_content in enumerate(all_document_contents): # Changed from document_contents
            # The metadata for each chunk will include the original document_id as 'source_document_id'
            # and other metadata from all_original_metadatas
            current_doc_original_metadata = all_original_metadatas[i].copy()
            current_doc_original_metadata["source_document_id"] = all_document_ids[i] # Use the generated doc_id
            
            langchain_doc = Document(page_content=doc_content, metadata=current_doc_original_metadata)
            splits = text_splitter.split_documents([langchain_doc])
            
            for j, split_doc in enumerate(splits):
                all_chunk_texts.append(split_doc.page_content)
                all_chunk_metadatas.append(split_doc.metadata) 
                all_chunk_ids.append(f"{all_document_ids[i]}_chunk_{j}") # Create a unique ID for each chunk
            print(f"Source '{all_document_ids[i]}' split into {len(splits)} chunks.")

        if not all_chunk_texts:
            print("No text chunks generated. Check document content.")
            return False
        
        print(f"Total chunks to embed and add: {len(all_chunk_texts)}")

        # 2. Initialize Embedding Function (still using LangChain's OpenAIEmbeddings for convenience)
        # The native chromadb client can also take an embedding_function that conforms to its expected interface,
        # or it can use sentence-transformers by default if you provide model name to collection.
        # Using OpenAIEmbeddings explicitly here.
        lc_embedding_function = OpenAIEmbeddings(model=embedding_model_name)

        # Helper to get embeddings for texts using the LangChain embedding function
        # Chroma's add() method can take embeddings directly or embed them if an embedding function
        # is configured with the collection or client.
        # For clarity, let's pre-embed if using LangChain's embedder.
        print("Generating embeddings for chunks...")
        chunk_embeddings = lc_embedding_function.embed_documents(all_chunk_texts)
        print(f"Generated {len(chunk_embeddings)} embeddings.")

        # 3. Initialize Chroma Client and Collection
        # For persistent storage:
        collection_persist_path = os.path.join(persist_directory_base, collection_name)
        os.makedirs(collection_persist_path, exist_ok=True) # Ensure base path for this collection exists

        # The native client takes a path argument for persistence.
        chroma_client = chromadb.PersistentClient(path=collection_persist_path)
        
        # Get or create the collection.
        # If providing your own embeddings, you don't specify embedding_function or metadata for the collection itself here,
        # unless you want Chroma to use a default embedder for queries if query_texts are used without pre-embedding.
        # Since we pre-embed for add and will pre-embed for query in the tool, this is fine.
        # If you want Chroma to handle embedding with a specific model on its own:
        # from chromadb.utils import embedding_functions
        # openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'), model_name=embedding_model_name)
        # collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=openai_ef)
        
        collection = chroma_client.get_or_create_collection(name=collection_name)
        print(f"Using ChromaDB collection: {collection_name} at {collection_persist_path}")

        # 4. Add documents (chunks) with their embeddings and metadata to the collection
        # The `add` method takes lists for ids, embeddings, metadatas, and documents (original text).
        print(f"Adding {len(all_chunk_ids)} items to collection '{collection_name}'...")
        collection.add(
            ids=all_chunk_ids,
            embeddings=chunk_embeddings,
            metadatas=all_chunk_metadatas,
            documents=all_chunk_texts  # Storing the original chunk text
        )
        print(f"Successfully added/updated items in ChromaDB collection: {collection_name}")
        # For PersistentClient, data is automatically persisted. No explicit vectordb.persist() is usually needed like with LangChain's Chroma wrapper.

        # Log to SQL (conceptual)
        for i, doc_id in enumerate(all_document_ids): # Changed from document_ids
            original_meta = all_original_metadatas[i]
            log_document_to_sql(
                doc_name=doc_id, # Use the derived document ID
                collection_name=collection_name,
                uploader_id=1, 
                description=f"Content from {original_meta.get('source', doc_id)}",
                file_path=original_meta.get('processed_path', doc_id), 
                file_size=original_meta.get('original_file_size', 0),
                mime_type=original_meta.get('content_mime_type', 'text/plain'), # Use stored mime_type
                visibility_scope="company", 
                target_company_id=1,
                embedding_model_name=embedding_model_name, 
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap,
                status="COMPLETED", 
                target_group_id=None, 
                target_vertical_id=None
            )
        return True

    except Exception as e:
        print(f"Error during RAG corpus processing for collection '{collection_name}': {e}")
        import traceback
        traceback.print_exc()
        return False


# --- Example Usage: ------------------------------------------------------------
if __name__ == '__main__':
    # --- Example Usage: ---
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable.")
        print("And ensure 'docling' is installed: pip install docling")
    else:
        # --- Setup for example ---
        sample_base_file_path = "backend/rag_files_sample" # Example base path
        os.makedirs(sample_base_file_path, exist_ok=True)
        
        # Create a dummy local txt file for testing
        sample_local_filename = "sample_local_doc.txt"
        sample_local_filepath = os.path.join(sample_base_file_path, sample_local_filename)
        with open(sample_local_filepath, "w") as f:
            f.write("This is a sample local text document for testing the ChromaDB ingestion.\nIt talks about local development environments.")

        sample_file_sources = [
            sample_local_filename, # Local file relative to base_file_path_prefix - UNCOMMENTED
            "non_existent_file.pdf", # To test skipping
            "https://www.orimi.com/pdf-test.pdf", # A sample PDF URL
            "https://arxiv.org/pdf/2408.09869", # The provided arXiv link - COMMA ADDED
        ]
        
        # Optional: if you want to pass specific metadata for each source
        # Ensure this list matches the length of sample_file_sources if used
        # sample_metadatas_override = [
        #     {"category": "local_test_data", "author": "script_runner"}, # For sample_local_filename
        #     None, # For non_existent_file
        #     {"category": "external_pdf", "topic": "pdf_example"}, # For orimi.com PDF
        #     # None, # This was commented out, keep as is for now
        #     {"category": "research_paper", "field": "AI"} # For arxiv PDF
        # ]

        collection_name_for_sample = "multi_source_docs_native_v3"
        base_persist_dir = "./my_chroma_data_multisource"

        success = process_and_embed_documents_native_chroma(
            file_sources=sample_file_sources,
            collection_name=collection_name_for_sample,
            # document_metadatas_override=sample_metadatas_override,
            persist_directory_base=base_persist_dir,
            base_file_path_prefix=sample_base_file_path # Pass the sample base path
        )

        if success:
            print(f"Native Chroma RAG Corpus Ingestion for '{collection_name_for_sample}' completed successfully.")
            
            # --- Test Querying directly with native chromadb client ---
            print("\nTesting direct query to the collection...")
            try:
                client = chromadb.PersistentClient(path=os.path.join(base_persist_dir, collection_name_for_sample))
                # Ensure the collection exists before trying to get it
                if collection_name_for_sample not in [c.name for c in client.list_collections()]:
                     print(f"Collection {collection_name_for_sample} not found. Skipping query test.")
                else:
                    collection_to_query = client.get_collection(name=collection_name_for_sample)
                    
                    query_text = "What is title of the research paper and the method used?" # Query relevant to the local sample
                    lc_embedder = OpenAIEmbeddings(model="text-embedding-3-large")
                    query_embedding = lc_embedder.embed_query(query_text)

                    results = collection_to_query.query(
                        query_embeddings=[query_embedding],
                        n_results=2,
                        include=['documents', 'metadatas', 'distances'] 
                    )
                    print("\nDirect Chroma Query Results:")
                    print(json.dumps(results, indent=2))
            except Exception as e:
                print(f"Error during direct query test: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Native Chroma RAG Corpus Ingestion for '{collection_name_for_sample}' failed.")

        # Cleanup dummy file and directory (optional)
        # try:
        #     os.remove(sample_local_filepath)
        #     os.rmdir(sample_base_file_path)
        #     print(f"Cleaned up sample file and directory: {sample_base_file_path}")
        # except OSError as e:
        #     print(f"Error cleaning up sample files: {e}")

    print(certifi.where())