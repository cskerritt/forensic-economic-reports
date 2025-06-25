from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from ..models.models import db, User
from urllib.parse import urlparse, urljoin
import base64
import os
import secrets

# Import SSO configuration
try:
    from ..config.sso_config import (
        SSO_ENABLED, 
        SSO_SECRET_KEY, 
        SSO_DEFAULT_USERNAME, 
        SSO_DEBUG
    )
except ImportError:
    # Default values if config is not available
    SSO_ENABLED = True
    SSO_SECRET_KEY = os.environ.get('SSO_SECRET_KEY', 'lcp-integration-secret-key')
    SSO_DEFAULT_USERNAME = 'admin'
    SSO_DEBUG = False

bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('evaluee.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('This account has been deactivated. Please contact support.')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('evaluee.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html')

@bp.route('/auto-login', methods=['GET'])
def auto_login():
    """Automatic login from the LCP application."""
    # Check if SSO is enabled
    if not SSO_ENABLED:
        flash('Single Sign-On is disabled')
        return redirect(url_for('auth.login'))

    # Get token from request
    token = request.args.get('token')
    
    if not token:
        flash('Invalid login attempt. No token provided.')
        return redirect(url_for('auth.login'))
    
    try:
        # In a production system, you would verify the token properly
        # This is a simplified approach for demonstration
        
        # Decode the base64 token which contains the user ID
        user_id_str = base64.b64decode(token).decode('utf-8')
        
        # In a real system, you'd validate this with a shared secret,
        # expiration time, etc. but for now we just look up the specified user
        
        # Find the user to login as (using the default from config)
        user = User.query.filter_by(username=SSO_DEFAULT_USERNAME).first()
        
        if not user:
            if SSO_DEBUG:
                flash(f'User {SSO_DEFAULT_USERNAME} not found')
            else:
                flash('SSO authentication failed')
            return redirect(url_for('auth.login'))
        
        # Log the user in
        login_user(user, remember=True)
        
        # Store SSO information in session
        session['sso_authenticated'] = True
        session['sso_source'] = 'lcp_tool'
        
        # Redirect to the main page
        return redirect(url_for('evaluee.index'))
    
    except Exception as e:
        if SSO_DEBUG:
            flash(f'Automatic login failed: {str(e)}')
        else:
            flash('SSO authentication failed')
        return redirect(url_for('auth.login'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('evaluee.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('auth.signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful! Welcome to Economic Analysis.')
            return redirect(url_for('evaluee.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.')
            return redirect(url_for('auth.signup'))
    
    return render_template('auth/signup.html')

@bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    
    # Clear any SSO-related session data
    if 'sso_authenticated' in session:
        session.pop('sso_authenticated', None)
    if 'sso_source' in session:
        session.pop('sso_source', None)
        
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    """User profile."""
    return render_template('auth/profile.html') 