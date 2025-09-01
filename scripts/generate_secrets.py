#!/usr/bin/env python3
import secrets
import string

def generate_secure_key(length=32):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=64):
    return secrets.token_urlsafe(length)

print("Generating Secure Production Secrets")
print("=" * 50)
print()

# Generate all required secrets
secret_key = generate_secure_key(32)
jwt_secret = generate_jwt_secret(64)
admin_jwt_secret = generate_jwt_secret(64)

print("Copy these to your Render Environment Variables:")
print()
print("SECRET_KEY=" + secret_key)
print("JWT_SECRET=" + jwt_secret)
print("ADMIN_JWT_SECRET=" + admin_jwt_secret)
print()
print("IMPORTANT SECURITY NOTES:")
print("1. Never commit these secrets to your repository")
print("2. Store them securely in Render environment variables")
print("3. Use different secrets for each environment")
print("4. These secrets are shown only once - save them now!")
print()
print("Database URL will be provided automatically by Render")
print("when you connect your PostgreSQL database.")