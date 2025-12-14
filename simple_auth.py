"""
Simple Authentication Module for Streamlit
No OAuth required - uses username/password
"""
import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta

class SimpleAuthenticator:
    """Simple username/password authentication for Streamlit apps"""
    
    def __init__(self, credentials_file='users.json'):
        """
        Initialize Simple Authenticator
        
        Args:
            credentials_file: Path to JSON file with user credentials
        """
        self.credentials_file = credentials_file
        self.credentials = self._load_credentials()
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
    
    def _load_credentials(self):
        """Load credentials from file or use defaults"""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        else:
            # Default credentials (change these!)
            default_creds = {
                'admin': self.hash_password('admin123'),
                'demo': self.hash_password('demo123')
            }
            self._save_credentials(default_creds)
            return default_creds
    
    def _save_credentials(self, credentials):
        """Save credentials to file"""
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=4)
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_credentials(self, username, password):
        """Verify username and password"""
        password_hash = self.hash_password(password)
        return self.credentials.get(username) == password_hash
    
    def add_user(self, username, password):
        """Add a new user"""
        if username in self.credentials:
            return False, "Username already exists"
        
        self.credentials[username] = self.hash_password(password)
        self._save_credentials(self.credentials)
        return True, "User created successfully"
    
    def change_password(self, username, old_password, new_password):
        """Change user password"""
        if not self.verify_credentials(username, old_password):
            return False, "Invalid current password"
        
        self.credentials[username] = self.hash_password(new_password)
        self._save_credentials(self.credentials)
        return True, "Password changed successfully"
    
    def login_form(self):
        """Display login form"""
        
        # Simple banner with Streamlit native components
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 50px 30px; border-radius: 20px; margin: 20px auto 40px auto; 
                        text-align: center; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);">
                <h1 style="color: white; font-size: 3em; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                    📸 Photo Converter Pro
                </h1>
                <p style="color: #f0f0f0; font-size: 1.3em; margin-bottom: 35px;">
                    Transform Your Photos with AI-Powered Magic
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Features in native Streamlit columns
        st.markdown("### ✨ Powerful Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🎨</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">24 Style Variations</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Passport, Professional, Artistic & More</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🤖</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">AI Age Detection</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Transform to Any Age Range</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">✨</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">Pro Enhancements</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Skin, Hair, Eyes & More</div>
                </div>
            """, unsafe_allow_html=True)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🖼️</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">Custom Backgrounds</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Replace Any Background</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col5:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">⚡</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">Batch Processing</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Edit Multiple Photos</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col6:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%); 
                            padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; 
                            margin: 10px 0; min-height: 120px;">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">📥</div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">Easy Download</div>
                    <div style="color: #6b7280; font-size: 0.9em;">Individual or Bulk ZIP</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # How it works section
        st.markdown("### 🚀 How It Works")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.info("**1️⃣ Upload Photos**\n\nBatch upload multiple images for processing")
        
        with col_s2:
            st.success("**2️⃣ Choose Style**\n\nSelect from 24 AI-powered variations")
        
        with col_s3:
            st.warning("**3️⃣ Download**\n\nGet your professionally edited photos")
        
        st.markdown("---")
        
        # Login form styling
        st.markdown("""
            <style>
            .login-container {
                max-width: 450px;
                margin: 20px auto;
                padding: 40px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.markdown("### 🔐 Sign In to Get Started")
            st.markdown("Create a free account or login to access all features")
            st.markdown("")
            
            # Create tabs for login and signup
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", key="login_username")
                    password = st.text_input("Password", type="password", key="login_password")
                    remember_me = st.checkbox("Remember me")
                    
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    
                    if submit:
                        if not username or not password:
                            st.error("Please enter both username and password")
                        elif self.verify_credentials(username, password):
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.login_time = datetime.now()
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            
            with tab2:
                with st.form("signup_form"):
                    new_username = st.text_input("Choose Username", key="signup_username")
                    new_password = st.text_input("Choose Password", type="password", key="signup_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                    
                    signup = st.form_submit_button("Create Account", use_container_width=True)
                    
                    if signup:
                        if not new_username or not new_password:
                            st.error("Please fill in all fields")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = self.add_user(new_username, new_password)
                            if success:
                                st.success(f"✅ {message}")
                                st.info("You can now login with your credentials")
                            else:
                                st.error(f"❌ {message}")
            
            st.markdown("---")
            st.caption("🔒 Your data is secure and encrypted | 🌟 Powered by Google Gemini AI")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.stop()
    
    def logout(self):
        """Logout user"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.login_time = None
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_username(self):
        """Get current username"""
        return st.session_state.get('username')
    
    def require_authentication(self):
        """Require authentication to access app"""
        if not self.is_authenticated():
            self.login_form()
            return False
        return True
    
    def show_user_info(self, location='sidebar'):
        """Display user information"""
        if not self.is_authenticated():
            return
        
        username = self.get_username()
        login_time = st.session_state.get('login_time')
        
        display_func = st.sidebar if location == 'sidebar' else st
        
        with display_func:
            st.markdown("---")
            st.markdown("### 👤 Signed In")
            st.markdown(f"**User:** {username}")
            
            if login_time:
                duration = datetime.now() - login_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                st.caption(f"Session: {hours}h {minutes}m")
            
            # Change password
            with st.expander("🔑 Change Password"):
                with st.form("change_password_form"):
                    old_pass = st.text_input("Current Password", type="password")
                    new_pass = st.text_input("New Password", type="password")
                    confirm_pass = st.text_input("Confirm New Password", type="password")
                    
                    change = st.form_submit_button("Update Password")
                    
                    if change:
                        if not old_pass or not new_pass:
                            st.error("Please fill in all fields")
                        elif len(new_pass) < 6:
                            st.error("Password must be at least 6 characters")
                        elif new_pass != confirm_pass:
                            st.error("New passwords do not match")
                        else:
                            success, message = self.change_password(username, old_pass, new_pass)
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
            
            if st.button("🚪 Sign Out", use_container_width=True):
                self.logout()
                st.rerun()


# Utility function to create default users file
def create_default_users():
    """Create a default users.json file"""
    authenticator = SimpleAuthenticator()
    default_users = {
        'admin': authenticator.hash_password('admin123'),
        'demo': authenticator.hash_password('demo123'),
        'user': authenticator.hash_password('user123')
    }
    
    with open('users.json', 'w') as f:
        json.dump(default_users, f, indent=4)
    
    print("Created users.json with default users:")
    print("  - admin / admin123")
    print("  - demo / demo123")
    print("  - user / user123")


if __name__ == "__main__":
    create_default_users()