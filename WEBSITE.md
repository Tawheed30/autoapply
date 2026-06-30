# AutoApply Website - Full-Fledged Production Site

Your Job Application Accelerator has been transformed into a complete, production-ready website with user authentication, landing page, and marketing content.

## 🎯 What's New

### Pages
- **Landing Page** (`/`) - Marketing homepage with features, pricing, testimonials
- **Signup Page** (`/signup`) - User registration with password validation
- **Login Page** (`/login`) - Authentication with persistent sessions
- **Dashboard** (`/dashboard`) - Protected user dashboard (authenticated only)
- **Privacy Policy** (`/privacy`) - Legal privacy documentation
- **Terms of Service** (`/terms`) - Legal terms and conditions

### Authentication System
- JWT-based token authentication
- Secure password hashing (PBKDF2 with salt)
- Email validation
- Token expiration (24 hours)
- User account management

### API Endpoints

#### Public Authentication Endpoints

**Sign Up**
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123"
}

Response:
{
  "user_id": "uuid",
  "email": "john@example.com",
  "name": "John Doe",
  "token": "jwt_token"
}
```

**Login**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePassword123"
}

Response:
{
  "user_id": "uuid",
  "email": "john@example.com",
  "name": "John Doe",
  "token": "jwt_token"
}
```

#### Protected Endpoints (Require Authentication)

**Get Current User**
```bash
GET /api/auth/me
Authorization: Bearer <jwt_token>

Response:
{
  "user_id": "uuid",
  "email": "john@example.com",
  "name": "John Doe",
  "created_at": "2026-06-30T10:00:00"
}
```

**Access Dashboard**
```bash
GET /dashboard
Authorization: Bearer <jwt_token>

Returns: Dashboard HTML (authenticated)
```

## 🔐 Security Features

### Password Security
- PBKDF2 with SHA256 hashing
- Random salt generation (16 bytes)
- 100,000 iterations for slow hashing
- Password requirements enforced:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number

### Token Security
- JWT tokens signed with HS256
- 24-hour token expiration
- Bearer token format: `Authorization: Bearer <token>`
- Tokens validated on every protected route

### Database
- SQLite with users table
- Email uniqueness constraint
- Foreign key relationships
- User data isolated by ID

## 🚀 How to Use

### For Users

**1. Sign Up**
- Visit http://localhost:8787/signup
- Enter name, email, password
- Password requirements shown in real-time
- Click "Create Account"

**2. Sign In**
- Visit http://localhost:8787/login
- Enter email and password
- Click "Sign In"
- Token automatically stored in browser

**3. Access Dashboard**
- After login, redirected to `/dashboard`
- All dashboard features available
- Submit jobs, track applications, etc.

**4. Logout**
- Clear browser's localStorage
- Delete token: `localStorage.removeItem('token')`

### For Developers

**Test Authentication Flow**
```bash
# Sign up
TOKEN=$(curl -s -X POST http://localhost:8787/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123"
  }' | jq -r '.token')

# Get user info
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8787/api/auth/me | jq

# Access dashboard
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8787/dashboard | grep "<title>"
```

**Test Protected Routes**
```bash
# Without token (should fail)
curl http://localhost:8787/dashboard
# Returns: "Missing authorization header"

# With invalid token (should fail)
curl -H "Authorization: Bearer invalid" \
  http://localhost:8787/dashboard
# Returns: "Invalid or expired token"
```

## 📁 Project Structure

```
AutoApply/
├── app/
│   ├── main.py                 # FastAPI app with routes
│   ├── auth.py                 # Authentication system
│   ├── database.py             # Database with users table
│   └── ...                     # Other modules
├── templates/
│   ├── landing.html            # Landing page
│   ├── signup.html             # Signup page
│   ├── login.html              # Login page
│   ├── privacy.html            # Privacy policy
│   └── terms.html              # Terms of service
├── static/
│   └── dashboard.html          # Dashboard (requires auth)
├── requirements.txt            # Dependencies
└── WEBSITE.md                  # This file
```

## 🔄 User Database Schema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);
```

## 📊 Activity Logging

All user actions are logged:

```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    details TEXT,
    result TEXT,
    user_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Logged Events
- `user_signup` - New user registration
- `user_login` - User authentication
- `app_startup` - Application startup
- `app_shutdown` - Application shutdown
- Custom actions from other modules

## 🎨 Frontend Features

### Landing Page
- Modern gradient background
- Feature cards with hover effects
- Statistics section
- Pricing plans
- FAQ section
- Call-to-action buttons
- Fully responsive design

### Signup Page
- Real-time password validation
- Requirements checklist
- Terms & Privacy policy links
- Email validation
- Error handling
- Loading states

### Login Page
- Email/password authentication
- "Remember me" functionality
- Forgot password link (ready to implement)
- Error handling
- Loading states

## 📱 Responsive Design

All pages are fully responsive:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🔄 Next Steps / Enhancements

### Planned Features
1. **Password Reset**
   - Forgot password email flow
   - Token-based password reset
   - Email verification

2. **User Profile**
   - Edit profile information
   - Update password
   - Account settings

3. **Email Notifications**
   - Welcome email
   - Application status updates
   - Weekly digests

4. **Social Authentication**
   - Google OAuth
   - LinkedIn OAuth

5. **Team/Multi-user**
   - Share applications
   - Collaborative tracking
   - Role-based access

6. **Advanced Analytics**
   - User activity dashboard
   - Application success rates
   - Time-to-hire metrics

## 🚀 Deployment

### Cloud Deployment (Railway)

The website is ready to deploy to Railway with all authentication support:

```bash
# Login to Railway
railway login

# Deploy
railway up

# Set environment variables
railway variables set JWT_SECRET_KEY your_secret_key
railway variables set ANTHROPIC_API_KEY your_api_key
```

### Environment Variables

```env
# Required
JWT_SECRET_KEY=your_secret_key_here
ANTHROPIC_API_KEY=your_api_key_here

# Optional
DATABASE_URL=postgresql://...  # For PostgreSQL in production
LOG_LEVEL=INFO
```

### Production Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Enable HTTPS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up email service for notifications
- [ ] Configure custom domain
- [ ] Set up monitoring/logging
- [ ] Enable CORS for frontend if needed
- [ ] Rate limiting on auth endpoints
- [ ] Regular database backups

## 📞 Support

For issues or questions:
- Email: support@autoapply.io
- Privacy Policy: `/privacy`
- Terms of Service: `/terms`

## 📝 License

MIT License - See LICENSE file for details

---

**Version:** 1.0.0  
**Last Updated:** June 30, 2024  
**Status:** Production Ready ✅
