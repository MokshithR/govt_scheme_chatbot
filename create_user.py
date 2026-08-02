"""
Quick script to create a user for YOJANA MITHRA login
Run: python create_user.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from django.contrib.auth.models import User

def create_user():
    print("=" * 50)
    print("YOJANA MITHRA - Create User Account")
    print("=" * 50)
    
    # Check existing users
    existing_users = User.objects.all()
    if existing_users.exists():
        print("\n📋 Existing users:")
        for u in existing_users:
            print(f"  - {u.username} (Active: {u.is_active})")
        print()
    
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"\n⚠️  User '{username}' already exists!")
        choice = input("Do you want to reset the password? (yes/no): ").strip().lower()
        if choice in ['yes', 'y']:
            user = User.objects.get(username=username)
            new_password = input("Enter new password: ").strip()
            if new_password:
                user.set_password(new_password)
                user.save()
                print(f"\n✅ Password updated for '{username}'!")
                print(f"Login at: http://localhost:8000/login/")
            return
        else:
            return
    
    email = input("Enter email (optional, press Enter to skip): ").strip()
    password = input("Enter password: ").strip()
    
    if not password:
        print("❌ Password cannot be empty!")
        return
    
    first_name = input("Enter first name (optional): ").strip()
    last_name = input("Enter last name (optional): ").strip()
    
    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email if email else '',
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        print("\n" + "=" * 50)
        print("✅ User created successfully!")
        print("=" * 50)
        print(f"Username: {username}")
        print(f"Email: {email if email else 'Not provided'}")
        print(f"Name: {first_name} {last_name}".strip() if first_name or last_name else "Name: Not provided")
        print(f"\n🔑 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("\n🌐 Login at: http://localhost:8000/login/")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error creating user: {e}")

if __name__ == "__main__":
    create_user()
