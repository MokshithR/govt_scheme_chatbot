"""
Check if user exists in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from django.contrib.auth.models import User

username = input("Enter username to check: ").strip()

try:
    user = User.objects.get(username=username)
    print(f"\n✅ User found!")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Name: {user.first_name} {user.last_name}")
    print(f"Is Active: {user.is_active}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Last Login: {user.last_login}")
    
    # Test password
    test_password = input("\nEnter password to verify: ")
    if user.check_password(test_password):
        print("✅ Password is CORRECT!")
    else:
        print("❌ Password is INCORRECT!")
        
except User.DoesNotExist:
    print(f"\n❌ User '{username}' does NOT exist in database!")
    print("\nAll users in database:")
    all_users = User.objects.all()
    if all_users:
        for u in all_users:
            print(f"  - {u.username} (Active: {u.is_active})")
    else:
        print("  No users found in database!")
        print("\n💡 Create a user with: python create_user.py")
