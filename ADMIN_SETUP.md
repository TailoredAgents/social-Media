# Admin System Setup Guide

This guide explains how to set up and use the comprehensive admin system for AI Social Media Manager platform.

## Overview

The admin system provides a separate administrative interface with the following features:

- **Separate Admin Authentication**: Dedicated admin login system with enhanced security
- **User Management**: View, manage, and control user accounts
- **API Key Generation**: Generate and manage API keys for users
- **Registration Key Management**: Optional invite-only registration with admin-generated keys
- **Role-Based Access Control**: Support for SUPER_ADMIN, ADMIN, MODERATOR, and SUPPORT roles
- **Audit Logging**: Track all administrative actions
- **System Settings**: Configure platform-wide settings
- **Two-Factor Authentication Support**: Enhanced security for admin accounts

## Components Created

### Backend Components
- `backend/db/admin_models.py` - Admin database models (AdminUser, AdminSession, etc.)
- `backend/auth/admin_auth.py` - Admin authentication system with JWT and security features
- `backend/api/admin.py` - Admin API endpoints for user management and system administration
- `scripts/create_super_admin.py` - Script to create the first super admin user

### Frontend Components
- `frontend/src/pages/admin/AdminLogin.jsx` - Admin login page
- `frontend/src/pages/admin/AdminDashboard.jsx` - Comprehensive admin dashboard
- `frontend/src/pages/admin/UserManagement.jsx` - User management interface
- `frontend/src/contexts/AdminAuthContext.jsx` - Admin authentication context
- `frontend/src/components/AdminLayout.jsx` - Admin panel layout
- `frontend/src/components/AdminProtectedRoute.jsx` - Admin route protection

### Database Migration
- `alembic/versions/013_add_admin_system.py` - Creates all admin system tables

## Setup Instructions

### 1. Run Database Migrations
```bash
# Apply the admin system migration
alembic upgrade head
```

### 2. Create Your First Super Admin
```bash
# Run the super admin creation script
python scripts/create_super_admin.py

# Follow the prompts to enter:
# - Email address
# - Username  
# - Full name (optional)
# - Password (minimum 8 characters)
```

### 3. Access Admin Panel
- Navigate to `/admin/login` in your browser
- Login with the super admin credentials you created
- You'll be redirected to the admin dashboard at `/admin/dashboard`

### 4. User Registration Options
The platform supports **open SaaS registration** - users can sign up directly without registration keys.

**Optional Registration Control**: If you want to restrict registration, you can:
- Enable email verification in settings
- Use registration keys for invite-only access (optional feature)
- Configure email domain restrictions

The system is configured for open registration by default. Users can sign up at `/register` on the frontend.

## Admin Routes

- `/admin/login` - Admin login page
- `/admin/dashboard` - Main admin dashboard with system statistics
- `/admin/users` - User management interface
- `/admin/settings` - System settings (coming soon)
- `/admin/audit-logs` - Audit log viewer (coming soon)
- `/admin/api-keys` - API key management (coming soon)
- `/admin/admin-users` - Admin user management (super admin only)

## Admin Features

### User Management
- View all registered users
- Search and filter users by status
- Generate API keys for users
- Revoke API keys
- Suspend/activate user accounts
- Mark users as verified
- View user statistics and activity

### API Key Management
- Generate secure API keys for users
- Track API key usage
- Revoke API keys with reason logging
- Monitor API usage statistics

### Registration Key Management (Optional)
- Create secure registration keys for invite-only access (when enabled)
- Set usage limits (single-use or multi-use keys)
- Add email domain restrictions (@company.com only)
- Set expiration dates for time-limited access
- Track which users registered with each key
- Deactivate or delete unused keys
- Note: By default, open registration is enabled and keys are not required

### Security Features
- Separate JWT tokens for admin authentication (shorter lifespan)
- Progressive lockout after failed login attempts
- Session tracking with IP address and user agent
- Two-factor authentication support (TOTP)
- Comprehensive audit logging
- Role-based permissions

### Dashboard Statistics
- Total users and active users
- New registrations
- Content creation metrics
- API usage statistics
- Failed login attempts
- System health status

## Admin Roles

1. **SUPER_ADMIN**: Full system access, can manage other admin users
2. **ADMIN**: User management and system settings
3. **MODERATOR**: Content moderation and user suspension
4. **SUPPORT**: Read-only access for customer support

## Security Considerations

- Admin tokens expire in 30 minutes (shorter than user tokens)
- All admin actions are logged in audit_logs table
- Admin sessions are tracked separately from user sessions
- Rate limiting and progressive lockout for failed login attempts
- Two-factor authentication recommended for super admins

## API Endpoints

The admin system provides these API endpoints:

- `POST /api/admin/auth/login` - Admin login
- `POST /api/admin/auth/logout` - Admin logout
- `GET /api/admin/auth/me` - Get admin profile
- `GET /api/admin/dashboard` - Dashboard statistics
- `GET /api/admin/users` - List users
- `GET /api/admin/users/{id}` - Get user details
- `POST /api/admin/users/{id}/api-key` - Generate API key
- `DELETE /api/admin/users/{id}/api-key` - Revoke API key
- `PUT /api/admin/users/{id}/management` - Update user status
- `POST /api/admin/registration-keys` - Create registration key
- `GET /api/admin/registration-keys` - List registration keys
- `PUT /api/admin/registration-keys/{id}/deactivate` - Deactivate key
- `DELETE /api/admin/registration-keys/{id}` - Delete unused key

## Development Notes

- The admin system uses a separate authentication context from regular users
- Admin routes are protected with `AdminProtectedRoute` component
- Database models support soft deletes and audit trails
- All admin API calls include request ID tracking for debugging

## Next Steps

To extend the admin system, you can:

1. Add more admin pages (settings, audit logs, analytics)
2. Implement email notifications for admin actions
3. Add bulk user operations
4. Create admin dashboard widgets
5. Implement content moderation tools
6. Add system monitoring and alerts

## Troubleshooting

If you encounter issues:

1. Ensure all database migrations have been applied
2. Check that the super admin user was created successfully
3. Verify admin API endpoints are registered in the router
4. Check browser console for any JavaScript errors
5. Review server logs for authentication errors

The admin system is now fully integrated and ready for use!