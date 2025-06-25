import os
from flask import Flask, render_template, request
from flask_migrate import Migrate
from flask_login import LoginManager
from .models.models import db, User
from .config.config import config
import logging
from logging.handlers import RotatingFileHandler
import traceback

migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Set up enhanced logging
    app.logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Add file handler for logging
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'economic_analysis.log'),
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.info('Economic Analysis startup')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f'Not Found: {request.path}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True)
        error_description = str(error)
        if hasattr(error, '__cause__') and error.__cause__:
            error_description += f"\nCaused by: {error.__cause__}"
        return render_template('errors/500.html',
                              error=str(error),
                              error_description=error_description), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        db.session.rollback()
        app.logger.error(f'Unhandled Exception: {e}')
        error_trace = traceback.format_exc()
        app.logger.error(error_trace)
        return render_template('errors/500.html',
                              error=str(e),
                              error_description=error_trace), 500

    # Register blueprints
    from .routes import evaluee, demographics, worklife, aef, earnings
    # from forensic_econ_app.routes.healthcare import healthcare  # Removed healthcare module
    from forensic_econ_app.routes.settings import settings
    from forensic_econ_app.routes.health import bp as health_bp
    from forensic_econ_app.routes.auth import bp as auth_bp
    from forensic_econ_app.routes.household import household
    from forensic_econ_app.routes.pcpm import bp as pcpm_bp
    from forensic_econ_app.routes.fringe_benefits import bp as fringe_benefits_bp
    from forensic_econ_app.routes.reports import bp as reports_bp
    from forensic_econ_app.routes.admin import bp as admin_bp
    from forensic_econ_app.routes.help import bp as help_bp
    # Conditional import for life care plan - full version if dependencies available, simple otherwise
    try:
        from .utils.package_checker import get_life_care_blueprint
        life_care_plan_bp, lcp_version = get_life_care_blueprint()
        app.logger.info(f'Loading life care plan module: {lcp_version} version')
    except Exception as e:
        app.logger.warning(f'Error loading life care plan module: {e}')
        from forensic_econ_app.routes.life_care_plan import bp as life_care_plan_bp
    # from forensic_econ_app.routes.sample_data import bp as sample_data_bp
    from .commands import init_ecec_data, create_admin

    app.logger.debug('Registering blueprints...')

    app.register_blueprint(auth_bp)
    app.register_blueprint(evaluee.bp)
    app.register_blueprint(demographics.bp)
    app.register_blueprint(worklife.bp)
    app.register_blueprint(aef.bp)
    app.register_blueprint(earnings.bp)
    # app.register_blueprint(healthcare)  # Removed healthcare module
    app.register_blueprint(settings)
    app.register_blueprint(health_bp)
    app.register_blueprint(household)
    app.register_blueprint(pcpm_bp)
    app.register_blueprint(fringe_benefits_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(help_bp)
    app.register_blueprint(life_care_plan_bp)
    # app.register_blueprint(sample_data_bp)
    app.logger.debug('Successfully registered blueprints')

    # Register commands
    app.cli.add_command(init_ecec_data)
    app.cli.add_command(create_admin)

    
    # Register forensic reports blueprint
    from .routes import forensic_reports
    app.register_blueprint(forensic_reports.bp)

    return app