import os
import asyncio

import psycopg2
try:
    import asyncpg
except ImportError:
    asyncpg = None
    print("⚠️  asyncpg not installed. Asynchronous database operations will not work.")

def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

load_env()

async def create_async_connection_pool():
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'vacloudopsdb1')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', '127.0.0.1')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
    
    # Add timeout to prevent hanging (5 seconds for connection)
    connection_timeout = float(os.environ.get('DB_CONNECTION_TIMEOUT', '5.0'))

    try:
        pool = await asyncio.wait_for(
            asyncpg.create_pool(
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                min_size=1,
                max_size=10,
                command_timeout=10.0  # 10 seconds for queries
            ),
            timeout=connection_timeout
        )
        print("Async connection pool created successfully!")
        return pool
    except asyncio.TimeoutError:
        print(f"⚠️  Database connection timeout after {connection_timeout}s. Database may be unavailable.")
        return None
    except Exception as e:
        print(f"⚠️  Error creating async connection pool: {e}")
        return None

async_pool = None

async def async_postgres_connection():
    global async_pool
    if async_pool is None:
        async_pool = await create_async_connection_pool()

    if async_pool:
        return await async_pool.acquire()
    else:
        raise ConnectionError("Database connection pool is not initialized.")

async def close_db_connection_pool():
    global async_pool
    if async_pool:
        await async_pool.close()
        async_pool = None
        print("Async connection pool closed.")

# Keep the old synchronous function for compatibility if it's used elsewhere, but mark it for future removal
def basic_postgres_connection():
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'vacloudopsdb1')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', '127.0.0.1')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
    return psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    ) 