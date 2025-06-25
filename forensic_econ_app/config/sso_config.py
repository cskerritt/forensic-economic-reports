"""
Single Sign-On (SSO) Configuration

This file contains configuration settings for the SSO integration between
the LCP tool and the Economic Analysis tool.
"""
import os
import secrets

# Enable or disable SSO functionality
SSO_ENABLED = True

# Secret key for validating SSO tokens (should be set as an environment variable in production)
SSO_SECRET_KEY = os.environ.get('SSO_SECRET_KEY', 'lcp-integration-secret-key')

# Token expiration time in seconds (60 minutes by default)
SSO_TOKEN_EXPIRATION = 3600  # 1 hour

# Default user to log in when SSO is used (admin by default)
# This is a simplification for demonstration purposes
# In a production environment, you would map LCP users to Economic Analysis users
SSO_DEFAULT_USERNAME = 'admin'

# Debug mode (enables detailed error messages for SSO issues)
SSO_DEBUG = os.environ.get('SSO_DEBUG', 'False').lower() == 'true' 