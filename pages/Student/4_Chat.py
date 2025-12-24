import streamlit as st
import time
from datetime import datetime
from utils.database import get_db_connection

def show():
    st.title("💬 Chat")
    
    # Initialize chat state
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Conversations")
        
        # Search conversations
        search = st.text_input("Search chats...", placeholder="Search by name")
        
        # Get recent conversations
        conversations = get_recent_conversations(search)
        
        # Display conversations
        for conv in conversations:
            is_active = st.session_state.current_chat == conv['other_user_id']
            
            if is_active:
                st.markdown(f"""
                    <div style='background-color: #3B82F6; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <b>{conv['display_name']}</b><br>
                        <small>{conv['last_message'][:30]}...</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(f"**{conv['display_name']}**\n{conv['last_message'][:30]}...", 
                           key=f"chat_{conv['other_user_id']}",
                           use_container_width=True):
                    st.session_state.current_chat = conv['other_user_id']
                    st.rerun()
        
        # New conversation button
        if st.button("+ New Chat", use_container_width=True):
            show_new_chat_modal()
    
    with col2:
        if st.session_state.current_chat:
            show_chat_messages(st.session_state.current_chat)
        else:
            st.info("👈 Select a conversation or start a new chat")
            st.image("https://cdn-icons-png.flaticon.com/512/2454/2454273.png", width=300)

def show_new_chat_modal():
    """Show modal for starting new chat"""
    with st.expander("Start New Chat", expanded=True):
        search_user = st.text_input("Search users...")
        
        if search_user:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    u.id,
                    COALESCE(s.full_name, a.full_name, u.username) as display_name,
                    u.profile_picture,
                    s.department
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                LEFT JOIN alumni a ON u.id = a.user_id
                WHERE u.id != ?
                AND u.is_active = 1
                AND (s.full_name LIKE ? OR u.username LIKE ?)
                LIMIT 10
            ''', (st.session_state.user_id, f"%{search_user}%", f"%{search_user}%"))
            
            users = cursor.fetchall()
            conn.close()
            
            for user in users:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(user.get('profile_picture', 
                             "https://cdn-icons-png.flaticon.com/512/149/149071.png"), 
                             width=40)
                with col2:
                    if st.button(f"💬 {user['display_name']}", key=f"newchat_{user['id']}"):
                        st.session_state.current_chat = user['id']
                        st.rerun()

def show_chat_messages(other_user_id):
    """Display chat messages with a user"""
    # Get user info
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.id,
            COALESCE(s.full_name, a.full_name, u.username) as display_name,
            u.profile_picture,
            s.department,
            u.last_login
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE u.id = ?
    ''', (other_user_id,))
    
    user_info = cursor.fetchone()
    
    # Chat header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image(user_info.get('profile_picture', 
                 "https://cdn-icons-png.flaticon.com/512/149/149071.png"), 
                 width=50)
    with col2:
        st.subheader(user_info['display_name'])
        st.caption(f"🎓 {user_info.get('department', 'User')}")
    with col3:
        if st.button("📞 Call"):
            st.info("Voice/video call feature coming soon!")
    
    st.divider()
    
    # Messages container
    messages_container = st.container(height=400)
    
    with messages_container:
        # Get messages
        cursor.execute('''
            SELECT 
                m.*,
                CASE 
                    WHEN m.sender_id = ? THEN 1
                    ELSE 0
                END as is_sender
            FROM messages m
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
            LIMIT 50
        ''', (st.session_state.user_id, st.session_state.user_id, other_user_id,
              other_user_id, st.session_state.user_id))
        
        messages = cursor.fetchall()
        
        # Mark messages as read
        cursor.execute('''
            UPDATE messages 
            SET is_read = 1
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        ''', (other_user_id, st.session_state.user_id))
        conn.commit()
        
        for msg in messages:
            is_sender = msg['is_sender'] == 1
            
            if is_sender:
                # Right aligned (sent messages)
                st.markdown(f"""
                    <div style='text-align: right; margin: 10px 0;'>
                        <div style='background-color: #3B82F6; color: white; 
                                    padding: 10px; border-radius: 15px 15px 0 15px;
                                    display: inline-block; max-width: 70%;'>
                            {msg['message']}
                        </div>
                        <div style='font-size: 0.8em; color: #666;'>
                            {msg['timestamp'][11:16]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Left aligned (received messages)
                st.markdown(f"""
                    <div style='text-align: left; margin: 10px 0;'>
                        <div style='background-color: #E5E7EB; color: black; 
                                    padding: 10px; border-radius: 15px 15px 15px 0;
                                    display: inline-block; max-width: 70%;'>
                            {msg['message']}
                        </div>
                        <div style='font-size: 0.8em; color: #666;'>
                            {msg['timestamp'][11:16]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    conn.close()
    
    # Message input
    st.divider()
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        message = st.text_input(
            "Type a message...",
            key="new_message_input",
            placeholder="Press Enter to send",
            label_visibility="collapsed"
        )
    
    with col2:
        send_btn = st.button("Send", type="primary", use_container_width=True)
    
    # Send message logic
    if send_btn and message:
        send_message(other_user_id, message)
        st.rerun()

def get_recent_conversations(search=None):
    """Get list of recent conversations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        WITH last_messages AS (
            SELECT 
                CASE 
                    WHEN sender_id = ? THEN receiver_id
                    ELSE sender_id
                END as other_user_id,
                MAX(timestamp) as last_time
            FROM messages
            WHERE sender_id = ? OR receiver_id = ?
            GROUP BY other_user_id
        )
        SELECT 
            lm.other_user_id,
            COALESCE(s.full_name, a.full_name, u.username) as display_name,
            u.profile_picture,
            s.department,
            (SELECT message FROM messages 
             WHERE ((sender_id = ? AND receiver_id = lm.other_user_id) 
                    OR (sender_id = lm.other_user_id AND receiver_id = ?))
             ORDER BY timestamp DESC LIMIT 1) as last_message
        FROM last_messages lm
        JOIN users u ON lm.other_user_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE u.is_active = 1
    '''
    
    params = [st.session_state.user_id, st.session_state.user_id, 
              st.session_state.user_id, st.session_state.user_id,
              st.session_state.user_id]
    
    if search:
        query += " AND (s.full_name LIKE ? OR u.username LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    query += " ORDER BY lm.last_time DESC LIMIT 10"
    
    cursor.execute(query, tuple(params))
    conversations = cursor.fetchall()
    conn.close()
    
    return conversations

def send_message(receiver_id, message):
    """Send a message"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO messages (sender_id, receiver_id, message, is_delivered)
            VALUES (?, ?, ?, 1)
        ''', (st.session_state.user_id, receiver_id, message))
        conn.commit()
        st.success("Message sent!")
    except Exception as e:
        st.error(f"Error sending message: {e}")
    finally:
        conn.close()
