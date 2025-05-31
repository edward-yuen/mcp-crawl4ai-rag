"""
Quick patch to fix the misleading tool description in crawl4ai_mcp.py

This updates the tool description to accurately reflect what it does.
"""
import os

# Read the current file
file_path = r"C:\Users\shopb\Documents\AI\mcp-crawl4ai-rag\src\crawl4ai_mcp.py"
with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the misleading description
old_description = '''"""
    Query documents from the LightRAG schema.
    
    This tool searches for documents stored in the lightrag schema, which may contain
    data from other RAG applications or pre-existing document collections.'''

new_description = '''"""
    Search for entities in the LightRAG knowledge graph.
    
    This tool searches for ENTITIES (not documents) in the knowledge graph stored
    in the chunk_entity_relation schema. It searches entity IDs and descriptions.'''

if old_description in content:
    content = content.replace(old_description, new_description)
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("[SUCCESS] Successfully updated the tool description!")
    print("\nThe query_lightrag_schema tool now correctly indicates it searches")
    print("knowledge graph ENTITIES, not regular documents.")
else:
    print("[ERROR] Could not find the exact description to replace.")
    print("You may need to manually update the description in crawl4ai_mcp.py")
    print("\nLook for the 'query_lightrag_schema' function and update its docstring to:")
    print(new_description)
