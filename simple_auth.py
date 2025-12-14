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
        if username not in self.credentials:
            return False
        
        password_hash = self.hash_password(password)
        return self.credentials[username] == password_hash
    
    def add_user(self, username, password):
        """Add new user"""
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
        
        # Check if user just logged in and needs to accept T&C
        if st.session_state.get('show_terms', False):
            self._show_terms_and_conditions()
            return
        
        # Hero banner - 50% smaller
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px 15px; border-radius: 15px; margin: 10px auto 20px auto; 
                    text-align: center; box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);'>
            <h1 style='color: white; font-size: 1.5em; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
                📸 Photo Converter Pro
            </h1>
            <p style='color: #f0f0f0; font-size: 0.65em; margin-bottom: 0;'>
                Transform Your Photos with AI-Powered Magic
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sign In button that scrolls to login form
        st.markdown("""
        <div style='text-align: center; margin: 20px auto;'>
            <a href='#sign-in-form' style='text-decoration: none;'>
                <button style='background: #7c3aed; color: white; border: none; 
                              padding: 12px 40px; border-radius: 8px; font-size: 1em; 
                              font-weight: 600; cursor: pointer; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);'>
                    🔐 Sign In
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # Features section with responsive grid (6 in a row on desktop, 2 on mobile)
        st.markdown("""
        <style>
        @media (min-width: 1024px) {
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 8px;
                margin: 20px 0;
            }
        }
        @media (min-width: 768px) and (max-width: 1023px) {
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 20px 0;
            }
        }
        @media (max-width: 767px) {
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin: 20px 0;
            }
        }
        .feature-box-small {
            background: linear-gradient(135deg, #f0f4ff 0%, #e6f0ff 100%);
            padding: 12px;
            border-radius: 10px;
            border-left: 3px solid #667eea;
            text-align: center;
            min-height: 90px;
        }
        .feature-icon-small {
            font-size: 1.8em;
            margin-bottom: 6px;
        }
        .feature-title-small {
            font-weight: 600;
            color: #1f2937;
            font-size: 0.85em;
            margin-bottom: 4px;
        }
        .feature-desc-small {
            color: #6b7280;
            font-size: 0.7em;
            line-height: 1.3;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### ✨ Powerful Features")
        
        # All 6 features in responsive grid
        st.markdown("""
        <div class="feature-grid">
            <div class="feature-box-small">
                <div class="feature-icon-small">🎨</div>
                <div class="feature-title-small">24 Styles</div>
                <div class="feature-desc-small">Multiple variations</div>
            </div>
            <div class="feature-box-small">
                <div class="feature-icon-small">🤖</div>
                <div class="feature-title-small">AI Age</div>
                <div class="feature-desc-small">Any age range</div>
            </div>
            <div class="feature-box-small">
                <div class="feature-icon-small">✨</div>
                <div class="feature-title-small">Enhancements</div>
                <div class="feature-desc-small">Skin, hair, eyes</div>
            </div>
            <div class="feature-box-small">
                <div class="feature-icon-small">🖼️</div>
                <div class="feature-title-small">Backgrounds</div>
                <div class="feature-desc-small">Custom settings</div>
            </div>
            <div class="feature-box-small">
                <div class="feature-icon-small">🧠</div>
                <div class="feature-title-small">Accessible</div>
                <div class="feature-desc-small">Neurodivergent friendly</div>
            </div>
            <div class="feature-box-small">
                <div class="feature-icon-small">📥</div>
                <div class="feature-title-small">Download</div>
                <div class="feature-desc-small">Individual or ZIP</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # How it works section
        st.markdown("### 🚀 How It Works")
        st.markdown("")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.info("**1️⃣ Upload Photos**\n\nBatch upload multiple images for processing")
        
        with col_s2:
            st.success("**2️⃣ Choose Style**\n\nSelect from 24 AI-powered variations")
        
        with col_s3:
            st.warning("**3️⃣ Download**\n\nGet your professionally edited photos")
        
        st.markdown("---")
        st.markdown("")
        
        # Login form anchor - NO signup tab
        st.markdown("<div id='sign-in-form'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔐 Sign In")
            st.caption("Login to access all features")
            st.markdown("")
            
            # Single login form (no tabs, no signup)
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                remember_me = st.checkbox("Remember me")
                
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    elif self.verify_credentials(username, password):
                        # Set flag to show T&C popup
                        st.session_state.show_terms = True
                        st.session_state.pending_username = username
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            
            st.markdown("---")
            st.caption("🔒 Your data is secure and encrypted")
        
        st.stop()
    
    def _show_terms_and_conditions(self):
        """Display Terms and Conditions popup"""
        
        # Full-screen centered layout
        st.markdown("""
        <style>
        .terms-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            max-width: 800px;
            margin: 50px auto;
        }
        .terms-title {
            color: #1f2937;
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 25px;
            text-align: center;
            border-bottom: 3px solid #7c3aed;
            padding-bottom: 15px;
        }
        .terms-content {
            color: #4b5563;
            font-size: 1em;
            line-height: 1.8;
            margin-bottom: 30px;
        }
        .terms-list {
            margin: 20px 0;
            padding-left: 25px;
        }
        .terms-list li {
            margin: 15px 0;
        }
        .terms-footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            font-size: 0.9em;
            color: #6b7280;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="terms-container">
            <div class="terms-title">📋 Terms and Conditions</div>
            <div class="terms-content">
                <p><strong>Please read and accept our terms to continue using Photo Converter Pro:</strong></p>
                <ul class="terms-list">
                    <li>✅ <strong>Age Requirement:</strong> You must be 18 years or older to use this service.</li>
                    <li>✅ <strong>Uploaded Content:</strong> You own all photos you upload and are responsible for their content.</li>
                    <li>✅ <strong>Prohibited Content:</strong> Do not upload illegal, offensive, or inappropriate images.</li>
                    <li>✅ <strong>AI Processing:</strong> Your photos will be processed using Google Gemini AI technology.</li>
                    <li>✅ <strong>Data Privacy:</strong> We do not store your images permanently after processing.</li>
                    <li>✅ <strong>Account Security:</strong> You are responsible for maintaining your account credentials.</li>
                    <li>✅ <strong>Fair Use:</strong> This service is for personal, non-commercial use only.</li>
                    <li>✅ <strong>API Limits:</strong> Usage may be subject to rate limits based on API availability.</li>
                    <li>✅ <strong>No Guarantees:</strong> AI results may vary and are not guaranteed to be perfect.</li>
                    <li>✅ <strong>Right to Modify:</strong> We may update features or terms at any time.</li>
                    <li>✅ <strong>No Liability:</strong> We are not liable for any misuse or issues arising from the service.</li>
                    <li>✅ <strong>Acceptance:</strong> By clicking "I Accept", you agree to all terms stated above.</li>
                </ul>
                <div class="terms-footer">
                    Last updated: December 2025
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("")
        
        # Buttons with clear spacing
        col_space1, col_decline, col_space2, col_accept, col_space3 = st.columns([1, 2, 1, 2, 1])
        
        with col_decline:
            if st.button("❌ Decline Terms", use_container_width=True, type="secondary", key="decline_terms_btn"):
                st.session_state.show_terms = False
                st.session_state.pop('pending_username', None)
                st.error("❌ You must accept the terms to use this service.")
                st.rerun()
        
        with col_accept:
            if st.button("✅ I Accept Terms", use_container_width=True, type="primary", key="accept_terms_btn"):
                # Complete login
                st.session_state.authenticated = True
                st.session_state.username = st.session_state.pending_username
                st.session_state.login_time = datetime.now()
                st.session_state.show_terms = False
                st.session_state.pop('pending_username', None)
                st.success("✅ Terms accepted! Welcome to Photo Converter Pro!")
                st.rerun()
        
        st.stop()
    
    def logout(self):
        """Logout user"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.login_time = None
    
    def require_auth(self):
        """Require authentication - show login form if not authenticated"""
        if not st.session_state.authenticated:
            self.login_form()
        return True
    
    def require_authentication(self):
        """Alias for require_auth - for backwards compatibility"""
        return self.require_auth()
    
    def show_user_info(self, location='sidebar'):
        """Display user info with logout button"""
        if location == 'sidebar':
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"**👤 Logged in as:** {st.session_state.username}")
                if st.session_state.login_time:
                    login_time = st.session_state.login_time.strftime("%Y-%m-%d %H:%M")
                    st.caption(f"🕒 Login time: {login_time}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
                    st.rerun()
        else:
            # Main area display
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**👤 Logged in as:** {st.session_state.username}")
            with col2:
                if st.button("🚪 Logout"):
                    self.logout()
                    st.rerun()
    
    def get_username(self):
        """Get current username"""
        return st.session_state.username
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return st.session_state.authenticated