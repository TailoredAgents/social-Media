"""
Two-Factor Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.db.database import get_db
from backend.db.models import User
from backend.auth.dependencies import get_current_active_user
from backend.auth.jwt_handler import jwt_handler
from backend.auth.two_factor import two_factor_service
from backend.schemas.two_factor import (
    Enable2FARequest, Setup2FAResponse, Verify2FASetupRequest,
    Disable2FARequest, TwoFactorStatusResponse, RegenerateBackupCodesRequest,
    RegenerateBackupCodesResponse
)

router = APIRouter(prefix="/api/2fa", tags=["two-factor-authentication"])


@router.get("/status", response_model=TwoFactorStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current 2FA status for the user"""
    backup_codes_remaining = None
    
    if current_user.two_factor_enabled and current_user.two_factor_backup_codes:
        backup_codes_remaining = len(current_user.two_factor_backup_codes)
    
    return TwoFactorStatusResponse(
        enabled=current_user.two_factor_enabled or False,
        backup_codes_remaining=backup_codes_remaining
    )


@router.post("/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    request: Enable2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Initiate 2FA setup - generate QR code and backup codes
    This doesn't enable 2FA until verification is completed
    """
    # Verify current password
    if not jwt_handler.verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Check if 2FA is already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Generate new TOTP secret
    secret = two_factor_service.generate_secret()
    
    # Generate QR code
    qr_code = two_factor_service.generate_qr_code(current_user.email, secret)
    
    # Generate backup codes
    backup_codes = two_factor_service.generate_backup_codes()
    
    # Store temporarily encrypted secret (not yet enabled)
    # We'll use a temporary field or session storage
    encrypted_secret = two_factor_service.encrypt_secret(secret)
    
    # For now, store in user record but don't enable yet
    current_user.two_factor_secret = encrypted_secret
    hashed_backup_codes = [
        two_factor_service.hash_backup_code(code) for code in backup_codes
    ]
    current_user.two_factor_backup_codes = hashed_backup_codes
    
    db.commit()
    
    return Setup2FAResponse(
        qr_code=qr_code,
        manual_entry_key=secret,
        backup_codes=backup_codes
    )


@router.post("/verify-setup")
async def verify_2fa_setup(
    request: Verify2FASetupRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify TOTP code and enable 2FA"""
    # Check if setup was initiated
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Please start setup first."
        )
    
    # Check if already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Decrypt secret and verify token
    try:
        secret = two_factor_service.decrypt_secret(current_user.two_factor_secret)
        if not two_factor_service.verify_token(secret, request.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    current_user.two_factor_enabled = True
    db.commit()
    
    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/disable")
async def disable_2fa(
    request: Disable2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for the user"""
    # Check if 2FA is enabled
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify current password
    if not jwt_handler.verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Verify either TOTP code or backup code
    verification_valid = False
    
    try:
        # Try TOTP verification first
        if current_user.two_factor_secret:
            secret = two_factor_service.decrypt_secret(current_user.two_factor_secret)
            if two_factor_service.verify_token(secret, request.verification_code):
                verification_valid = True
    except Exception:
        pass
    
    # If TOTP failed, try backup code
    if not verification_valid and current_user.two_factor_backup_codes:
        is_valid, _ = two_factor_service.verify_backup_code(
            request.verification_code, current_user.two_factor_backup_codes
        )
        verification_valid = is_valid
    
    if not verification_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Disable 2FA and clear secrets
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = None
    
    db.commit()
    
    return {"message": "Two-factor authentication disabled successfully"}


@router.post("/regenerate-backup-codes", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    request: RegenerateBackupCodesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate backup codes for 2FA"""
    # Check if 2FA is enabled
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify current password
    if not jwt_handler.verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Verify TOTP code
    try:
        secret = two_factor_service.decrypt_secret(current_user.two_factor_secret)
        if not two_factor_service.verify_token(secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    # Generate new backup codes
    new_backup_codes = two_factor_service.generate_backup_codes()
    hashed_backup_codes = [
        two_factor_service.hash_backup_code(code) for code in new_backup_codes
    ]
    
    # Update user record
    current_user.two_factor_backup_codes = hashed_backup_codes
    db.commit()
    
    return RegenerateBackupCodesResponse(backup_codes=new_backup_codes)


@router.post("/verify")
async def verify_2fa_code(
    token: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Utility endpoint to verify a 2FA code
    Useful for sensitive operations that require 2FA verification
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    try:
        secret = two_factor_service.decrypt_secret(current_user.two_factor_secret)
        if not two_factor_service.verify_token(secret, token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    return {"message": "Code verified successfully"}