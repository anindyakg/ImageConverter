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
                data = json.load(f)
                # Convert old format to new format if needed
                if data and isinstance(list(data.values())[0], str):
                    # Old format: {'username': 'hash'}
                    # Convert to new format: {'username': {'password': 'hash', 'expiry': None}}
                    new_data = {}
                    for username, password_hash in data.items():
                        new_data[username] = {
                            'password': password_hash,
                            'expiry': None  # No expiry for existing users
                        }
                    self._save_credentials(new_data)
                    return new_data
                return data
        else:
            # Default credentials (change these!)
            default_creds = {
                'admin': {
                    'password': self.hash_password('admin123'),
                    'expiry': None  # Permanent account
                },
                'demo': {
                    'password': self.hash_password('demo123'),
                    'expiry': None  # Permanent account
                }
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
        """Verify username and password, check if account has expired"""
        if username not in self.credentials:
            return False, "Invalid username or password"
        
        user_data = self.credentials[username]
        
        # Check if account has expired
        if user_data.get('expiry'):
            expiry_time = datetime.fromisoformat(user_data['expiry'])
            if datetime.now() > expiry_time:
                return False, "Account has expired. Please contact support."
        
        # Verify password
        password_hash = self.hash_password(password)
        if user_data['password'] == password_hash:
            return True, "Success"
        
        return False, "Invalid username or password"
    
    def add_user(self, username, password, expiry_hours=None):
        """
        Add new user with optional expiration
        
        Args:
            username: Username for the new account
            password: Password for the new account
            expiry_hours: Number of hours until account expires (None = no expiry)
        
        Returns:
            Tuple of (success: bool, message: str, expiry_time: str or None)
        """
        if username in self.credentials:
            return False, "Username already exists", None
        
        # Calculate expiry time if specified
        expiry_time = None
        if expiry_hours:
            expiry_datetime = datetime.now() + timedelta(hours=expiry_hours)
            expiry_time = expiry_datetime.isoformat()
        
        self.credentials[username] = {
            'password': self.hash_password(password),
            'expiry': expiry_time
        }
        self._save_credentials(self.credentials)
        
        if expiry_time:
            expiry_str = datetime.fromisoformat(expiry_time).strftime("%Y-%m-%d %H:%M:%S")
            return True, f"User created successfully. Account expires: {expiry_str}", expiry_time
        else:
            return True, "User created successfully (permanent account)", None
    
    def add_trial_user(self, username, password, trial_hours=2):
        """
        Add a trial user that expires after specified hours (default 2 hours)
        
        Args:
            username: Username for trial account
            password: Password for trial account
            trial_hours: Hours until expiration (default: 2)
        
        Returns:
            Tuple of (success: bool, message: str, expiry_time: str)
        """
        return self.add_user(username, password, expiry_hours=trial_hours)
    
    def get_account_info(self, username):
        """Get account information including expiry status"""
        if username not in self.credentials:
            return None
        
        user_data = self.credentials[username]
        
        # Handle old format (string) vs new format (dict)
        if isinstance(user_data, str):
            # Old format - just a password hash string
            # Convert to new format
            self.credentials[username] = {
                'password': user_data,
                'expiry': None
            }
            self._save_credentials(self.credentials)
            user_data = self.credentials[username]
        
        info = {
            'username': username,
            'has_expiry': user_data.get('expiry') is not None
        }
        
        if user_data.get('expiry'):
            try:
                expiry_datetime = datetime.fromisoformat(user_data['expiry'])
                info['expiry_time'] = expiry_datetime.strftime("%Y-%m-%d %H:%M:%S")
                info['is_expired'] = datetime.now() > expiry_datetime
                
                if not info['is_expired']:
                    time_remaining = expiry_datetime - datetime.now()
                    total_seconds = int(time_remaining.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    if hours > 0:
                        info['time_remaining'] = f"{hours}h {minutes}m {seconds}s"
                    else:
                        info['time_remaining'] = f"{minutes}m {seconds}s"
                    
                    info['total_seconds_remaining'] = total_seconds
                else:
                    info['time_remaining'] = "Expired"
                    info['total_seconds_remaining'] = 0
            except Exception as e:
                # If there's an error parsing the expiry, treat as no expiry
                info['expiry_time'] = "Error parsing expiry"
                info['is_expired'] = False
                info['time_remaining'] = "Unknown"
        else:
            info['expiry_time'] = "Never (Permanent)"
            info['is_expired'] = False
            info['time_remaining'] = "Unlimited"
        
        return info
    
    def extend_account(self, username, additional_hours):
        """Extend account expiration by additional hours"""
        if username not in self.credentials:
            return False, "User not found"
        
        user_data = self.credentials[username]
        
        if not user_data.get('expiry'):
            return False, "Account has no expiration (permanent account)"
        
        current_expiry = datetime.fromisoformat(user_data['expiry'])
        new_expiry = current_expiry + timedelta(hours=additional_hours)
        
        self.credentials[username]['expiry'] = new_expiry.isoformat()
        self._save_credentials(self.credentials)
        
        return True, f"Account extended until {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def change_password(self, username, old_password, new_password):
        """Change user password"""
        success, message = self.verify_credentials(username, old_password)
        if not success:
            return False, message
        
        self.credentials[username]['password'] = self.hash_password(new_password)
        self._save_credentials(self.credentials)
        return True, "Password changed successfully"
    
    def login_form(self):
        """Display login form"""
        
        # Check if user just logged in and needs to accept T&C
        if st.session_state.get('show_terms', False):
            self._show_terms_popup()
        
        # Hero banner - 50% smaller with Beta version
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px 15px; border-radius: 15px; margin: 10px auto 20px auto; 
                    text-align: center; box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);'>
            <h1 style='color: white; font-size: 1.5em; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
                📸 Photo Converter Pro <span style='font-size: 0.5em; background: rgba(255,255,255,0.3); padding: 3px 8px; border-radius: 5px;'>Beta 1.0</span>
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
            st.info("📧 Need a trial account? Reach out to **contact@photoconverter.org**")
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
                    else:
                        success, message = self.verify_credentials(username, password)
                        if success:
                            # Set flag to show T&C popup
                            st.session_state.show_terms = True
                            st.session_state.pending_username = username
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            st.markdown("---")
            st.caption("🔒 Your data is secure and encrypted")
        
        st.stop()
    
    @st.dialog("📋 Terms and Conditions")
    def _show_terms_popup(self):
        """Display Terms and Conditions in a modal popup"""
        
        st.markdown("""
        <div style='font-size: 0.95em; line-height: 1.7;'>
            <p><strong>Please read and accept our terms to continue:</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Scrollable terms in a container
        with st.container(height=400):
            st.markdown("""
            <ul style='padding-left: 20px; margin: 15px 0;'>
                <li style='margin: 12px 0;'>✅ <strong>Age Requirement:</strong> You must be 18 years or older to use this service.</li>
                <li style='margin: 12px 0;'>✅ <strong>Uploaded Content:</strong> You own all photos you upload and are responsible for their content.</li>
                <li style='margin: 12px 0;'>✅ <strong>Prohibited Content:</strong> Do not upload illegal, offensive, or inappropriate images.</li>
                <li style='margin: 12px 0;'>✅ <strong>AI Processing:</strong> Your photos will be processed using Google Gemini AI technology.</li>
                <li style='margin: 12px 0;'>✅ <strong>Data Privacy:</strong> We do not store your images permanently after processing.</li>
                <li style='margin: 12px 0;'>✅ <strong>Account Security:</strong> You are responsible for maintaining your account credentials.</li>
                <li style='margin: 12px 0;'>✅ <strong>Fair Use:</strong> This service is for personal, non-commercial use only.</li>
                <li style='margin: 12px 0;'>✅ <strong>API Limits:</strong> Usage may be subject to rate limits based on API availability.</li>
                <li style='margin: 12px 0;'>✅ <strong>No Guarantees:</strong> AI results may vary and are not guaranteed to be perfect.</li>
                <li style='margin: 12px 0;'>✅ <strong>Right to Modify:</strong> We may update features or terms at any time.</li>
                <li style='margin: 12px 0;'>✅ <strong>No Liability:</strong> We are not liable for any misuse or issues arising from the service.</li>
                <li style='margin: 12px 0;'>✅ <strong>Acceptance:</strong> By clicking "I Accept", you agree to all terms stated above.</li>
            </ul>
            <p style='margin-top: 20px; font-size: 0.9em; color: #6b7280; text-align: center;'>
                Last updated: December 2025
            </p>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Decline", use_container_width=True, type="secondary", key="decline_btn"):
                st.session_state.show_terms = False
                st.session_state.pop('pending_username', None)
                st.rerun()
        
        with col2:
            if st.button("✅ I Accept", use_container_width=True, type="primary", key="accept_btn"):
                # Complete login
                st.session_state.authenticated = True
                st.session_state.username = st.session_state.pending_username
                st.session_state.login_time = datetime.now()
                st.session_state.show_terms = False
                st.session_state.pop('pending_username', None)
                st.rerun()
    
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
        """Display user info with logout button and expiry information"""
        import time
        
        account_info = self.get_account_info(st.session_state.username)
        
        if location == 'sidebar':
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"**👤 Logged in as:** {st.session_state.username}")
                
                if account_info and account_info['has_expiry']:
                    if account_info['is_expired']:
                        st.error(f"⏰ Account expired")
                        st.warning("🚨 Your session has expired. You will be logged out in 3 seconds...")
                        time.sleep(3)
                        self.logout()
                        st.rerun()
                    else:
                        total_seconds = account_info.get('total_seconds_remaining', 0)
                        
                        # Show warning if less than 5 minutes remaining
                        if total_seconds <= 300 and total_seconds > 0:
                            st.warning(f"⚠️ **Warning:** Only **{account_info['time_remaining']}** remaining!")
                            st.caption("⚡ Please save your work!")
                        else:
                            st.info(f"⏰ Time remaining: **{account_info['time_remaining']}**")
                        
                        st.caption(f"📅 Expires: {account_info['expiry_time']}")
                        
                        # Manual refresh button
                        if st.button("🔄 Refresh Timer", use_container_width=True, key="refresh_timer"):
                            import time as time_module
                            st.session_state.last_timer_update = time_module.time()
                            st.rerun()
                else:
                    st.success("✨ Permanent account")
                
                if st.session_state.login_time:
                    login_time = st.session_state.login_time.strftime("%Y-%m-%d %H:%M")
                    st.caption(f"🕒 Login: {login_time}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
                    st.rerun()
        else:
            # Main area display
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**👤 Logged in as:** {st.session_state.username}")
                if account_info and account_info['has_expiry'] and not account_info['is_expired']:
                    total_seconds = account_info.get('total_seconds_remaining', 0)
                    if total_seconds <= 300:
                        st.warning(f"⚠️ {account_info['time_remaining']} remaining")
                    else:
                        st.caption(f"⏰ {account_info['time_remaining']} remaining")
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