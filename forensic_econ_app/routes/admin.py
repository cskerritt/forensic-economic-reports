"""
Admin routes for the application.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from ..models.models import db, User, Evaluee, EarningsScenario, HouseholdServicesScenario
from werkzeug.security import generate_password_hash
from sqlalchemy import func
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin required decorator
def admin_required(f):
    """Decorator to require admin access for a route."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard."""
    # Get counts for various models
    user_count = User.query.count()
    evaluee_count = Evaluee.query.count()
    earnings_scenario_count = EarningsScenario.query.count()
    household_services_count = HouseholdServicesScenario.query.count()
    medical_cost_count = 0  # Medical costs have been removed

    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        'admin/index.html',
        user_count=user_count,
        evaluee_count=evaluee_count,
        earnings_scenario_count=earnings_scenario_count,
        household_services_count=household_services_count,
        medical_cost_count=medical_cost_count,
        recent_users=recent_users
    )

@bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=users)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form

        # Validate input
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.new_user'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.new_user'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.new_user'))

        # Create new user
        user = User(
            username=username,
            email=email,
            is_admin=is_admin
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            flash(f'Error creating user: {str(e)}', 'danger')
            return redirect(url_for('admin.new_user'))

    return render_template('admin/new_user.html')

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        is_active = 'is_active' in request.form

        # Validate input
        if not username or not email:
            flash('Username and email are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # Check if username already exists (for a different user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # Check if email already exists (for a different user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # Update user
        user.username = username
        user.email = email
        user.is_admin = is_admin
        user.is_active = is_active

        # Update password if provided
        if password:
            user.set_password(password)

        try:
            db.session.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {str(e)}")
            flash(f'Error updating user: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

    return render_template('admin/edit_user.html', user=user)

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        flash(f'Error deleting user: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))

@bp.route('/evaluees')
@login_required
@admin_required
def evaluees():
    """List all evaluees."""
    evaluees = Evaluee.query.order_by(Evaluee.last_name, Evaluee.first_name).all()
    return render_template('admin/evaluees.html', evaluees=evaluees)

@bp.route('/system-info')
@login_required
@admin_required
def system_info():
    """Display system information."""
    # Get database statistics
    stats = {
        'users': User.query.count(),
        'evaluees': Evaluee.query.count(),
        'earnings_scenarios': EarningsScenario.query.count(),
        'household_services': HouseholdServicesScenario.query.count(),
        'medical_costs': 0,  # Medical costs have been removed
    }

    return render_template('admin/system_info.html', stats=stats)
