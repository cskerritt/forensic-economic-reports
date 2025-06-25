"""Database utilities for improved connection handling and retry logic."""
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def get_engine(app):
    """Create a SQLAlchemy engine with connection pooling."""
    return create_engine(
        app.config['SQLALCHEMY_DATABASE_URI'],
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
    )

def retry_on_db_error(max_retries=3, retry_delay=1):
    """
    Decorator to retry database operations on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (in seconds)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyError) as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                        raise
                    
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** (retries - 1))
                    logger.warning(f"Database operation failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

def check_db_connection(db):
    """
    Check if the database connection is working.
    
    Args:
        db: SQLAlchemy database instance
        
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        # Execute a simple query
        db.session.execute('SELECT 1')
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        db.session.rollback()
        return False
