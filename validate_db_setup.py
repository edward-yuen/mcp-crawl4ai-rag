import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT")),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        print("OK Connected to database")
        
        # Test schema exists
        schema_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'crawl')"
        )
        print(f"OK Crawl schema: {'EXISTS' if schema_exists else 'MISSING'}")
        
        # Test table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'crawl' AND table_name = 'crawled_pages')"
        )
        print(f"OK Crawled pages table: {'EXISTS' if table_exists else 'MISSING'}")
        
        # Test function exists
        func_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.routines WHERE routine_schema = 'crawl' AND routine_name = 'match_crawled_pages')"
        )
        print(f"OK Match function: {'EXISTS' if func_exists else 'MISSING'}")
        
        await conn.close()
        
        if schema_exists and table_exists and func_exists:
            print("\nSUCCESS: Database setup is complete!")
            return True
        else:
            print("\nERROR: Database setup incomplete")
            return False
            
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db())
