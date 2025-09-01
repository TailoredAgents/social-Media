"""
Production Environment Validation for Security
Validates required environment variables and security configurations
"""
import os
import secrets
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityConfigError(Exception):
    """Raised when security configuration is invalid"""
    pass

def validate_environment() -> Dict[str, any]:
    """
    Validate all required environment variables for production deployment
    Returns validation results and recommendations
    """
    validation_results = {
        'validation_passed': True,
        'errors': [],
        'warnings': [],
        'recommendations': [],
        'validated_vars': {},
        'configuration_completeness': 0
    }
    
    # Required environment variables
    required_vars = {
        'SECRET_KEY': {
            'description': 'JWT and session encryption key',
            'min_length': 32,
            'secure': True
        },
        'DATABASE_URL': {
            'description': 'PostgreSQL database connection string',
            'min_length': 20,
            'secure': False
        },
        'OPENAI_API_KEY': {
            'description': 'OpenAI API key for content generation',
            'min_length': 20,
            'secure': True
        }
    }
    
    # Optional but recommended variables
    optional_vars = {
        'SERPER_API_KEY': {
            'description': 'Serper API key for research',
            'min_length': 20,
            'secure': True
        },
        'SENTRY_DSN': {
            'description': 'Sentry error tracking DSN',
            'min_length': 30,
            'secure': False
        },
        'REDIS_URL': {
            'description': 'Redis connection for Celery',
            'min_length': 10,
            'secure': False
        },
        'CELERY_BROKER_URL': {
            'description': 'Celery message broker URL',
            'min_length': 10,
            'secure': False
        }
    }
    
    # Validate required variables
    for var_name, config in required_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            validation_results['validation_passed'] = False
            validation_results['errors'].append(
                f"Missing required environment variable: {var_name} - {config['description']}"
            )
        elif len(value) < config['min_length']:
            validation_results['validation_passed'] = False
            validation_results['errors'].append(
                f"Environment variable {var_name} is too short (minimum {config['min_length']} characters)"
            )
        else:
            # Mark as validated (don't store secure values)
            if config['secure']:
                validation_results['validated_vars'][var_name] = f"***{value[-4:]}"
            else:
                validation_results['validated_vars'][var_name] = value[:50] + "..." if len(value) > 50 else value
    
    # Check optional variables
    for var_name, config in optional_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            validation_results['warnings'].append(
                f"Optional variable not set: {var_name} - {config['description']}"
            )
        elif len(value) < config['min_length']:
            validation_results['warnings'].append(
                f"Optional variable {var_name} seems too short (expected min {config['min_length']} characters)"
            )
        else:
            if config['secure']:
                validation_results['validated_vars'][var_name] = f"***{value[-4:]}"
            else:
                validation_results['validated_vars'][var_name] = value[:50] + "..." if len(value) > 50 else value
    
    # Security-specific validations
    _validate_secret_key_security(validation_results)
    _validate_database_security(validation_results)
    _validate_deployment_environment(validation_results)
    
    # Calculate completeness
    total_vars = len(required_vars) + len(optional_vars)
    valid_vars = len(validation_results['validated_vars'])
    validation_results['configuration_completeness'] = int((valid_vars / total_vars) * 100)
    
    return validation_results

def _validate_secret_key_security(results: Dict[str, any]):
    """Validate SECRET_KEY security requirements"""
    secret_key = os.getenv('SECRET_KEY')
    
    if not secret_key:
        return  # Already handled in main validation
    
    # Check if it's obviously insecure
    insecure_patterns = [
        'test', 'dev', 'development', 'secret', 'password',
        '123', 'abc', 'changeme', 'default'
    ]
    
    if any(pattern in secret_key.lower() for pattern in insecure_patterns):
        results['validation_passed'] = False
        results['errors'].append(
            "SECRET_KEY appears to contain insecure patterns. Use a cryptographically random key."
        )
    
    # Check entropy (basic check)
    if len(set(secret_key)) < 10:
        results['warnings'].append(
            "SECRET_KEY has low character diversity. Consider using more random characters."
        )
    
    if len(secret_key) < 64:
        results['recommendations'].append(
            "Consider using a longer SECRET_KEY (64+ characters) for enhanced security"
        )

def _validate_database_security(results: Dict[str, any]):
    """Validate database connection security"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        return
    
    # Check for insecure database configurations
    if 'localhost' in database_url or '127.0.0.1' in database_url:
        results['warnings'].append(
            "Database URL points to localhost - ensure this is intentional for your deployment"
        )
    
    if 'password=password' in database_url or 'password=123' in database_url:
        results['validation_passed'] = False
        results['errors'].append(
            "Database uses an insecure default password"
        )
    
    if not database_url.startswith('postgresql://'):
        results['warnings'].append(
            "Database URL doesn't use PostgreSQL - ensure compatibility with pgvector extension"
        )

def _validate_deployment_environment(results: Dict[str, any]):
    """Validate deployment-specific environment settings"""
    
    # Check environment type
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    if environment in ['development', 'dev', 'test']:
        results['warnings'].append(
            f"Running in {environment} environment - ensure production settings for deployment"
        )
    
    # Check debug settings
    if os.getenv('DEBUG', '').lower() in ['true', '1', 'yes']:
        results['validation_passed'] = False
        results['errors'].append(
            "DEBUG is enabled - this must be disabled in production"
        )
    
    # Check CORS settings
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '')
    if '*' in allowed_origins:
        results['warnings'].append(
            "CORS allows all origins (*) - consider restricting to specific domains in production"
        )

def generate_secure_secret_key() -> str:
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(64)

def create_env_template() -> str:
    """Create a template .env file with all required variables"""
    template = """# AI Social Media Agent - Environment Configuration
# Copy this file to .env and fill in your actual values

# Core Security (REQUIRED)
SECRET_KEY=your_64_character_secret_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/aisocial

# AI Services (REQUIRED)  
OPENAI_API_KEY=sk-your_openai_api_key_here

# Research Services (OPTIONAL)
SERPER_API_KEY=your_serper_api_key_here

# Task Queue (OPTIONAL - required for autonomous mode)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Monitoring (OPTIONAL)
SENTRY_DSN=your_sentry_dsn_here

# Security Settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Social Platform APIs (for future use)
# TWITTER_API_KEY=
# TWITTER_API_SECRET=
# LINKEDIN_CLIENT_ID=
# LINKEDIN_CLIENT_SECRET=
"""
    return template

def validate_on_startup():
    """Validate environment on startup with enhanced reporting"""
    result = validate_environment()
    
    if not result["validation_passed"]:
        logger.error("🚨 Environment validation failed!")
        for error in result["errors"]:
            logger.error(f"  ❌ {error}")
        
        # Only warn, don't fail startup for now
        logger.warning("⚠️  Continuing with environment issues - fix before production deployment")
    else:
        logger.info("✅ Environment validation passed")
    
    if result["warnings"]:
        logger.warning(f"⚠️  Found {len(result['warnings'])} configuration warnings:")
        for warning in result["warnings"]:
            logger.warning(f"  • {warning}")
    
    logger.info(f"📊 Configuration completeness: {result['configuration_completeness']}%")

if __name__ == '__main__':
    # CLI usage for validation
    results = validate_environment()
    
    print("🔒 Environment Security Validation")
    print("=" * 50)
    
    if results['validation_passed']:
        print("✅ All required environment variables are valid")
    else:
        print("❌ Environment validation failed")
        
    if results['errors']:
        print("\n🚨 ERRORS:")
        for error in results['errors']:
            print(f"  • {error}")
    
    if results['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in results['warnings']:
            print(f"  • {warning}")
    
    if results['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
    
    if results['validated_vars']:
        print(f"\n✓ Validated Variables ({len(results['validated_vars'])}):")
        for var, value in results['validated_vars'].items():
            print(f"  • {var}: {value}")
    
    print(f"\n📊 Validation Summary:")
    print(f"  • Errors: {len(results['errors'])}")
    print(f"  • Warnings: {len(results['warnings'])}")
    print(f"  • Variables Validated: {len(results['validated_vars'])}")
    print(f"  • Configuration Completeness: {results['configuration_completeness']}%")