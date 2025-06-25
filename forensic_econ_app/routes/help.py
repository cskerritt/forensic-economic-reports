from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('help', __name__, url_prefix='/help')

@bp.route('/quick-start')
@login_required
def quick_start():
    """Display the quick start guide."""
    return render_template('help/quick_start.html')

@bp.route('/keyboard-shortcuts')
@login_required
def keyboard_shortcuts():
    """Display keyboard shortcuts."""
    return render_template('help/keyboard_shortcuts.html')

@bp.route('/workflow')
@login_required
def workflow():
    """Display the recommended workflow."""
    return render_template('help/workflow.html')
