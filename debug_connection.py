#!/usr/bin/env python3
"""
Debug the database connection issue in lightrag_integration.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

async def debug_connection():
    """Debug database connection access."""
    print("=== Database Connection Debug ===\n")
    
    from database import initialize_db_connection, get_db_connection, close_db_connection
    
    # Initialize connection
    print("[1] Initializing database connection...")
    await initialize_db_connection()
    print("   [OK] Connection initialized")
    
    # Test direct access
    print("\n[2] Testing direct database access...")
    try:
        db = await get_db_connection()
        print(f"   [OK] Got connection object: {type(db)}")
        
        # Test a simple query
        result = await db.fetchval("SELECT 1")
        print(f"   [OK] Simple query result: {result}")
        
        # Test AGE extension
        await db.execute("LOAD 'age'")
        print("   [OK] AGE extension loaded")
        
        # Test actual data access
        count = await db.fetchval("SELECT count(*) FROM chunk_entity_relation._ag_label_vertex")
        print(f"   [OK] Node count: {count}")
        
        if count > 0:
            # Test JSON property access
            sample = await db.fetch("""
                SELECT id, properties::json->>'entity_id' as entity_id
                FROM chunk_entity_relation._ag_label_vertex 
                LIMIT 1
            """)
            print(f"   [OK] Sample query worked, got {len(sample)} rows")
            if sample:
                print(f"   Sample entity_id: {sample[0]['entity_id']}")
        
    except Exception as e:
        print(f"   [ERROR] Database access failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the lightrag functions
    print("\n[3] Testing lightrag_integration functions...")
    try:
        from lightrag_integration import search_lightrag_documents
        
        # Test with a direct call
        results = await search_lightrag_documents("fusion", 3)
        print(f"   [OK] search_lightrag_documents returned {len(results)} results")
        
    except Exception as e:
        print(f"   [ERROR] LightRAG function failed: {e}")
        import traceback
        traceback.print_exc()
    
    await close_db_connection()
    print("\n[OK] Debug completed")

if __name__ == "__main__":
    asyncio.run(debug_connection())
