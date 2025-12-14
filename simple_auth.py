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
            .login-title {
                font-size: 28px;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 8px;
                text-align: center;
            }
            .login-subtitle {
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 30px;
                text-align: center;
            }
            .banner-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 50px 30px;
                border-radius: 20px;
                margin: 20px auto 40px auto;
                max-width: 1200px;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            }
            .banner-title {
                color: white;
                font-size: 3em;
                font-weight: bold;
                text-align: center;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            .banner-subtitle {
                color: #f0f0f0;
                font-size: 1.3em;
                text-align: center;
                margin-bottom: 35px;
                font-weight: 300;
            }
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature-card {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 20px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: transform 0.3s ease;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.2);
            }
            .feature-icon {
                font-size: 2.5em;
                margin-bottom: 10px;
                display: block;
            }
            .feature-title {
                color: white;
                font-size: 1.1em;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .feature-desc {
                color: #e0e0e0;
                font-size: 0.9em;
                line-height: 1.4;
            }
            .demo-section {
                text-align: center;
                margin: 30px auto;
                max-width: 900px;
            }
            .demo-title {
                font-size: 1.8em;
                color: #1f2937;
                margin-bottom: 25px;
                font-weight: 600;
            }
            .step-box {
                background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%);
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #667eea;
                margin: 10px;
            }
            .step-number {
                font-size: 2em;
                color: #667eea;
                font-weight: bold;
            }
            .step-text {
                color: #1f2937;
                font-size: 1em;
                font-weight: 500;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Banner Section
        st.markdown("""
            <div class="banner-container">
                <div class="banner-title">📸 Photo Converter Pro</div>
                <div class="banner-subtitle">Transform Your Photos with AI-Powered Magic</div>
                
                <div class="features-grid">
                    <div class="feature-card">
                        <span class="feature-icon">🎨</span>
                        <div class="feature-title">24 Style Variations</div>
                        <div class="feature-desc">Choose from Passport, Professional, Artistic, Vintage, Modern, and Fun styles - each with 4 unique variations</div>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">🤖</span>
                        <div class="feature-title">AI Age Detection & Transform</div>
                        <div class="feature-desc">Automatically detect age and transform to any age range - from Child to Elderly with realistic results</div>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">✨</span>
                        <div class="feature-title">Professional Enhancements</div>
                        <div class="feature-desc">Enhance skin texture, whiten teeth, brighten eyes, remove grey hair, and more with AI precision</div>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">🖼️</span>
                        <div class="feature-title">Custom Backgrounds</div>
                        <div class="feature-desc">Replace any background with your choice - perfect for professional photos and creative projects</div>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">⚡</span>
                        <div class="feature-title">Batch Processing</div>
                        <div class="feature-desc">Upload and edit multiple photos at once - save time and maintain consistency across images</div>
                    </div>
                    
                    <div class="feature-card">
                        <span class="feature-icon">📥</span>
                        <div class="feature-title">Easy Download</div>
                        <div class="feature-desc">Download individual images or all at once in a convenient ZIP file - your choice!</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # How it works section
        st.markdown('<div class="demo-section"><div class="demo-title">🚀 How It Works</div></div>', unsafe_allow_html=True)
        
        col_demo1, col_demo2, col_demo3 = st.columns(3)
        
        with col_demo1:
            st.markdown("""
                <div class="step-box">
                    <div class="step-number">1️⃣</div>
                    <div class="step-text">Upload Photos</div>
                    <div class="feature-desc">Batch upload multiple images for processing</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_demo2:
            st.markdown("""
                <div class="step-box">
                    <div class="step-number">2️⃣</div>
                    <div class="step-text">Choose Style & Edit</div>
                    <div class="feature-desc">Select from 24 AI variations and enhancements</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_demo3:
            st.markdown("""
                <div class="step-box">
                    <div class="step-number">3️⃣</div>
                    <div class="step-text">Download Results</div>
                    <div class="feature-desc">Get your professionally edited photos instantly</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("")
        
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