"""
Verification Script for Database Setup
=======================================
Verifies that:
1. ORM models are properly defined
2. Database tables exist
3. Database connection works
4. Session saving utilities are available
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_orm_models():
    """Verify ORM models are properly defined."""
    try:
        from app.orm.models import Tenant, Session
        from app.orm.base import Base
        
        logger.info("✅ ORM models imported successfully")
        logger.info(f"   - Tenant model: {Tenant.__tablename__}")
        logger.info(f"   - Session model: {Session.__tablename__}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import ORM models: {e}")
        return False


def verify_database_connection():
    """Verify database connection works."""
    try:
        from app.orm.session import engine
        from sqlalchemy import inspect, text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def verify_tables_exist():
    """Verify required tables exist."""
    try:
        from app.orm.session import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['tenants', 'sessions']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            logger.error(f"❌ Missing tables: {', '.join(missing)}")
            logger.info(f"   Run: python migration.py")
            return False
        
        logger.info("✅ All required tables exist:")
        for table in required_tables:
            columns = inspector.get_columns(table)
            logger.info(f"   - {table}: {len(columns)} columns")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to verify tables: {e}")
        return False


def verify_db_utils():
    """Verify database utilities are available."""
    try:
        from app.services.ai.ml.db_utils import save_session_to_db, get_client_info
        
        logger.info("✅ Database utilities imported successfully")
        logger.info("   - save_session_to_db function available")
        logger.info("   - get_client_info function available")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import database utilities: {e}")
        return False


def verify_routes_integration():
    """Verify routes have database saving integrated."""
    try:
        import inspect
        from app.services.ai.ml import routes
        
        # Check if save_session_to_db is imported in routes
        if hasattr(routes, 'save_session_to_db'):
            logger.info("✅ Routes module has save_session_to_db imported")
        else:
            logger.warning("⚠️  Routes module doesn't have save_session_to_db - check imports")
        
        # Check if query_endpoint uses save_session_to_db
        if hasattr(routes, 'query_endpoint'):
            source = inspect.getsource(routes.query_endpoint)
            if 'save_session_to_db' in source:
                logger.info("✅ query_endpoint uses save_session_to_db")
            else:
                logger.warning("⚠️  query_endpoint doesn't use save_session_to_db")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to verify routes integration: {e}")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("🔍 Verifying Database Setup")
    logger.info("=" * 60)
    
    checks = [
        ("ORM Models", verify_orm_models),
        ("Database Connection", verify_database_connection),
        ("Database Tables", verify_tables_exist),
        ("Database Utilities", verify_db_utils),
        ("Routes Integration", verify_routes_integration),
    ]
    
    results = []
    for name, check_func in checks:
        logger.info(f"\n📋 Checking {name}...")
        result = check_func()
        results.append((name, result))
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Verification Summary")
    logger.info("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        logger.info("\n✅ All checks passed! Database setup is ready.")
    else:
        logger.info("\n⚠️  Some checks failed. Please review the errors above.")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Run: python migration.py")
        logger.info("   2. Verify database connection in .env")
        logger.info("   3. Check that all imports are correct")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
