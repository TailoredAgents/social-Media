"""
Social Media OAuth Authentication Flow
Integration Specialist Component - Handles OAuth flows for all supported platforms
"""
import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import hashlib
import base64

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.models import User, UserSetting

settings = get_settings()
logger = logging.getLogger(__name__)

class SocialOAuthManager:
    """
    Comprehensive OAuth manager for all social media platforms
    
    Supported Platforms:
    - Twitter (OAuth 2.0 with PKCE)
    - Instagram (Facebook OAuth)
    - Facebook (OAuth 2.0)
    - TikTok (OAuth 2.0)
    """
    
    def __init__(self):
        """Initialize OAuth manager with platform configurations"""
        self.platform_configs = {
            "twitter": {
                "client_id": settings.twitter_client_id,
                "client_secret": settings.twitter_client_secret,
                "auth_url": "https://twitter.com/i/oauth2/authorize",
                "token_url": "https://api.twitter.com/2/oauth2/token",
                "scope": "tweet.read tweet.write users.read follows.read follows.write offline.access",
                "requires_pkce": True,
                "api_base": "https://api.twitter.com/2"
            },
            "instagram": {
                "client_id": settings.facebook_app_id,  # Instagram uses Facebook OAuth
                "client_secret": settings.facebook_app_secret,
                "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
                "scope": "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement",
                "requires_pkce": False,
                "api_base": "https://graph.facebook.com/v18.0"
            },
            "facebook": {
                "client_id": settings.facebook_app_id,
                "client_secret": settings.facebook_app_secret,
                "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
                "scope": "pages_manage_posts,pages_read_engagement,publish_to_groups",
                "requires_pkce": False,
                "api_base": "https://graph.facebook.com/v18.0"
            }
        }
        
        # OAuth state storage (in production, use Redis or database)
        self.oauth_states = {}
        
        # Token storage and management
        self.token_refresh_threshold = 300  # Refresh if expires in 5 minutes
        
        logger.info("SocialOAuthManager initialized with support for 4 platforms")
    
    def generate_oauth_state(self, user_id: int, platform: str) -> str:
        """
        Generate secure OAuth state parameter
        
        Args:
            user_id: User ID for associating the OAuth flow
            platform: Target social media platform
            
        Returns:
            Secure state string
        """
        state_data = {
            "user_id": user_id,
            "platform": platform,
            "timestamp": int(time.time()),
            "nonce": secrets.token_urlsafe(16)
        }
        
        # Create state string
        state_json = json.dumps(state_data)
        state_bytes = state_json.encode('utf-8')
        state_b64 = base64.urlsafe_b64encode(state_bytes).decode('utf-8')
        
        # Store state temporarily (expires in 10 minutes)
        self.oauth_states[state_b64] = {
            **state_data,
            "expires_at": time.time() + 600
        }
        
        return state_b64
    
    def validate_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Validate OAuth state parameter
        
        Args:
            state: State string from OAuth callback
            
        Returns:
            State data if valid, None otherwise
        """
        try:
            if state not in self.oauth_states:
                return None
            
            state_data = self.oauth_states[state]
            
            # Check expiration
            if time.time() > state_data["expires_at"]:
                del self.oauth_states[state]
                return None
            
            # Remove from storage after use
            del self.oauth_states[state]
            
            return state_data
            
        except Exception as e:
            logger.error(f"Error validating OAuth state: {e}")
            return None
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for OAuth 2.0
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def build_authorization_url(
        self,
        platform: str,
        user_id: int,
        redirect_uri: str,
        additional_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Build authorization URL for OAuth flow
        
        Args:
            platform: Target social media platform
            user_id: User ID for state management
            redirect_uri: OAuth callback URL
            additional_params: Additional OAuth parameters
            
        Returns:
            Dictionary with auth_url and state information
        """
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.platform_configs[platform]
        
        # Generate state
        state = self.generate_oauth_state(user_id, platform)
        
        # Base OAuth parameters
        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": config["scope"],
            "state": state,
            "response_type": "code"
        }
        
        # Add PKCE parameters if required
        pkce_data = None
        if config["requires_pkce"]:
            code_verifier, code_challenge = self.generate_pkce_pair()
            params.update({
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            })
            
            # Store code verifier with state
            self.oauth_states[state] = {
                **self.oauth_states[state],
                "code_verifier": code_verifier
            }
            
            pkce_data = {
                "code_verifier": code_verifier,
                "code_challenge": code_challenge
            }
        
        # Add additional parameters
        if additional_params:
            params.update(additional_params)
        
        # Build URL
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL for {platform} (user: {user_id})")
        
        return {
            "auth_url": auth_url,
            "state": state,
            "platform": platform,
            "pkce_data": pkce_data
        }
    
    async def exchange_code_for_tokens(
        self,
        platform: str,
        authorization_code: str,
        redirect_uri: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens
        
        Args:
            platform: Social media platform
            authorization_code: OAuth authorization code
            redirect_uri: OAuth callback URL
            state: OAuth state parameter
            
        Returns:
            Token information including access_token, refresh_token, etc.
        """
        # Validate state
        state_data = self.validate_oauth_state(state)
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
        if state_data["platform"] != platform:
            raise HTTPException(status_code=400, detail="Platform mismatch in OAuth state")
        
        config = self.platform_configs[platform]
        
        # Prepare token exchange request
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # Add PKCE code verifier if required
        if config["requires_pkce"] and "code_verifier" in state_data:
            token_data["code_verifier"] = state_data["code_verifier"]
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config["token_url"],
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed for {platform}: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token exchange failed: {response.text}"
                    )
                
                token_response = response.json()
                
                # Standardize token response format
                standardized_tokens = {
                    "access_token": token_response.get("access_token"),
                    "token_type": token_response.get("token_type", "Bearer"),
                    "expires_in": token_response.get("expires_in"),
                    "refresh_token": token_response.get("refresh_token"),
                    "scope": token_response.get("scope"),
                    "platform": platform,
                    "user_id": state_data["user_id"],
                    "obtained_at": datetime.utcnow().isoformat(),
                    "raw_response": token_response
                }
                
                # Calculate expiration time
                if standardized_tokens["expires_in"]:
                    expires_at = datetime.utcnow() + timedelta(seconds=int(standardized_tokens["expires_in"]))
                    standardized_tokens["expires_at"] = expires_at.isoformat()
                
                logger.info(f"Successfully obtained tokens for {platform} (user: {state_data['user_id']})")
                
                return standardized_tokens
                
            except httpx.RequestError as e:
                logger.error(f"HTTP error during token exchange for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Network error during token exchange")
            except Exception as e:
                logger.error(f"Unexpected error during token exchange for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Token exchange failed")
    
    async def refresh_access_token(
        self,
        platform: str,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            platform: Social media platform
            refresh_token: Refresh token
            
        Returns:
            New token information
        """
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.platform_configs[platform]
        
        # Prepare refresh request
        refresh_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config["token_url"],
                    data=refresh_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed for {platform}: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Token refresh failed: {response.text}"
                    )
                
                token_response = response.json()
                
                # Standardize response
                refreshed_tokens = {
                    "access_token": token_response.get("access_token"),
                    "token_type": token_response.get("token_type", "Bearer"),
                    "expires_in": token_response.get("expires_in"),
                    "refresh_token": token_response.get("refresh_token", refresh_token),  # Keep old if not provided
                    "scope": token_response.get("scope"),
                    "platform": platform,
                    "refreshed_at": datetime.utcnow().isoformat(),
                    "raw_response": token_response
                }
                
                # Calculate new expiration
                if refreshed_tokens["expires_in"]:
                    expires_at = datetime.utcnow() + timedelta(seconds=int(refreshed_tokens["expires_in"]))
                    refreshed_tokens["expires_at"] = expires_at.isoformat()
                
                logger.info(f"Successfully refreshed tokens for {platform}")
                
                return refreshed_tokens
                
            except httpx.RequestError as e:
                logger.error(f"HTTP error during token refresh for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Network error during token refresh")
            except Exception as e:
                logger.error(f"Unexpected error during token refresh for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Token refresh failed")
    
    async def get_user_profile(
        self,
        platform: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user profile information from social media platform
        
        Args:
            platform: Social media platform
            access_token: Valid access token
            
        Returns:
            User profile information
        """
        if platform not in self.platform_configs:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.platform_configs[platform]
        
        # Platform-specific profile endpoints
        profile_endpoints = {
            "twitter": "/users/me",
            "linkedin": "/people/~",
            "instagram": "/me",
            "facebook": "/me"
        }
        
        endpoint = profile_endpoints.get(platform)
        if not endpoint:
            raise ValueError(f"Profile endpoint not configured for {platform}")
        
        url = f"{config['api_base']}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Profile fetch failed for {platform}: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch profile: {response.text}"
                    )
                
                profile_data = response.json()
                
                # Standardize profile format
                standardized_profile = {
                    "platform": platform,
                    "platform_user_id": self._extract_user_id(platform, profile_data),
                    "username": self._extract_username(platform, profile_data),
                    "display_name": self._extract_display_name(platform, profile_data),
                    "profile_image": self._extract_profile_image(platform, profile_data),
                    "follower_count": self._extract_follower_count(platform, profile_data),
                    "verified": self._extract_verified_status(platform, profile_data),
                    "raw_profile": profile_data,
                    "fetched_at": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Successfully fetched profile for {platform}")
                
                return standardized_profile
                
            except httpx.RequestError as e:
                logger.error(f"HTTP error during profile fetch for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Network error during profile fetch")
            except Exception as e:
                logger.error(f"Unexpected error during profile fetch for {platform}: {e}")
                raise HTTPException(status_code=500, detail="Profile fetch failed")
    
    def _extract_user_id(self, platform: str, profile_data: Dict) -> str:
        """Extract user ID from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("id") or d.get("id"),
            "linkedin": lambda d: d.get("id"),
            "instagram": lambda d: d.get("id"),
            "facebook": lambda d: d.get("id")
        }
        return str(extractors.get(platform, lambda d: None)(profile_data) or "")
    
    def _extract_username(self, platform: str, profile_data: Dict) -> str:
        """Extract username from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("username") or d.get("username"),
            "linkedin": lambda d: d.get("localizedLastName", ""),  # LinkedIn doesn't have usernames
            "instagram": lambda d: d.get("username"),
            "facebook": lambda d: d.get("name")  # Facebook uses name instead of username
        }
        return extractors.get(platform, lambda d: "")(profile_data) or ""
    
    def _extract_display_name(self, platform: str, profile_data: Dict) -> str:
        """Extract display name from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("name") or d.get("name"),
            "linkedin": lambda d: f"{d.get('localizedFirstName', '')} {d.get('localizedLastName', '')}".strip(),
            "instagram": lambda d: d.get("name"),
            "facebook": lambda d: d.get("name")
        }
        return extractors.get(platform, lambda d: "")(profile_data) or ""
    
    def _extract_profile_image(self, platform: str, profile_data: Dict) -> str:
        """Extract profile image URL from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("profile_image_url") or d.get("profile_image_url"),
            "linkedin": lambda d: d.get("profilePicture", {}).get("displayImage"),
            "instagram": lambda d: d.get("profile_picture_url"),
            "facebook": lambda d: d.get("picture", {}).get("data", {}).get("url")
        }
        return extractors.get(platform, lambda d: "")(profile_data) or ""
    
    def _extract_follower_count(self, platform: str, profile_data: Dict) -> int:
        """Extract follower count from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("public_metrics", {}).get("followers_count", 0),
            "linkedin": lambda d: 0,  # LinkedIn API doesn't provide follower count in basic profile
            "instagram": lambda d: d.get("followers_count", 0),
            "facebook": lambda d: 0  # Facebook doesn't provide follower count in basic profile
        }
        return extractors.get(platform, lambda d: 0)(profile_data) or 0
    
    def _extract_verified_status(self, platform: str, profile_data: Dict) -> bool:
        """Extract verified status from platform-specific profile data"""
        extractors = {
            "twitter": lambda d: d.get("data", {}).get("verified", False) or d.get("verified", False),
            "linkedin": lambda d: False,  # LinkedIn doesn't have public verification status
            "instagram": lambda d: d.get("is_verified", False),
            "facebook": lambda d: d.get("verified", False)
        }
        return extractors.get(platform, lambda d: False)(profile_data) or False
    
    async def store_user_tokens(
        self,
        user_id: int,
        platform: str,
        token_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        Store user OAuth tokens and profile data in database
        
        Args:
            user_id: User ID
            platform: Social media platform
            token_data: OAuth token information
            profile_data: User profile data
            db: Database session
            
        Returns:
            Success status
        """
        try:
            # Get user settings
            user_settings = db.query(UserSetting).filter(
                UserSetting.user_id == user_id
            ).first()
            
            if not user_settings:
                # Create user settings if doesn't exist
                user_settings = UserSetting(user_id=user_id)
                db.add(user_settings)
            
            # Update connected accounts
            if not user_settings.connected_accounts:
                user_settings.connected_accounts = {}
            
            # Store platform connection data
            user_settings.connected_accounts[platform] = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_at": token_data.get("expires_at"),
                "scope": token_data.get("scope"),
                "platform_user_id": profile_data.get("platform_user_id"),
                "username": profile_data.get("username"),
                "display_name": profile_data.get("display_name"),
                "profile_image": profile_data.get("profile_image"),
                "follower_count": profile_data.get("follower_count", 0),
                "verified": profile_data.get("verified", False),
                "connected_at": datetime.utcnow().isoformat(),
                "last_refreshed": None
            }
            
            db.commit()
            
            logger.info(f"Successfully stored tokens for {platform} (user: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing user tokens: {e}")
            db.rollback()
            return False
    
    async def get_valid_token(
        self,
        user_id: int,
        platform: str,
        db: Session
    ) -> Optional[str]:
        """
        Get valid access token for user and platform, refreshing if necessary
        
        Args:
            user_id: User ID
            platform: Social media platform
            db: Database session
            
        Returns:
            Valid access token or None
        """
        try:
            # Get user settings
            user_settings = db.query(UserSetting).filter(
                UserSetting.user_id == user_id
            ).first()
            
            if not user_settings or not user_settings.connected_accounts:
                return None
            
            account_data = user_settings.connected_accounts.get(platform)
            if not account_data:
                return None
            
            access_token = account_data.get("access_token")
            expires_at_str = account_data.get("expires_at")
            refresh_token = account_data.get("refresh_token")
            
            if not access_token:
                return None
            
            # Check if token needs refresh
            if expires_at_str and refresh_token:
                expires_at = datetime.fromisoformat(expires_at_str)
                time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()
                
                # Refresh if expiring within threshold
                if time_until_expiry < self.token_refresh_threshold:
                    try:
                        new_tokens = await self.refresh_access_token(platform, refresh_token)
                        
                        # Update stored tokens
                        account_data.update({
                            "access_token": new_tokens["access_token"],
                            "refresh_token": new_tokens.get("refresh_token", refresh_token),
                            "expires_at": new_tokens.get("expires_at"),
                            "last_refreshed": datetime.utcnow().isoformat()
                        })
                        
                        user_settings.connected_accounts[platform] = account_data
                        db.commit()
                        
                        access_token = new_tokens["access_token"]
                        logger.info(f"Refreshed token for {platform} (user: {user_id})")
                        
                    except Exception as e:
                        logger.error(f"Failed to refresh token for {platform} (user: {user_id}): {e}")
                        return None
            
            return access_token
            
        except Exception as e:
            logger.error(f"Error getting valid token: {e}")
            return None
    
    def disconnect_platform(
        self,
        user_id: int,
        platform: str,
        db: Session
    ) -> bool:
        """
        Disconnect user from social media platform
        
        Args:
            user_id: User ID
            platform: Social media platform
            db: Database session
            
        Returns:
            Success status
        """
        try:
            user_settings = db.query(UserSetting).filter(
                UserSetting.user_id == user_id
            ).first()
            
            if not user_settings or not user_settings.connected_accounts:
                return False
            
            if platform in user_settings.connected_accounts:
                del user_settings.connected_accounts[platform]
                db.commit()
                
                logger.info(f"Disconnected {platform} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error disconnecting platform: {e}")
            db.rollback()
            return False
    
    async def get_user_access_token(
        self,
        user_id: int,
        platform: str
    ) -> Optional[str]:
        """
        Get user's access token for a platform (async wrapper for get_valid_token)
        
        Args:
            user_id: User ID
            platform: Social media platform
            
        Returns:
            Access token or None if not found
        """
        try:
            from backend.db.database import get_db
            
            # Get database session
            db_generator = get_db()
            db = next(db_generator)
            
            try:
                return await self.get_valid_token(user_id, platform, db)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting user access token: {e}")
            return None

# Global OAuth manager instance
oauth_manager = SocialOAuthManager()