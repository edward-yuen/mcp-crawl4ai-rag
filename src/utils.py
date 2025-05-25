"""
Utility functions for the Crawl4AI MCP server.
"""
import os
import json
import logging
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import openai
from .database import get_db_connection, DatabaseConnection

# Set up logging
logger = logging.getLogger(__name__)

# Load OpenAI API key for embeddings
openai.api_key = os.getenv("OPENAI_API_KEY")


def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for multiple texts in a single API call.
    
    Args:
        texts: List of texts to create embeddings for
        
    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    if not texts:
        return []
        
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",  # Hardcoding embedding model for now, will change this later to be more dynamic
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Error creating batch embeddings: {e}")
        # Return empty embeddings if there's an error
        return [[0.0] * 1536 for _ in range(len(texts))]


def create_embedding(text: str) -> List[float]:
    """
    Create an embedding for a single text using OpenAI's API.
    
    Args:
        text: Text to create an embedding for
        
    Returns:
        List of floats representing the embedding
    """
    try:
        embeddings = create_embeddings_batch([text])
        return embeddings[0] if embeddings else [0.0] * 1536
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        # Return empty embedding if there's an error
        return [0.0] * 1536


def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
    """
    Generate contextual information for a chunk within a document to improve retrieval.
    
    Args:
        full_document: The complete document text
        chunk: The specific chunk of text to generate context for
        
    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    model_choice = os.getenv("MODEL_CHOICE")
    
    try:
        # Create the prompt for generating contextual information
        prompt = f"""<document> 
{full_document[:25000]} 
</document>
Here is the chunk we want to situate within the whole document 
<chunk> 
{chunk}
</chunk> 
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        # Call the OpenAI API to generate contextual information
        response = openai.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        # Extract the generated context
        context = response.choices[0].message.content.strip()
        
        # Combine the context with the original chunk
        contextual_text = f"{context}\n---\n{chunk}"
        
        return contextual_text, True
    
    except Exception as e:
        logger.error(f"Error generating contextual embedding: {e}. Using original chunk instead.")
        return chunk, False


def process_chunk_with_context(args):
    """
    Process a single chunk with contextual embedding.
    This function is designed to be used with concurrent.futures.
    
    Args:
        args: Tuple containing (url, content, full_document)
        
    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    url, content, full_document = args
    return generate_contextual_embedding(full_document, content)


async def add_documents_to_postgres(
    urls: List[str], 
    chunk_numbers: List[int],
    contents: List[str], 
    metadatas: List[Dict[str, Any]],
    url_to_full_document: Dict[str, str],
    batch_size: int = 20
) -> None:
    """
    Add documents to the PostgreSQL crawled_pages table in batches.
    Deletes existing records with the same URLs before inserting to prevent duplicates.
    
    Args:
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        contents: List of document contents
        metadatas: List of document metadata
        url_to_full_document: Dictionary mapping URLs to their full document content
        batch_size: Size of each batch for insertion
    """
    # Get database connection
    db = await get_db_connection()
    
    # Get unique URLs to delete existing records
    unique_urls = list(set(urls))
    
    # Delete existing records for these URLs in a single operation
    try:
        if unique_urls:
            # Use ANY to delete all records with matching URLs
            await db.execute(
                "DELETE FROM crawl.crawled_pages WHERE url = ANY($1::text[])",
                unique_urls
            )
            logger.info(f"Deleted existing records for {len(unique_urls)} URLs")
    except Exception as e:
        logger.error(f"Batch delete failed: {e}. Trying one-by-one deletion as fallback.")
        # Fallback: delete records one by one
        for url in unique_urls:
            try:
                await db.execute(
                    "DELETE FROM crawl.crawled_pages WHERE url = $1",
                    url
                )
            except Exception as inner_e:
                logger.error(f"Error deleting record for URL {url}: {inner_e}")
                # Continue with the next URL even if one fails
    
    # Check if MODEL_CHOICE is set for contextual embeddings
    model_choice = os.getenv("MODEL_CHOICE")
    use_contextual_embeddings = bool(model_choice)
    
    # Process in batches to avoid memory issues
    for i in range(0, len(contents), batch_size):
        batch_end = min(i + batch_size, len(contents))
        
        # Get batch slices
        batch_urls = urls[i:batch_end]
        batch_chunk_numbers = chunk_numbers[i:batch_end]
        batch_contents = contents[i:batch_end]
        batch_metadatas = metadatas[i:batch_end]
        
        # Apply contextual embedding to each chunk if MODEL_CHOICE is set
        if use_contextual_embeddings:
            # Prepare arguments for parallel processing
            process_args = []
            for j, content in enumerate(batch_contents):
                url = batch_urls[j]
                full_document = url_to_full_document.get(url, "")
                process_args.append((url, content, full_document))
            
            # Process in parallel using ThreadPoolExecutor
            contextual_contents = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all tasks and collect results
                future_to_idx = {executor.submit(process_chunk_with_context, arg): idx 
                                for idx, arg in enumerate(process_args)}
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result, success = future.result()
                        contextual_contents.append((idx, result))
                        if success:
                            batch_metadatas[idx]["contextual_embedding"] = True
                    except Exception as e:
                        logger.error(f"Error processing chunk {idx}: {e}")
                        # Use original content as fallback
                        contextual_contents.append((idx, batch_contents[idx]))
            
            # Sort results back into original order
            contextual_contents.sort(key=lambda x: x[0])
            contextual_contents = [content for _, content in contextual_contents]
            
            if len(contextual_contents) != len(batch_contents):
                logger.warning(f"Expected {len(batch_contents)} results but got {len(contextual_contents)}")
                # Use original contents as fallback
                contextual_contents = batch_contents
        else:
            # If not using contextual embeddings, use original contents
            contextual_contents = batch_contents
        
        # Create embeddings for the entire batch at once
        batch_embeddings = create_embeddings_batch(contextual_contents)
        
        # Prepare batch data for insertion
        batch_data = []
        for j in range(len(contextual_contents)):
            # Extract metadata fields
            chunk_size = len(contextual_contents[j])
            
            # Update metadata with chunk size
            metadata = {
                "chunk_size": chunk_size,
                **batch_metadatas[j]
            }
            
            # Prepare data tuple for insertion
            batch_data.append((
                batch_urls[j],
                batch_chunk_numbers[j],
                contextual_contents[j],  # Store contextual content
                json.dumps(metadata),    # Convert metadata to JSON string
                batch_embeddings[j]      # Use embedding from contextual content
            ))
        
        # Insert batch into PostgreSQL using execute_many
        try:
            await db.execute_many(
                """
                INSERT INTO crawl.crawled_pages (url, chunk_number, content, metadata, embedding)
                VALUES ($1, $2, $3, $4::jsonb, $5::vector)
                ON CONFLICT (url, chunk_number) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    created_at = CURRENT_TIMESTAMP
                """,
                batch_data
            )
            logger.info(f"Inserted batch of {len(batch_data)} documents")
        except Exception as e:
            logger.error(f"Error inserting batch into PostgreSQL: {e}")
            # Try inserting one by one as fallback
            for data in batch_data:
                try:
                    await db.execute(
                        """
                        INSERT INTO crawl.crawled_pages (url, chunk_number, content, metadata, embedding)
                        VALUES ($1, $2, $3, $4::jsonb, $5::vector)
                        ON CONFLICT (url, chunk_number) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            created_at = CURRENT_TIMESTAMP
                        """,
                        *data
                    )
                except Exception as inner_e:
                    logger.error(f"Error inserting single document: {inner_e}")


async def search_documents(
    query: str, 
    match_count: int = 10, 
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents in PostgreSQL using vector similarity.
    
    Args:
        query: Query text
        match_count: Maximum number of results to return
        filter_metadata: Optional metadata filter
        
    Returns:
        List of matching documents
    """
    # Get database connection
    db = await get_db_connection()
    
    # Create embedding for the query
    query_embedding = create_embedding(query)
    
    # Execute the search using the match_crawled_pages function
    try:
        # Prepare filter parameter (empty dict if no filter provided)
        filter_param = json.dumps(filter_metadata) if filter_metadata else '{}'
        
        # Execute the search function
        # Reason: We need to pass the embedding as a list and convert to vector in SQL
        results = await db.fetch(
            """
            SELECT * FROM crawl.match_crawled_pages(
                $1::vector,
                $2,
                $3::jsonb
            )
            """,
            query_embedding,
            match_count,
            filter_param
        )
        
        # Convert results to list of dictionaries
        documents = []
        for row in results:
            doc = {
                'id': row['id'],
                'url': row['url'],
                'chunk_number': row['chunk_number'],
                'content': row['content'],
                'metadata': row['metadata'],
                'similarity': row['similarity']
            }
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return []
