import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = "data/mes_connect.db"

def get_db_connection():
    """Create and return a database connection"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'alumni', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_picture TEXT,
            bio TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0
        )
    ''')
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            batch TEXT,
            department TEXT,
            roll_number TEXT UNIQUE,
            contact_number TEXT,
            semester TEXT,
            cgpa REAL,
            skills TEXT,
            interests TEXT,
            github_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Alumni table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            graduation_year INTEGER,
            current_position TEXT,
            company TEXT,
            industry TEXT,
            experience_years INTEGER,
            linkedin_url TEXT,
            expertise_area TEXT,
            salary_range TEXT,
            is_mentor BOOLEAN DEFAULT 0,
            available_for_mentorship BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Connections/Friends
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            connected_user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'blocked')),
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (connected_user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, connected_user_id)
        )
    ''')
    
    # Messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            is_delivered BOOLEAN DEFAULT 0,
            message_type TEXT DEFAULT 'text',
            attachment_url TEXT,
            FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Confessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS confessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            confession_text TEXT NOT NULL,
            tags TEXT,
            is_anonymous BOOLEAN DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by_admin BOOLEAN DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            reports_count INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Confession Likes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS confession_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            confession_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (confession_id) REFERENCES confessions (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(confession_id, user_id)
        )
    ''')
    
    # Events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            organizer_id INTEGER NOT NULL,
            event_type TEXT CHECK(event_type IN ('workshop', 'seminar', 'hackathon', 'social', 'career_fair', 'other')),
            event_date DATE NOT NULL,
            event_time TIME NOT NULL,
            end_date DATE,
            end_time TIME,
            location TEXT,
            online_link TEXT,
            max_participants INTEGER,
            fee REAL DEFAULT 0,
            registration_deadline DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            cover_image TEXT,
            FOREIGN KEY (organizer_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Event Registrations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_status TEXT DEFAULT 'pending',
            attendance_status TEXT DEFAULT 'registered',
            feedback TEXT,
            rating INTEGER,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(event_id, user_id)
        )
    ''')
    
    # Groups
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            creator_id INTEGER NOT NULL,
            group_type TEXT CHECK(group_type IN ('study', 'project', 'hobby', 'department', 'batch', 'other')),
            is_public BOOLEAN DEFAULT 1,
            max_members INTEGER,
            cover_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rules TEXT,
            FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Group Members
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member' CHECK(role IN ('member', 'admin', 'moderator')),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(group_id, user_id)
        )
    ''')
    
    # Create admin user
    admin_password = hashlib.sha256("education".encode()).hexdigest()
    
    cursor.execute("SELECT id FROM users WHERE username = 'mesadmin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password, email, role, is_verified, bio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('mesadmin', admin_password, 'admin@mesconnect.com', 'admin', 1, 'System Administrator'))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Execute SQL query safely"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
        else:
            conn.commit()
            result = cursor.lastrowid
        
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user details by ID"""
    query = '''
        SELECT u.*, 
               COALESCE(s.full_name, a.full_name, u.username) as display_name,
               s.department as student_department,
               s.batch as student_batch,
               a.company as alumni_company,
               a.current_position as alumni_position
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE u.id = ?
    '''
    return execute_query(query, (user_id,), fetch_one=True)

def update_user_profile(user_id, **kwargs):
    """Update user profile information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update users table
        user_fields = ['email', 'profile_picture', 'bio']
        user_updates = {k: v for k, v in kwargs.items() if k in user_fields}
        
        if user_updates:
            set_clause = ', '.join([f"{k} = ?" for k in user_updates.keys()])
            query = f"UPDATE users SET {set_clause} WHERE id = ?"
            cursor.execute(query, tuple(user_updates.values()) + (user_id,))
        
        # Get user role
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user_role = cursor.fetchone()[0]
        
        # Update role-specific table
        if user_role == 'student':
            student_fields = ['full_name', 'batch', 'department', 'roll_number', 
                            'contact_number', 'semester', 'cgpa', 'skills', 'interests', 'github_url']
            student_updates = {k: v for k, v in kwargs.items() if k in student_fields}
            
            if student_updates:
                # Check if student record exists
                cursor.execute("SELECT id FROM students WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    set_clause = ', '.join([f"{k} = ?" for k in student_updates.keys()])
                    query = f"UPDATE students SET {set_clause} WHERE user_id = ?"
                    cursor.execute(query, tuple(student_updates.values()) + (user_id,))
                else:
                    columns = ['user_id'] + list(student_updates.keys())
                    values = [user_id] + list(student_updates.values())
                    placeholders = ', '.join(['?'] * len(columns))
                    query = f"INSERT INTO students ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.execute(query, tuple(values))
        
        elif user_role == 'alumni':
            alumni_fields = ['full_name', 'graduation_year', 'current_position', 'company',
                           'industry', 'experience_years', 'linkedin_url', 'expertise_area',
                           'salary_range', 'is_mentor', 'available_for_mentorship']
            alumni_updates = {k: v for k, v in kwargs.items() if k in alumni_fields}
            
            if alumni_updates:
                cursor.execute("SELECT id FROM alumni WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    set_clause = ', '.join([f"{k} = ?" for k in alumni_updates.keys()])
                    query = f"UPDATE alumni SET {set_clause} WHERE user_id = ?"
                    cursor.execute(query, tuple(alumni_updates.values()) + (user_id,))
                else:
                    columns = ['user_id'] + list(alumni_updates.keys())
                    values = [user_id] + list(alumni_updates.values())
                    placeholders = ', '.join(['?'] * len(columns))
                    query = f"INSERT INTO alumni ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.execute(query, tuple(values))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating profile: {e}")
        return False
    finally:
        conn.close()
