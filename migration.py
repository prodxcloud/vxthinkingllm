"""
Database Migration Script for VaLLM
====================================
Creates all database tables defined in app.orm.models.

This script should be run from the project root:
    python migration.py

It will:
1. Connect to the database using settings from .env or app.core.db
2. Create all tables (tenants, sessions) if they don't exist
3. Verify the tables were created successfully
"""

import sys
import os
import uuid
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Import database configuration
from app.orm.base import Base
from app.orm.models import Tenant, Session
from app.orm.session import engine, SessionLocal
from app.core.db import get_db_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_connection():
    """Verify database connection is working."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"✅ Database connected: PostgreSQL {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def check_tables_exist():
    """Check if tables already exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = ['tenants', 'sessions']
    
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if missing_tables:
        logger.info(f"📋 Missing tables: {', '.join(missing_tables)}")
        return False, existing_tables
    else:
        logger.info(f"✅ All required tables exist: {', '.join(required_tables)}")
        return True, existing_tables


def create_tables():
    """Create all tables defined in the ORM models."""
    try:
        logger.info("🔨 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tables created successfully!")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_default_tenant():
    """Create the default primary tenant 'va_infinityai_ai'."""
    try:
        with SessionLocal() as db:
            # Check if default tenant already exists (by name or by TENANT_ID from env)
            env_tenant_id = os.getenv("TENANT_ID")
            if env_tenant_id:
                try:
                    env_uuid = uuid.UUID(env_tenant_id)
                    existing = db.query(Tenant).filter_by(tenant_id=env_uuid).first()
                    if existing:
                        logger.info(f"✅ Default tenant already exists (from TENANT_ID): {existing.tenant_id}")
                        return str(existing.tenant_id)
                except (ValueError, TypeError):
                    pass
            existing = db.query(Tenant).filter_by(tenant_name="va_infinityai_ai").first()
            if existing:
                logger.info(f"✅ Default tenant already exists: {existing.tenant_id}")
                return str(existing.tenant_id)
            
            # Use TENANT_ID from .env if set, else generate a fixed UUID
            if env_tenant_id:
                try:
                    default_tenant_id = uuid.UUID(env_tenant_id)
                except (ValueError, TypeError):
                    default_tenant_id = uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        "va_infinityai_ai.primary.tenant"
                    )
            else:
                default_tenant_id = uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    "va_infinityai_ai.primary.tenant"
                )
            
            # Generate a default API key and hash it
            # Default API key: "va_infinityai_ai_default_key_2024"
            default_api_key = "va_infinityai_ai_default_key_2024"
            token_hash = hashlib.sha256(default_api_key.encode()).hexdigest()
            
            # Create default tenant
            default_tenant = Tenant(
                tenant_id=default_tenant_id,
                tenant_name="va_infinityai_ai",
                email="admin@va_infinityai_ai.com",
                description="Primary default tenant for VaLLM - InfinityAI",
                token_hash=token_hash,
                environment="PRODUCTION",
                sub_tenants=[],
                allowed_services=None,  # None means all services allowed
                disallowed_services=None,
                scopes=None,  # None means all scopes
                is_read_only=False,
                rate_limit=10000,  # Higher limit for primary tenant
                is_active=True,
                expires_at=None,  # Never expires
                usage_count=0,
                allowed_ips=None,  # None means all IPs allowed
                metadata_={
                    "is_primary": True,
                    "created_by": "migration",
                    "default_api_key_preview": default_api_key[:20] + "...",
                    "note": "This is the primary default tenant created during migration"
                }
            )
            
            db.add(default_tenant)
            db.commit()
            db.refresh(default_tenant)
            
            logger.info(f"✅ Default tenant created successfully!")
            logger.info(f"   Tenant ID: {default_tenant.tenant_id}")
            logger.info(f"   Tenant Name: {default_tenant.tenant_name}")
            logger.info(f"   Environment: {default_tenant.environment}")
            logger.info(f"   Default API Key: {default_api_key}")
            logger.warning(f"   ⚠️  IMPORTANT: Save this API key securely: {default_api_key}")
            
            return str(default_tenant.tenant_id)
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Error creating default tenant: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error creating default tenant: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_tables():
    """Verify tables were created and show their structure."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"\n📊 Database Tables ({len(tables)} total):")
        logger.info("=" * 60)
        
        for table_name in ['tenants', 'sessions']:
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                logger.info(f"\n📋 Table: {table_name}")
                logger.info(f"   Columns ({len(columns)}):")
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    logger.info(f"     - {col['name']}: {col_type} ({nullable})")
                
                # Check indexes
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    logger.info(f"   Indexes ({len(indexes)}):")
                    for idx in indexes:
                        logger.info(f"     - {idx['name']}: {', '.join(idx['column_names'])}")
            else:
                logger.warning(f"⚠️  Table '{table_name}' not found!")
        
        logger.info("=" * 60)
        
        # Show tenant data if available
        try:
            with SessionLocal() as db:
                tenants = db.query(Tenant).all()
                if tenants:
                    logger.info(f"\n👤 Tenants in database ({len(tenants)}):")
                    logger.info("=" * 60)
                    for tenant in tenants:
                        logger.info(f"\n   Tenant: {tenant.tenant_name}")
                        logger.info(f"   Tenant ID: {tenant.tenant_id}")
                        logger.info(f"   Email: {tenant.email or 'N/A'}")
                        logger.info(f"   Environment: {tenant.environment}")
                        logger.info(f"   Active: {tenant.is_active}")
                        logger.info(f"   Rate Limit: {tenant.rate_limit}")
                        logger.info(f"   Usage Count: {tenant.usage_count}")
                        if tenant.metadata_ and tenant.metadata_.get('is_primary'):
                            logger.info(f"   ⭐ PRIMARY TENANT")
                    logger.info("=" * 60)
        except Exception as e:
            logger.debug(f"Could not fetch tenant data: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False


def get_database_info():
    """Display database connection information."""
    try:
        config = get_db_config()
        logger.info("\n📡 Database Configuration:")
        logger.info("=" * 60)
        logger.info(f"   Host: {config['host']}")
        logger.info(f"   Port: {config['port']}")
        logger.info(f"   Database: {config['database']}")
        logger.info(f"   User: {config['user']}")
        logger.info("=" * 60)
    except Exception as e:
        logger.warning(f"⚠️  Could not get database config: {e}")


def main():
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("🚀 VaLLM Database Migration")
    logger.info("=" * 60)
    
    # Show database info
    get_database_info()
    
    # Check connection
    if not check_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Check existing tables
    tables_exist, existing_tables = check_tables_exist()
    
    if tables_exist:
        logger.info("\n✅ All tables already exist. Migration not needed.")
        verify_tables()
        
        # Still check/create default tenant even if tables exist
        logger.info("\n👤 Checking default tenant...")
        tenant_id = create_default_tenant()
        if tenant_id:
            logger.info(f"   Default tenant ID: {tenant_id}")
        else:
            logger.info("   Default tenant already exists or could not be created")
        
        logger.info("\n💡 To recreate tables, drop them first or use --force flag")
        return
    
    # Create tables
    logger.info("\n🔨 Starting migration...")
    if not create_tables():
        logger.error("❌ Migration failed!")
        sys.exit(1)
    
    # Create default tenant
    logger.info("\n👤 Creating default tenant...")
    tenant_id = create_default_tenant()
    if tenant_id:
        logger.info(f"   Default tenant ID: {tenant_id}")
    else:
        logger.warning("   ⚠️  Could not create default tenant (may already exist)")
    
    # Verify
    logger.info("\n🔍 Verifying migration...")
    if not verify_tables():
        logger.error("❌ Verification failed!")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Migration completed successfully!")
    logger.info("=" * 60)
    logger.info("\n📝 Next steps:")
    logger.info("   1. Tables are ready to use")
    logger.info("   2. Default tenant 'va_infinityai_ai' has been created")
    logger.info("   3. Start saving queries, requests, and responses to database")
    logger.info("   4. Use app.orm.session.get_db() or get_db_context() for database access")
    if tenant_id:
        logger.info(f"\n🔑 Default Tenant Information:")
        logger.info(f"   Tenant ID: {tenant_id}")
        logger.info(f"   Tenant Name: va_infinityai_ai")
        logger.info(f"   Default API Key: va_infinityai_ai_default_key_2024")
        logger.warning(f"   ⚠️  Save the API key securely!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VaLLM Database Migration")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of tables (WARNING: This will drop existing tables!)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if tables exist, don't create them"
    )
    
    args = parser.parse_args()
    
    if args.check_only:
        get_database_info()
        check_database_connection()
        tables_exist, _ = check_tables_exist()
        if tables_exist:
            verify_tables()
        
        # Check for default tenant
        try:
            with SessionLocal() as db:
                from app.orm.models import Tenant
                default_tenant = db.query(Tenant).filter_by(tenant_name="va_infinityai_ai").first()
                if default_tenant:
                    logger.info(f"\n✅ Default tenant found:")
                    logger.info(f"   Tenant ID: {default_tenant.tenant_id}")
                    logger.info(f"   Name: {default_tenant.tenant_name}")
                    logger.info(f"   Environment: {default_tenant.environment}")
                    logger.info(f"   Active: {default_tenant.is_active}")
                else:
                    logger.warning("\n⚠️  Default tenant 'va_infinityai_ai' not found")
        except Exception as e:
            logger.warning(f"\n⚠️  Could not check for default tenant: {e}")
        
        sys.exit(0)
    
    if args.force:
        logger.warning("⚠️  FORCE MODE: This will drop and recreate all tables!")
        response = input("Are you sure? This will DELETE ALL DATA! (yes/no): ")
        if response.lower() != "yes":
            logger.info("Migration cancelled.")
            sys.exit(0)
        
        # Drop all tables
        try:
            logger.info("🗑️  Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ Tables dropped")
        except Exception as e:
            logger.error(f"❌ Error dropping tables: {e}")
            sys.exit(1)
    
    main()
