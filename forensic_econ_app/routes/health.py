from flask import Blueprint, jsonify
from ..models.models import db
import datetime
import logging
from sqlalchemy import text

bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

@bp.route('/health')
def health_check():
    """Simple health check endpoint."""
    try:
        # Test database connection
        result = db.session.execute(text('SELECT 1')).scalar()
        db_status = 'healthy' if result == 1 else 'unhealthy'

        health_data = {
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'database': db_status
        }
        return jsonify(health_data), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_data = {
            'status': 'unhealthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'error': str(e)
        }
        return jsonify(health_data), 500


