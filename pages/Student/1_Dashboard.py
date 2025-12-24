import streamlit as st
from utils.database import get_db_connection

def show():
    st.title("🎓 Student Dashboard")
    
    # Welcome message
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Welcome back, {st.session_state.full_name}! 👋")
        
        # Get user details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT batch, department FROM students WHERE user_id = ?", 
                      (st.session_state.user_id,))
        student_info = cursor.fetchone()
        
        if student_info:
            st.caption(f"Batch: {student_info['batch']} | Department: {student_info['department']}")
    with col2:
        from datetime import datetime
        st.metric("Today's Date", datetime.now().strftime("%d %b %Y"))
    
    # Quick Stats
    st.subheader("📊 Your Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Friends count
        cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ? AND status = 'accepted'", 
                      (st.session_state.user_id,))
        friends_count = cursor.fetchone()[0]
        st.metric("👥 Friends", friends_count)
    
    with col2:
        # Upcoming events count
        cursor.execute("""SELECT COUNT(*) FROM event_registrations er 
                       JOIN events e ON er.event_id = e.id 
                       WHERE er.user_id = ? AND e.event_date >= date('now')""", 
                      (st.session_state.user_id,))
        events_count = cursor.fetchone()[0]
        st.metric("📅 Events", events_count)
    
    with col3:
        # Groups count
        cursor.execute("SELECT COUNT(*) FROM group_members WHERE user_id = ?", 
                      (st.session_state.user_id,))
        groups_count = cursor.fetchone()[0]
        st.metric("👥 Groups", groups_count)
    
    with col4:
        # Unread messages
        cursor.execute("SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0", 
                      (st.session_state.user_id,))
        unread_msg = cursor.fetchone()[0]
        st.metric("💬 Messages", unread_msg, delta="unread" if unread_msg > 0 else None)
    
    conn.close()
    
    # Main content columns
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Upcoming Events
        st.subheader("📅 Upcoming Events")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, 
                   (SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id) as registered
            FROM events e
            WHERE e.event_date >= date('now')
            AND e.is_active = 1
            ORDER BY e.event_date
            LIMIT 5
        ''')
        
        events = cursor.fetchall()
        
        if events:
            for event in events:
                with st.container():
                    e_col1, e_col2 = st.columns([4, 1])
                    with e_col1:
                        st.write(f"**{event['title']}**")
                        st.caption(f"📅 {event['event_date']} | 🕒 {event['event_time']}")
                        st.caption(f"📍 {event['location']}")
                        if event['max_participants']:
                            progress = min(event['registered']/event['max_participants'], 1)
                            st.progress(progress, text=f"{event['registered']}/{event['max_participants']} registered")
                    with e_col2:
                        # Check if already registered
                        cursor.execute("SELECT id FROM event_registrations WHERE event_id = ? AND user_id = ?",
                                     (event['id'], st.session_state.user_id))
                        if cursor.fetchone():
                            st.success("✅ Registered")
                        else:
                            if st.button("Register", key=f"reg_{event['id']}"):
                                cursor.execute("INSERT INTO event_registrations (event_id, user_id) VALUES (?, ?)",
                                             (event['id'], st.session_state.user_id))
                                conn.commit()
                                st.success("Registered successfully!")
                                st.rerun()
                    st.divider()
        else:
            st.info("No upcoming events. Check back later!")
        
        conn.close()
        
        # Recent Confessions
        st.subheader("💬 Recent Confessions")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM confessions 
            WHERE approved_by_admin = 1
            ORDER BY timestamp DESC
            LIMIT 3
        ''')
        
        confessions = cursor.fetchall()
        
        if confessions:
            for confession in confessions:
                with st.expander(f"{confession['confession_text'][:50]}..."):
                    st.write(confession['confession_text'])
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.caption(f"❤️ {confession['likes_count']} likes")
                    with col_r:
                        st.caption(f"💬 {confession['comments_count']} comments")
                    # Check if user liked this confession
                    cursor.execute("SELECT id FROM confession_likes WHERE confession_id = ? AND user_id = ?",
                                 (confession['id'], st.session_state.user_id))
                    liked = cursor.fetchone() is not None
                    
                    if st.button("❤️ Like" if not liked else "💔 Unlike", key=f"like_{confession['id']}"):
                        if liked:
                            cursor.execute("DELETE FROM confession_likes WHERE confession_id = ? AND user_id = ?",
                                         (confession['id'], st.session_state.user_id))
                            cursor.execute("UPDATE confessions SET likes_count = likes_count - 1 WHERE id = ?",
                                         (confession['id'],))
                        else:
                            cursor.execute("INSERT INTO confession_likes (confession_id, user_id) VALUES (?, ?)",
                                         (confession['id'], st.session_state.user_id))
                            cursor.execute("UPDATE confessions SET likes_count = likes_count + 1 WHERE id = ?",
                                         (confession['id'],))
                        conn.commit()
                        st.rerun()
        else:
            st.info("No confessions yet. Be the first to share!")
        
        conn.close()
    
    with col_right:
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📝 Post Confession", use_container_width=True):
            st.switch_page("pages/Student/6_Confessions.py")
        
        if st.button("👥 Find Friends", use_container_width=True):
            st.switch_page("pages/Student/3_Friends.py")
        
        if st.button("💬 Start Chat", use_container_width=True):
            st.switch_page("pages/Student/4_Chat.py")
        
        if st.button("👥 Join Group", use_container_width=True):
            st.switch_page("pages/Student/5_Groups.py")
        
        if st.button("📅 Create Event", use_container_width=True):
            st.switch_page("pages/Student/7_Events.py")
        
        st.divider()
        
        # Study Groups
        st.subheader("📚 Study Groups")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.*, 
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM groups g
            WHERE g.group_type = 'study' 
            AND g.is_public = 1
            AND g.id NOT IN (SELECT group_id FROM group_members WHERE user_id = ?)
            LIMIT 3
        ''', (st.session_state.user_id,))
        
        study_groups = cursor.fetchall()
        
        if study_groups:
            for group in study_groups:
                st.write(f"**{group['name']}**")
                st.caption(f"👥 {group['member_count']} members")
                if st.button("Join", key=f"join_{group['id']}", size="small"):
                    cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                                 (group['id'], st.session_state.user_id))
                    conn.commit()
                    st.success("Successfully joined the group!")
                    st.rerun()
                st.divider()
        
        conn.close()
        
        # Deadlines/Reminders
        st.subheader("⏰ Reminders")
        
        deadlines = [
            {"task": "Project Submission", "date": "2024-01-25"},
            {"task": "Exam Registration", "date": "2024-01-28"},
            {"task": "Scholarship Apply", "date": "2024-01-30"},
        ]
        
        from datetime import datetime
        for deadline in deadlines:
            days_left = (datetime.strptime(deadline['date'], "%Y-%m-%d") - datetime.now()).days
            st.write(f"**{deadline['task']}**")
            st.caption(f"⏳ {days_left} days left")
            st.progress(max(0, 1 - days_left/30))
