import streamlit as st
from utils.database import get_db_connection

def show():
    st.title("👥 Groups")
    
    tab1, tab2, tab3 = st.tabs(["My Groups", "Discover Groups", "Create Group"])
    
    with tab1:
        show_my_groups()
    
    with tab2:
        discover_groups()
    
    with tab3:
        create_group()

def show_my_groups():
    st.subheader("Groups You're In")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            g.*,
            gm.role,
            (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
            COALESCE(s.full_name, a.full_name, u.username) as creator_name
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN users u ON g.creator_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE gm.user_id = ?
        ORDER BY gm.joined_at DESC
    ''', (st.session_state.user_id,))
    
    groups = cursor.fetchall()
    
    if groups:
        for group in groups:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if group['cover_image']:
                        st.image(group['cover_image'], width=80)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/2252/2252086.png", width=80)
                
                with col2:
                    st.write(f"**{group['name']}**")
                    st.caption(f"📝 {group['description'][:100] if group['description'] else 'No description'}")
                    st.caption(f"👥 {group['member_count']} members • "
                              f"🏷️ {group['group_type'].replace('_', ' ').title()}")
                    
                    # Show your role
                    if group['role'] == 'admin':
                        st.caption("👑 You are an admin")
                    elif group['role'] == 'moderator':
                        st.caption("🛡️ You are a moderator")
                
                with col3:
                    if st.button("Enter", key=f"enter_{group['id']}"):
                        show_group_chat(group['id'])
                    
                    if group['role'] in ['admin', 'moderator']:
                        if st.button("Manage", key=f"manage_{group['id']}"):
                            manage_group(group['id'])
                
                st.divider()
    else:
        st.info("You haven't joined any groups yet. Discover groups to join!")
    
    conn.close()

def discover_groups():
    st.subheader("Discover Groups")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        group_type = st.selectbox(
            "Group Type",
            ["All", "Study", "Project", "Hobby", "Department", "Batch", "Other"]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Most Members", "Recently Created", "Alphabetical"]
        )
    
    with col3:
        privacy = st.selectbox(
            "Privacy",
            ["All", "Public Only", "Private Only"]
        )
    
    # Get groups
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            g.*,
            (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
            COALESCE(s.full_name, a.full_name, u.username) as creator_name,
            EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = ?) as is_member
        FROM groups g
        JOIN users u ON g.creator_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE g.id NOT IN (
            SELECT group_id FROM group_members 
            WHERE user_id = ? AND is_banned = 1
        )
    '''
    
    params = [st.session_state.user_id, st.session_state.user_id]
    
    if group_type != "All":
        query += " AND g.group_type = ?"
        params.append(group_type.lower())
    
    if privacy == "Public Only":
        query += " AND g.is_public = 1"
    elif privacy == "Private Only":
        query += " AND g.is_public = 0"
    
    # Sorting
    if sort_by == "Most Members":
        query += " ORDER BY member_count DESC"
    elif sort_by == "Recently Created":
        query += " ORDER BY g.created_at DESC"
    elif sort_by == "Alphabetical":
        query += " ORDER BY g.name ASC"
    
    cursor.execute(query, tuple(params))
    groups = cursor.fetchall()
    
    if groups:
        for group in groups:
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if group['cover_image']:
                        st.image(group['cover_image'], width=80)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/2252/2252086.png", width=80)
                
                with col2:
                    st.write(f"**{group['name']}**")
                    st.caption(f"📝 {group['description'][:100] if group['description'] else 'No description'}")
                    st.caption(f"👥 {group['member_count']} members • "
                              f"👤 Created by {group['creator_name']}")
                    st.caption(f"🏷️ {group['group_type'].replace('_', ' ').title()} • "
                              f"{'🔓 Public' if group['is_public'] else '🔒 Private'}")
                
                with col3:
                    if group['is_member']:
                        st.success("✅ Joined")
                    else:
                        if group['is_public']:
                            if st.button("Join", key=f"join_{group['id']}"):
                                cursor.execute('''
                                    INSERT INTO group_members (group_id, user_id)
                                    VALUES (?, ?)
                                ''', (group['id'], st.session_state.user_id))
                                conn.commit()
                                st.success("Successfully joined the group!")
                                st.rerun()
                        else:
                            if st.button("Request", key=f"req_{group['id']}"):
                                st.info("Request to join feature coming soon!")
                
                st.divider()
    else:
        st.info("No groups found. Try different filters!")
    
    conn.close()

def create_group():
    st.subheader("Create New Group")
    
    with st.form("create_group_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Group Name*")
            group_type = st.selectbox(
                "Group Type*",
                ["study", "project", "hobby", "department", "batch", "other"]
            )
        
        with col2:
            is_public = st.radio(
                "Privacy*",
                ["🔓 Public (Anyone can join)", "🔒 Private (Requires approval)"],
                index=0
            )
            max_members = st.number_input(
                "Max Members (0 for unlimited)",
                min_value=0,
                value=0
            )
        
        description = st.text_area("Description", height=100)
        rules = st.text_area("Group Rules", height=100)
        
        submitted = st.form_submit_button("Create Group", type="primary")
        
        if submitted:
            if not name:
                st.error("Group name is required!")
            else:
                success = create_new_group(
                    name=name,
                    description=description,
                    group_type=group_type,
                    is_public=is_public.startswith("🔓"),
                    max_members=max_members if max_members > 0 else None,
                    rules=rules
                )
                
                if success:
                    st.success("Group created successfully!")
                    st.balloons()
                else:
                    st.error("Failed to create group. Please try again.")

def show_group_chat(group_id):
    st.info(f"Group chat feature for group {group_id} would open here")

def manage_group(group_id):
    st.info(f"Group management for group {group_id}")

def create_new_group(**kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO groups (name, description, creator_id, group_type, 
                              is_public, max_members, rules)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (kwargs['name'], kwargs['description'], st.session_state.user_id,
              kwargs['group_type'], kwargs['is_public'], kwargs['max_members'],
              kwargs.get('rules')))
        
        group_id = cursor.lastrowid
        
        # Add creator as admin
        cursor.execute('''
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (?, ?, 'admin')
        ''', (group_id, st.session_state.user_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error creating group: {e}")
        return False
    finally:
        conn.close()
