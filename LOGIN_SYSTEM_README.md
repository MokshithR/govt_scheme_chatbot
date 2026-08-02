# User Authentication System

## Overview
A professional login system has been implemented for the Government Voice Chatbot with modern, gradient-styled UI matching the chatbot's design aesthetic.

## Features Implemented

### 1. Login Page (`/login/`)
- **Professional gradient design** with blue theme
- Split layout with branding on left, form on right
- Username/email and password fields with icons
- "Remember me" checkbox
- Forgot password link (placeholder)
- Error message display
- Redirect to chatbot after successful login
- Auto-redirect if already logged in

### 2. Registration Page (`/register/`)
- **Modern card design** matching login aesthetics
- Username, email, password fields with validation
- Password confirmation
- Email uniqueness validation
- Username uniqueness validation
- Success message and redirect to login after registration
- Auto-redirect if already logged in

### 3. Logout Functionality
- Logout button in chatbot header (top right)
- Shows username when logged in
- Success message after logout
- Redirect to login page

### 4. Main Chatbot Integration
- User info displayed in header when authenticated
- Clean logout button with icon
- Responsive design

## URLs

```
/login/          - User login page
/register/       - User registration page
/logout/         - Logout endpoint
/                - Main chatbot (with user info if logged in)
```

## Usage

### For New Users
1. Navigate to `http://localhost:8000/register/`
2. Fill in username, email, and password
3. Click "Create Account"
4. Redirected to login page
5. Login with credentials
6. Access chatbot

### For Existing Users
1. Navigate to `http://localhost:8000/login/`
2. Enter username and password
3. Click "Login"
4. Access chatbot

### Logout
- Click the "Logout" button in the top-right corner of the chatbot header

## Technical Details

### Views Added (`chatbot/views.py`)
- `login_view()` - Handles login GET/POST requests
- `register_view()` - Handles registration with validation
- `logout_view()` - Handles logout and session clearing

### URLs Added (`chatbot/urls.py`)
```python
path('login/', views.login_view, name='login'),
path('register/', views.register_view, name='register'),
path('logout/', views.logout_view, name='logout'),
```

### Templates Created
- `chatbot/templates/chatbot/login.html` - Login page
- `chatbot/templates/chatbot/register.html` - Registration page
- Updated `chatbot/templates/chatbot/index.html` - Added user info display

### Styling
- **Login/Register Pages**: Split-screen gradient design with white form cards
- **Icons**: Font Awesome for user, lock, envelope, etc.
- **Responsive**: Mobile-friendly with Bootstrap 5
- **Theme**: Matches chatbot's purple-blue gradient aesthetic

## Optional Enhancements (Future)

You can add these features if needed:

1. **Protect Chatbot Route**: Require login to access chatbot
   ```python
   from django.contrib.auth.decorators import login_required
   
   @login_required(login_url='/login/')
   def index(request):
       return render(request, 'chatbot/index.html')
   ```

2. **Password Reset**: Implement forgot password functionality
3. **Email Verification**: Send verification emails on registration
4. **Social Login**: Add Google/Facebook OAuth
5. **User Profile**: Add profile page with settings
6. **Password Strength Indicator**: Real-time password strength meter

## Testing

### Create a Test User
```bash
python manage.py createsuperuser
```
Or use the register page.

### Test Login Flow
1. Start server: `python manage.py runserver`
2. Visit: `http://localhost:8000/login/`
3. Try invalid credentials (should show error)
4. Register new user at `/register/`
5. Login with new credentials
6. Verify username appears in chatbot header
7. Click logout and verify redirect

## Security Notes

- Passwords are hashed using Django's default PBKDF2 algorithm
- CSRF protection enabled on all forms
- Session-based authentication
- Messages framework for user feedback
- Input validation on registration

## Customization

### Change Colors
Edit the gradient colors in the `<style>` section of:
- `login.html` - Line 11-12 (background gradient)
- `register.html` - Line 11-12 (background gradient)

### Modify Login Requirements
Edit validation logic in `views.py`:
- `login_view()` - Add custom authentication logic
- `register_view()` - Add custom validation rules

## Troubleshooting

### "CSRF verification failed"
- Ensure `{% csrf_token %}` is in all forms
- Check Django settings for CSRF middleware

### "User already exists" error
- Use different username or email
- Or delete existing user via Django admin

### Logout doesn't work
- Check that `django.contrib.sessions` is in INSTALLED_APPS
- Verify `SessionMiddleware` is in MIDDLEWARE

## Summary

The authentication system is fully functional with:
✅ Professional UI design
✅ User registration with validation
✅ Secure login/logout
✅ Integration with main chatbot
✅ Responsive mobile design
✅ Error handling and user feedback

The system is ready for production use with optional enhancements available as needed.
