import streamlit as st
from utils.database import get_db_connection

def show():
    st.title("💖 Confessions")
    
    tab1, tab2, tab3 = st.tabs(["Post Confession", "View Confessions", "My Confessions"])
    
    with tab1:
        post_confession()
    
    with tab2:
        view_confessions()
    
    with tab3:
        my_confessions()

def post_confession():
    st.subheader("Share Your Confession")
    
    with st.form("confession_form"):
        confession_text = st.text_area(
            "Your Confession*",
            height=150,
            placeholder="Share your thoughts, feelings, or experiences...",
            help="Be respectful and kind. Anonymous confessions are encouraged."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            tags = st.multiselect(
                "Tags",
                ["Love", "Friendship", "College Life", "Struggle", "Achievement", 
                 "Advice", "Funny", "Sad", "Inspirational", "Secret"]
            )
        
        with col2:
            is_anonymous = st.radio(
                "Post as",
                ["🙈 Anonymous", "👤 With my name"],
                index=0
            )
        
        submitted = st.form_submit_button("Post Confession", type="primary")
        
        if submitted:
            if not confession_text:
                st.error("Please write a confession!")
            elif len(confession_text) < 10:
                st.error("Confession must be at least 10 characters")
            elif len(confession_text) > 1000:
                st.error("Confession is too long (max 1000 characters)")
            else:
                success = save_confession(
                    text=confession_text,
                    tags=",".join(tags) if tags else None,
                    anonymous=is_anonymous.startswith("🙈")
                )
                
                if success:
                    st.success("Confession posted successfully! It will be visible after admin approval.")
                    st.balloons()
                else:
                    st.error("Failed to post confession. Please try again.")

def view_confessions():
    st.subheader("Recent Confessions")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        tag_filter = st.selectbox(
            "Filter by tag",
            ["All"] + ["Love", "Friendship", "College Life", "Struggle", "Achievement", 
                      "Advice", "Funny", "Sad", "Inspirational", "Secret"]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Most Recent", "Most Liked"]
        )
    
    # Get confessions
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT c.*,
               COALESCE(s.full_name, a.full_name, u.username) as author_name
        FROM confessions c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE c.approved_by_admin = 1
    '''
    
    params = []
    
    if tag_filter != "All":
        query += " AND c.tags LIKE ?"
        params.append(f"%{tag_filter}%")
    
    # Sorting
    if sort_by == "Most Recent":
        query += " ORDER BY c.timestamp DESC"
    elif sort_by == "Most Liked":
        query += " ORDER BY c.likes_count DESC, c.timestamp DESC"
    
    query += " LIMIT 20"
    
    cursor.execute(query, tuple(params))
    confessions = cursor.fetchall()
    
    if confessions:
        for confession in confessions:
            display_confession(confession)
    else:
        st.info("No confessions found. Be the first to post!")
    
    conn.close()

def my_confessions():
    st.subheader("My Confessions")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*
        FROM confessions c
        WHERE c.user_id = ?
        ORDER BY c.timestamp DESC
    ''', (st.session_state.user_id,))
    
    confessions = cursor.fetchall()
    
    if confessions:
        for confession in confessions:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    display_confession(confession, show_actions=True)
                
                with col2:
                    if st.button("Delete", key=f"del_{confession['id']}"):
                        cursor.execute('DELETE FROM confessions WHERE id = ?', (confession['id'],))
                        conn.commit()
                        st.success("Confession deleted successfully!")
                        st.rerun()
    else:
        st.info("You haven't posted any confessions yet.")
    
    conn.close()

def display_confession(confession, show_actions=False):
    """Display a confession card"""
    with st.container():
        # Confession header
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if confession['is_featured']:
                st.markdown(f"**🌟 {confession['confession_text'][:100]}...**")
            else:
                st.markdown(f"**{confession['confession_text'][:100]}...**")
        
        with col2:
            if confession['is_anonymous']:
                st.caption("🙈 Anonymous")
            else:
                st.caption(f"👤 {confession.get('author_name', 'User')}")
        
        # Confession content (collapsible)
        with st.expander("Read full confession"):
            st.write(confession['confession_text'])
            
            # Tags
            if confession['tags']:
                tags = confession['tags'].split(',')
                st.write("**Tags:** " + " ".join([f"`{tag}`" for tag in tags]))
        
        # Stats and actions
        col_l, col_m, col_r = st.columns(3)
        
        with col_l:
            # Check if user liked this confession
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM confession_likes WHERE confession_id = ? AND user_id = ?",
                         (confession['id'], st.session_state.user_id))
            liked = cursor.fetchone() is not None
            
            like_icon = "❤️" if liked else "🤍"
            if st.button(f"{like_icon} {confession['likes_count']}", 
                        key=f"like_{confession['id']}"):
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
        
        with col_m:
            if st.button(f"💬 {confession['comments_count']}", 
                        key=f"comment_{confession['id']}"):
                show_comments(confession['id'])
        
        with col_r:
            st.caption(f"📅 {confession['timestamp'][:10]}")
        
        conn.close()
        
        if show_actions and confession['approved_by_admin'] == 0:
            st.warning("⏳ Waiting for admin approval")
        
        st.divider()

def show_comments(confession_id):
    st.info(f"Comments for confession {confession_id} would appear here")

def save_confession(text, tags=None, anonymous=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = st.session_state.user_id if not anonymous else None
        
        cursor.execute('''
            INSERT INTO confessions (user_id, confession_text, tags, is_anonymous)
            VALUES (?, ?, ?, ?)
        ''', (user_id, text, tags, anonymous))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")
        return False
    finally:
        conn.close()
