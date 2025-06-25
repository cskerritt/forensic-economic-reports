"""
Simplified Life Care Plan Routes

Basic life care plan functionality without external dependencies.
This version uses only Flask core dependencies for basic CRUD operations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import logging

from ..models.models import db
from ..utils.package_checker import check_life_care_dependencies

logger = logging.getLogger(__name__)

bp = Blueprint('life_care_plan', __name__, url_prefix='/life-care-plan')


# Simple evaluee model using basic SQLAlchemy
class SimpleLCPEvaluee(db.Model):
    """Simplified Life Care Plan evaluee model."""
    __tablename__ = 'simple_lcp_evaluees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=True)
    date_of_injury = db.Column(db.DateTime, nullable=True)
    primary_diagnosis = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="simple_lcp_evaluees")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@bp.route('/evaluees')
@login_required
def evaluees_index():
    """List all simple life care plan evaluees."""
    try:
        evaluees = SimpleLCPEvaluee.query.filter_by(user_id=current_user.id).order_by(SimpleLCPEvaluee.created_at.desc()).all()
        
        # Check if full functionality is available
        full_available, missing_packages = check_life_care_dependencies()
        
        return render_template('life_care_plan/simple_evaluees.html', 
                             evaluees=evaluees,
                             full_available=full_available,
                             missing_packages=missing_packages)
    except Exception as e:
        logger.error(f"Error loading evaluees: {str(e)}")
        flash(f'Error loading evaluees: {str(e)}', 'danger')
        return redirect(url_for('evaluee.index'))


@bp.route('/evaluees/create', methods=['GET', 'POST'])
@login_required
def create_evaluee():
    """Create a simple life care plan evaluee."""
    if request.method == 'POST':
        try:
            evaluee = SimpleLCPEvaluee(
                user_id=current_user.id,
                first_name=request.form.get('first_name', '').strip(),
                last_name=request.form.get('last_name', '').strip(),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d') if request.form.get('date_of_birth') else None,
                date_of_injury=datetime.strptime(request.form.get('date_of_injury'), '%Y-%m-%d') if request.form.get('date_of_injury') else None,
                primary_diagnosis=request.form.get('primary_diagnosis')
            )
            
            db.session.add(evaluee)
            db.session.commit()
            
            flash(f'Life Care Plan evaluee "{evaluee.full_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.evaluees_index'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating evaluee: {str(e)}")
            flash(f'Error creating evaluee: {str(e)}', 'danger')
    
    return render_template('life_care_plan/simple_create.html')


@bp.route('/info')
@login_required
def info():
    """Information about the Life Care Plan module."""
    return render_template('life_care_plan/info.html')


@bp.route('/status')
@login_required
def status():
    """Check package status and installation instructions."""
    full_available, missing_packages = check_life_care_dependencies()
    
    package_status = {}
    required_packages = ['pandas', 'openpyxl', 'docx', 'matplotlib']
    
    for package in required_packages:
        try:
            __import__(package)
            package_status[package] = 'available'
        except ImportError:
            package_status[package] = 'missing'
    
    return render_template('life_care_plan/status.html',
                         full_available=full_available,
                         missing_packages=missing_packages,
                         package_status=package_status)