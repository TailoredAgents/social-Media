"""
Social Media Integrations Package

Provides unified access to social media platform APIs with backwards compatibility.
Updated for Meta Graph API v22.0 unified approach.
"""
from backend.integrations.meta_client import meta_client

# Unified Meta client (preferred for new code)
from backend.integrations.meta_client import MetaGraphAPIClient

# Legacy clients (for backwards compatibility)
try:
    from backend.integrations.facebook_client import FacebookAPIClient
    facebook_client = FacebookAPIClient()
except ImportError:
    facebook_client = None

try:
    from backend.integrations.instagram_client import InstagramClient  
    instagram_client = InstagramClient()
except ImportError:
    instagram_client = None

try:
    from backend.integrations.twitter_client import twitter_client
except ImportError:
    twitter_client = None


__all__ = [
    'meta_client',
    'MetaGraphAPIClient', 
    'facebook_client',
    'instagram_client', 
    'twitter_client'
]