"""
Package availability checker for life care plan functionality.
"""

def check_life_care_dependencies():
    """
    Check if all required packages for full life care plan functionality are available.
    
    Returns:
        tuple: (bool, list) - (all_available, missing_packages)
    """
    required_packages = {
        'pandas': 'pandas>=2.0.0',
        'openpyxl': 'openpyxl>=3.1.0', 
        'docx': 'python-docx>=1.1.0',
        'matplotlib': 'matplotlib>=3.7.0'
    }
    
    missing = []
    
    for package, requirement in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(requirement)
    
    # Also check if packages have been verified as working
    import os
    status_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.lcp_status')
    packages_verified = os.path.exists(status_file)
    
    return len(missing) == 0 and packages_verified, missing


def get_life_care_blueprint():
    """
    Get the appropriate life care plan blueprint based on available dependencies.
    
    Returns:
        module: Either full or simple life care plan blueprint
    """
    all_available, missing = check_life_care_dependencies()
    
    if all_available:
        try:
            from ..routes.life_care_plan import bp
            return bp, 'full'
        except ImportError as e:
            # Fall back to simple version if full version has other issues
            from ..routes.life_care_plan_simple import bp
            return bp, 'simple_fallback'
    else:
        from ..routes.life_care_plan_simple import bp
        return bp, 'simple'