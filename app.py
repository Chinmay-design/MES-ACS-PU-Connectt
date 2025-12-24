import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
from utils.database import init_db, get_db_connection
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="MES Connect - Campus Networking Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 3rem;
        border-radius: 20px;
        background: white;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #3B82F6;
    }
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
    }
    .student-badge {
        background: #10B981;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .alumni-badge {
        background: #8B5CF6;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .admin-badge {
        background: #EF4444;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# Session state initialization
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'full_name' not in st.session_state:
        st.session_state.full_name = None
    if 'email' not in st.session_state:
        st.session_state.email = None
    if 'profile_picture' not in st.session_state:
        st.session_state.profile_picture = None

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.role, u.email, u.profile_picture,
               COALESCE(s.full_name, a.full_name, u.username) as full_name
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE u.username = ? AND u.password = ? AND u.is_active = 1
    ''', (username, hash_password(password)))
    
    user = cursor.fetchone()
    
    # Update last login
    if user:
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user[0],))
        conn.commit()
    
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'role': user[2],
            'email': user[3],
            'profile_picture': user[4],
            'full_name': user[5]
        }
    return None

def register_user(username, password, email, role, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert into users table
        cursor.execute('''
            INSERT INTO users (username, password, email, role)
            VALUES (?, ?, ?, ?)
        ''', (username, hash_password(password), email, role))
        
        user_id = cursor.lastrowid
        
        # Insert into role-specific table
        if role == 'student':
            cursor.execute('''
                INSERT INTO students (user_id, full_name, batch, department, roll_number, contact_number)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, kwargs.get('full_name', ''), 
                  kwargs.get('batch', ''), kwargs.get('department', ''),
                  kwargs.get('roll_number', ''), kwargs.get('contact_number', '')))
        
        elif role == 'alumni':
            cursor.execute('''
                INSERT INTO alumni (user_id, full_name, graduation_year, current_position, company, linkedin_url, expertise_area)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, kwargs.get('full_name', ''), 
                  kwargs.get('graduation_year', ''), 
                  kwargs.get('current_position', ''), 
                  kwargs.get('company', ''),
                  kwargs.get('linkedin_url', ''),
                  kwargs.get('expertise_area', '')))
        
        conn.commit()
        return True, user_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: users.username" in str(e):
            return False, "Username already exists"
        elif "UNIQUE constraint failed: users.email" in str(e):
            return False, "Email already exists"
        return False, str(e)
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# Login Page
def show_login_page():
    st.markdown('<h1 class="main-header">🎓 MES Connect</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Connect • Collaborate • Grow</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 **Login**", "📝 **Sign Up**"])
        
        with tab1:
            st.subheader("Welcome Back!")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.button("🚀 Login", use_container_width=True, type="primary")
            with col_b:
                if st.button("🔄 Reset Password", use_container_width=True):
                    st.info("Password reset feature coming soon!")
            
            if login_btn:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Authenticating..."):
                        user = verify_login(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['id']
                            st.session_state.username = user['username']
                            st.session_state.user_role = user['role']
                            st.session_state.full_name = user['full_name']
                            st.session_state.email = user['email']
                            st.session_state.profile_picture = user['profile_picture']
                            st.success(f"Welcome back, {user['full_name']}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
        
        with tab2:
            st.subheader("Join Our Community")
            
            role = st.selectbox("I am a", ["Student", "Alumni"])
            
            if role == "Student":
                st.page_link("pages/2_👤_Student_Signup.py", label="👉 Student Registration", icon="🎓")
            else:
                st.page_link("pages/3_👨‍🎓_Alumni_Signup.py", label="👉 Alumni Registration", icon="👨‍🎓")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Main Dashboard Navigation
def show_dashboard():
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3067/3067256.png", width=100)
        
        # User info
        role_badge = {
            'student': '<span class="student-badge">🎓 Student</span>',
            'alumni': '<span class="alumni-badge">👨‍🎓 Alumni</span>',
            'admin': '<span class="admin-badge">👑 Admin</span>'
        }.get(st.session_state.user_role, '')
        
        st.markdown(f"### 👋 {st.session_state.full_name}")
        st.markdown(f"**Role:** {role_badge}", unsafe_allow_html=True)
        st.markdown(f"**Email:** {st.session_state.email}")
        
        st.markdown("---")
        
        # Navigation based on role
        if st.session_state.user_role == 'student':
            menu_options = ["Dashboard", "Profile", "Friends", "Chat", "Groups", "Confessions", "Events", "Settings"]
            menu_icons = ["house", "person", "people", "chat", "group", "chat-heart", "calendar-event", "gear"]
            
            selected = st.selectbox(
                "Navigation",
                menu_options,
                index=0,
                format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}"
            )
            
            # Map selection to pages
            page_map = {
                "Dashboard": "pages/Student/1_Dashboard.py",
                "Profile": "pages/Student/2_Profile.py",
                "Friends": "pages/Student/3_Friends.py",
                "Chat": "pages/Student/4_Chat.py",
                "Groups": "pages/Student/5_Groups.py",
                "Confessions": "pages/Student/6_Confessions.py",
                "Events": "pages/Student/7_Events.py",
                "Settings": "pages/Student/8_Settings.py"
            }
            
        elif st.session_state.user_role == 'alumni':
            menu_options = ["Dashboard", "Profile", "Networking", "Chat", "Groups", "Events", "Contributions", "Settings"]
            selected = st.selectbox("Navigation", menu_options)
            
            page_map = {
                "Dashboard": "pages/Alumni/1_Dashboard.py",
                "Profile": "pages/Alumni/2_Profile.py",
                "Networking": "pages/Alumni/3_Networking.py",
                "Chat": "pages/Alumni/4_Chat.py",
                "Groups": "pages/Alumni/5_Groups.py",
                "Events": "pages/Alumni/6_Events.py",
                "Contributions": "pages/Alumni/7_Contributions.py",
                "Settings": "pages/Alumni/8_Settings.py"
            }
        
        else:  # admin
            menu_options = ["Dashboard", "Student Management", "Alumni Management", "Announcements", 
                           "Confession Moderation", "Groups Management", "Analytics"]
            selected = st.selectbox("Navigation", menu_options)
            
            page_map = {
                "Dashboard": "pages/Admin/1_Dashboard.py",
                "Student Management": "pages/Admin/2_Student_Management.py",
                "Alumni Management": "pages/Admin/3_Alumni_Management.py",
                "Announcements": "pages/Admin/4_Announcements.py",
                "Confession Moderation": "pages/Admin/5_Confession_Moderation.py",
                "Groups Management": "pages/Admin/6_Groups_Management.py",
                "Analytics": "pages/Admin/7_Analytics.py"
            }
        
        st.markdown("---")
        
        # Quick stats
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if st.session_state.user_role == 'student':
            cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ? AND status = 'accepted'", 
                         (st.session_state.user_id,))
            friends = cursor.fetchone()[0]
            
            cursor.execute("""SELECT COUNT(*) FROM event_registrations er 
                           JOIN events e ON er.event_id = e.id 
                           WHERE er.user_id = ? AND e.event_date >= date('now')""", 
                         (st.session_state.user_id,))
            events = cursor.fetchone()[0]
            
            st.metric("👥 Friends", friends)
            st.metric("📅 Events", events)
        
        conn.close()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Show selected page
    if selected in page_map:
        try:
            # Dynamically import and show the page
            module_path = page_map[selected].replace('/', '.').replace('.py', '')
            module = __import__(module_path, fromlist=['show'])
            module.show()
        except Exception as e:
            st.error(f"Error loading page: {e}")
            st.info(f"Page: {page_map[selected]}")
    else:
        st.error("Page not found")

# Main Application
def main():
    load_css()
    init_session_state()
    init_db()  # Initialize database
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
