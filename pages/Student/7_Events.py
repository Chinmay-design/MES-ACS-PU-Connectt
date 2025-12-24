import streamlit as st
from datetime import datetime
from utils.database import get_db_connection

def show():
    st.title("📅 Events")
    
    tab1, tab2, tab3 = st.tabs(["Upcoming Events", "My Events", "Create Event"])
    
    with tab1:
        upcoming_events()
    
    with tab2:
        my_events()
    
    with tab3:
        create_event()

def upcoming_events():
    st.subheader("🎯 Upcoming Events")
    
    # Get events
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.*,
               COALESCE(s.full_name, a.full_name, u.username) as organizer_name,
               (SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id) as registered_count,
               EXISTS(SELECT 1 FROM event_registrations WHERE event_id = e.id AND user_id = ?) as is_registered
        FROM events e
        JOIN users u ON e.organizer_id = u.id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN alumni a ON u.id = a.user_id
        WHERE e.event_date >= date('now')
        AND e.is_active = 1
        ORDER BY e.event_date
    ''', (st.session_state.user_id,))
    
    events = cursor.fetchall()
    
    if events:
        for event in events:
            display_event_card(event, show_register=True)
    else:
        st.info("No upcoming events found.")
    
    conn.close()

def my_events():
    st.subheader("📋 My Events")
    
    tab_attending, tab_organizing = st.tabs(["Attending", "Organizing"])
    
    with tab_attending:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*,
                   COALESCE(s.full_name, a.full_name, u.username) as organizer_name,
                   er.attendance_status
            FROM events e
            JOIN event_registrations er ON e.id = er.event_id
            JOIN users u ON e.organizer_id = u.id
            LEFT JOIN students s ON u.id = s.user_id
            LEFT JOIN alumni a ON u.id = a.user_id
            WHERE er.user_id = ?
            AND e.event_date >= date('now')
            ORDER BY e.event_date
        ''', (st.session_state.user_id,))
        
        attending_events = cursor.fetchall()
        
        if attending_events:
            for event in attending_events:
                display_event_card(event, show_status=True)
        else:
            st.info("You're not registered for any events yet.")
        
        conn.close()
    
    with tab_organizing:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id) as registered_count
            FROM events e
            WHERE e.organizer_id = ?
            ORDER BY e.event_date
        ''', (st.session_state.user_id,))
        
        organizing_events = cursor.fetchall()
        
        if organizing_events:
            for event in organizing_events:
                display_event_card(event, show_manage=True)
        else:
            st.info("You haven't organized any events yet.")
        
        conn.close()

def create_event():
    st.subheader("➕ Create New Event")
    
    with st.form("create_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Event Title*")
            event_type = st.selectbox(
                "Event Type*",
                ["workshop", "seminar", "hackathon", "social", "career_fair", "other"]
            )
            event_date = st.date_input("Event Date*", min_value=datetime.now().date())
            event_time = st.time_input("Event Time*")
        
        with col2:
            location = st.text_input("Location*")
            max_participants = st.number_input("Max Participants (0 for unlimited)", 
                                              min_value=0, value=0)
            registration_deadline = st.date_input("Registration Deadline", 
                                                 min_value=datetime.now().date())
        
        description = st.text_area("Event Description*", height=150)
        
        fee = st.number_input("Registration Fee (₹)", min_value=0.0, value=0.0)
        
        submitted = st.form_submit_button("Create Event", type="primary")
        
        if submitted:
            if not title or not description or not location:
                st.error("Please fill all required fields (*)")
            elif event_date < datetime.now().date():
                st.error("Event date cannot be in the past")
            else:
                success = save_event(
                    title=title,
                    description=description,
                    event_type=event_type,
                    event_date=event_date,
                    event_time=event_time,
                    location=location,
                    max_participants=max_participants if max_participants > 0 else None,
                    fee=fee,
                    registration_deadline=registration_deadline
                )
                
                if success:
                    st.success("Event created successfully!")
                    st.balloons()
                else:
                    st.error("Failed to create event. Please try again.")

def display_event_card(event, show_register=False, show_status=False, show_manage=False):
    """Display an event card"""
    with st.container():
        # Event header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"### {event['title']}")
            event_type_emoji = {
                'workshop': '🔧',
                'seminar': '🎓',
                'hackathon': '💻',
                'social': '🎉',
                'career_fair': '💼',
                'other': '📅'
            }.get(event['event_type'], '📅')
            
            st.caption(f"{event_type_emoji} {event['event_type'].replace('_', ' ').title()} "
                      f"• 👤 Organized by {event.get('organizer_name', 'Unknown')}")
        
        with col2:
            if event['fee'] > 0:
                st.metric("Fee", f"₹{event['fee']}")
            else:
                st.success("Free")
        
        # Event details
        col_details1, col_details2 = st.columns(2)
        
        with col_details1:
            st.write(f"**📅 Date:** {event['event_date']}")
            st.write(f"**🕒 Time:** {event['event_time']}")
        
        with col_details2:
            st.write(f"**📍 Location:** {event['location']}")
        
        # Progress bar for registration
        if event['max_participants']:
            registered = event.get('registered_count', 0)
            capacity = event['max_participants']
            percentage = min(registered / capacity, 1.0)
            
            st.progress(percentage, text=f"{registered}/{capacity} registered")
            
            if registered >= capacity:
                st.warning("⚠️ Event is full!")
        
        # Description (collapsible)
        with st.expander("View Description"):
            st.write(event['description'])
        
        # Actions
        if show_register:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if event.get('is_registered'):
                    st.success("✅ Registered")
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if st.button("Register Now", key=f"reg_{event['id']}", 
                                use_container_width=True):
                        try:
                            cursor.execute('''
                                INSERT INTO event_registrations (event_id, user_id)
                                VALUES (?, ?)
                            ''', (event['id'], st.session_state.user_id))
                            conn.commit()
                            st.success("Successfully registered for the event!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
            with col_btn2:
                if st.button("View Details", key=f"view_{event['id']}", 
                            use_container_width=True):
                    show_event_details(event['id'])
        
        elif show_status:
            st.info(f"Status: {event.get('attendance_status', 'registered').title()}")
        
        elif show_manage:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if st.button("Manage", key=f"mng_{event['id']}"):
                    manage_event(event['id'])
            with col_m2:
                if st.button("Participants", key=f"part_{event['id']}"):
                    view_participants(event['id'])
        
        st.divider()

def save_event(**kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO events (
                title, description, organizer_id, event_type,
                event_date, event_time, location,
                max_participants, fee, registration_deadline
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs['title'], kwargs['description'], st.session_state.user_id,
            kwargs['event_type'], kwargs['event_date'], kwargs['event_time'],
            kwargs['location'], kwargs.get('max_participants'),
            kwargs['fee'], kwargs.get('registration_deadline')
        ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")
        return False
    finally:
        conn.close()

def show_event_details(event_id):
    st.info(f"Detailed view for event {event_id} would open here")

def manage_event(event_id):
    st.info(f"Management interface for event {event_id} would open here")

def view_participants(event_id):
    st.info(f"Participants list for event {event_id} would open here")
