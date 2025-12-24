import streamlit as st
from utils.database import get_db_connection

def show():
    st.title("👥 Friends & Connections")
    
    tab1, tab2, tab3 = st.tabs(["My Friends", "Find Friends", "Pending Requests"])
    
    with tab1:
        show_my_friends()
    
    with tab2:
        find_friends()
    
    with tab3:
        show_pending_requests()

def show_my_friends():
    st.subheader("Your Connections")
    
    # Search friends
    search = st.text_input("🔍 Search friends...", placeholder="Search by name or department")
    
    # Get friends list
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT DISTINCT 
            u.id, 
            COALESCE(s.full_name, a.full_name, u.username) as display_name,
            u.profile_picture,
            s.department,
            s.batch,
            s.skills
        FROM connections c
        JOIN users u ON (
            (c.user_id = ? AND c.connected_user_id = u.id) OR
            (c.connected_user_id = ? AND c.user_id = u.id)
        )
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE c.status = 'accepted'
        AND u.id != ?
    '''
    
    params = [st.session_state.user_id, st.session_state.user_id, st.session_state.user_id]
    
    if search:
        query += " AND (s.full_name LIKE ? OR s.department LIKE ? OR u.username LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    cursor.execute(query, tuple(params))
    friends = cursor.fetchall()
    
    if friends:
        for friend in friends:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    st.image(friend.get('profile_picture', 
                             "https://cdn-icons-png.flaticon.com/512/149/149071.png"), 
                             width=50)
                
                with col2:
                    st.write(f"**{friend['display_name']}**")
                    st.caption(f"🎓 {friend.get('department', 'Student')}")
                    if friend.get('batch'):
                        st.caption(f"📅 Batch: {friend['batch']}")
                
                with col3:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("💬", key=f"chat_{friend['id']}"):
                            st.switch_page("pages/Student/4_Chat.py")
                    with col_b:
                        if st.button("👁️", key=f"view_{friend['id']}"):
                            show_friend_profile(friend['id'])
                    with col_c:
                        if st.button("❌", key=f"remove_{friend['id']}"):
                            # Remove friend
                            cursor.execute('''
                                DELETE FROM connections 
                                WHERE (user_id = ? AND connected_user_id = ?)
                                   OR (user_id = ? AND connected_user_id = ?)
                            ''', (st.session_state.user_id, friend['id'], 
                                  friend['id'], st.session_state.user_id))
                            conn.commit()
                            st.success("Friend removed")
                            st.rerun()
                
                st.divider()
    else:
        st.info("You haven't added any friends yet. Use 'Find Friends' to connect!")
    
    conn.close()

def find_friends():
    st.subheader("Discover People")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        department = st.selectbox(
            "Department",
            ["All", "Computer Science", "Electronics", "Mechanical", "Civil", 
             "Electrical", "AI & ML", "Data Science"]
        )
    
    with col2:
        batch = st.selectbox(
            "Batch",
            ["All", "2020-2024", "2021-2025", "2022-2026", "2023-2027", "2024-2028"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Recently Joined", "Alphabetical"]
        )
    
    # Get suggested friends
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            u.id,
            COALESCE(s.full_name, a.full_name, u.username) as display_name,
            u.profile_picture,
            s.department,
            s.batch,
            s.skills,
            u.created_at
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        WHERE u.role = 'student'
        AND u.id != ?
        AND u.id NOT IN (
            SELECT connected_user_id FROM connections WHERE user_id = ?
            UNION
            SELECT user_id FROM connections WHERE connected_user_id = ?
        )
        AND u.is_active = 1
    '''
    
    params = [st.session_state.user_id, st.session_state.user_id, st.session_state.user_id]
    
    if department != "All":
        query += " AND s.department = ?"
        params.append(department)
    
    if batch != "All":
        query += " AND s.batch = ?"
        params.append(batch)
    
    # Sorting
    if sort_by == "Recently Joined":
        query += " ORDER BY u.created_at DESC"
    elif sort_by == "Alphabetical":
        query += " ORDER BY display_name ASC"
    
    query += " LIMIT 20"
    
    cursor.execute(query, tuple(params))
    suggestions = cursor.fetchall()
    
    if suggestions:
        for user in suggestions:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                
                with col1:
                    st.image(user.get('profile_picture', 
                             "https://cdn-icons-png.flaticon.com/512/149/149071.png"), 
                             width=50)
                
                with col2:
                    st.write(f"**{user['display_name']}**")
                    st.caption(f"🎓 {user.get('department', 'Student')}")
                    if user.get('batch'):
                        st.caption(f"📅 Batch: {user['batch']}")
                    if user.get('skills'):
                        st.caption(f"🛠️ Skills: {user['skills'][:50]}...")
                
                with col3:
                    # Check connection status
                    cursor.execute('''
                        SELECT status FROM connections 
                        WHERE (user_id = ? AND connected_user_id = ?)
                           OR (user_id = ? AND connected_user_id = ?)
                    ''', (st.session_state.user_id, user['id'], 
                          user['id'], st.session_state.user_id))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        status = result[0]
                        if status == 'pending':
                            # Check who sent the request
                            cursor.execute('''
                                SELECT user_id FROM connections 
                                WHERE user_id = ? AND connected_user_id = ? AND status = 'pending'
                            ''', (st.session_state.user_id, user['id']))
                            
                            if cursor.fetchone():
                                st.info("Request sent")
                            else:
                                col_accept, col_reject = st.columns(2)
                                with col_accept:
                                    if st.button("✓", key=f"accept_{user['id']}"):
                                        cursor.execute('''
                                            UPDATE connections 
                                            SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP
                                            WHERE user_id = ? AND connected_user_id = ?
                                        ''', (user['id'], st.session_state.user_id))
                                        conn.commit()
                                        st.success("Friend request accepted!")
                                        st.rerun()
                                with col_reject:
                                    if st.button("✗", key=f"reject_{user['id']}"):
                                        cursor.execute('''
                                            DELETE FROM connections 
                                            WHERE user_id = ? AND connected_user_id = ?
                                        ''', (user['id'], st.session_state.user_id))
                                        conn.commit()
                                        st.info("Friend request rejected")
                                        st.rerun()
                        elif status == 'accepted':
                            st.success("Friends ✓")
                    else:
                        if st.button("Add Friend", key=f"add_{user['id']}"):
                            cursor.execute('''
                                INSERT INTO connections (user_id, connected_user_id, status)
                                VALUES (?, ?, 'pending')
                            ''', (st.session_state.user_id, user['id']))
                            conn.commit()
                            st.success("Friend request sent!")
                            st.rerun()
                
                st.divider()
    else:
        st.info("No suggestions found. Try different filters.")
    
    conn.close()

def show_pending_requests():
    st.subheader("Pending Friend Requests")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.id,
            c.user_id,
            c.requested_at,
            COALESCE(s.full_name, a.full_name, u.username) as display_name,
            u.profile_picture,
            s.department
        FROM connections c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE c.connected_user_id = ?
        AND c.status = 'pending'
        ORDER BY c.requested_at DESC
    ''', (st.session_state.user_id,))
    
    requests = cursor.fetchall()
    
    if requests:
        for req in requests:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    st.image(req.get('profile_picture', 
                             "https://cdn-icons-png.flaticon.com/512/149/149071.png"), 
                             width=50)
                
                with col2:
                    st.write(f"**{req['display_name']}**")
                    st.caption(f"🎓 {req.get('department', 'Student')}")
                    st.caption(f"📅 Requested: {req['requested_at'][:10]}")
                
                with col3:
                    col_accept, col_reject = st.columns(2)
                    with col_accept:
                        if st.button("Accept", key=f"acc_{req['id']}", use_container_width=True):
                            cursor.execute('''
                                UPDATE connections 
                                SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP
                                WHERE user_id = ? AND connected_user_id = ?
                            ''', (req['user_id'], st.session_state.user_id))
                            conn.commit()
                            st.success("Friend request accepted!")
                            st.rerun()
                    with col_reject:
                        if st.button("Reject", key=f"rej_{req['id']}", use_container_width=True):
                            cursor.execute('''
                                DELETE FROM connections 
                                WHERE user_id = ? AND connected_user_id = ?
                            ''', (req['user_id'], st.session_state.user_id))
                            conn.commit()
                            st.info("Friend request rejected")
                            st.rerun()
                
                st.divider()
    else:
        st.info("No pending requests")
    
    conn.close()

def show_friend_profile(friend_id):
    st.info(f"Friend profile view for user {friend_id} would open here")
