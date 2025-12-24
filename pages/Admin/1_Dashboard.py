import streamlit as st
import pandas as pd
from utils.database import get_db_connection

def show():
    st.title("👑 Admin Dashboard")
    
    # Check if user is admin
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        st.metric("Total Users", total_users)
    
    with col2:
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')")
        new_today = cursor.fetchone()[0]
        st.metric("New Today", new_today)
    
    with col3:
        cursor.execute("SELECT COUNT(*) FROM confessions WHERE approved_by_admin = 0")
        pending_confessions = cursor.fetchone()[0]
        st.metric("Pending Confessions", pending_confessions)
    
    with col4:
        st.metric("Active Now", "N/A")
    
    conn.close()
    
    # Recent Activity
    st.subheader("🔄 Recent Activity")
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        st.write("**New Registrations**")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, role, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        new_users = cursor.fetchall()
        
        if new_users:
            for user in new_users:
                st.write(f"👤 {user['username']} ({user['role']}) - {user['created_at'][:10]}")
        else:
            st.info("No new registrations")
    
    with col_act2:
        st.write("**Pending Confessions**")
        cursor.execute("""
            SELECT confession_text, timestamp 
            FROM confessions 
            WHERE approved_by_admin = 0
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        confessions = cursor.fetchall()
        
        if confessions:
            for confession in confessions:
                st.write(f"💬 {confession['confession_text'][:50]}...")
        else:
            st.info("No pending confessions")
    
    conn.close()
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("👥 Manage Users", use_container_width=True):
            st.switch_page("pages/Admin/2_Student_Management.py")
    
    with col_btn2:
        if st.button("💬 Moderate Confessions", use_container_width=True):
            st.switch_page("pages/Admin/5_Confession_Moderation.py")
    
    with col_btn3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.switch_page("pages/Admin/7_Analytics.py")
          
