import streamlit as st
import pandas as pd
from utils.database import get_db_connection

def show():
    st.title("👥 Student Management")
    
    # Check if user is admin
    if st.session_state.user_role != 'admin':
        st.error("Access denied. Admin privileges required.")
        return
    
    tab1, tab2, tab3 = st.tabs(["All Students", "Add Student", "Reports"])
    
    with tab1:
        show_all_students()
    
    with tab2:
        add_student()
    
    with tab3:
        show_reports()

def show_all_students():
    st.subheader("All Students")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search = st.text_input("Search by name or roll number")
    
    with col2:
        department = st.selectbox(
            "Department",
            ["All", "Computer Science", "Electronics", "Mechanical", "Civil", 
             "Electrical", "AI & ML", "Data Science"]
        )
    
    with col3:
        batch = st.selectbox(
            "Batch",
            ["All", "2020-2024", "2021-2025", "2022-2026", "2023-2027", "2024-2028"]
        )
    
    # Get students
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT 
            u.id, u.username, u.email, u.created_at, u.is_active,
            s.full_name, s.batch, s.department, s.roll_number, s.contact_number
        FROM users u
        JOIN students s ON u.id = s.user_id
        WHERE u.role = 'student'
    '''
    
    params = []
    
    if search:
        query += " AND (s.full_name LIKE ? OR s.roll_number LIKE ? OR u.username LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if department != "All":
        query += " AND s.department = ?"
        params.append(department)
    
    if batch != "All":
        query += " AND s.batch = ?"
        params.append(batch)
    
    query += " ORDER BY u.created_at DESC"
    
    cursor.execute(query, tuple(params))
    students = cursor.fetchall()
    
    if students:
        # Convert to DataFrame for display
        df_data = []
        for student in students:
            df_data.append({
                'ID': student['id'],
                'Name': student['full_name'],
                'Username': student['username'],
                'Roll No': student['roll_number'],
                'Batch': student['batch'],
                'Department': student['department'],
                'Email': student['email'],
                'Joined': student['created_at'][:10],
                'Status': 'Active' if student['is_active'] else 'Inactive'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Actions for selected student
        st.subheader("Student Actions")
        
        selected_id = st.selectbox(
            "Select Student ID",
            [student['id'] for student in students]
        )
        
        col_a1, col_a2, col_a3 = st.columns(3)
        
        with col_a1:
            if st.button("View Profile", use_container_width=True):
                view_student_profile(selected_id)
        
        with col_a2:
            if st.button("Deactivate/Activate", use_container_width=True):
                toggle_student_status(selected_id)
                st.rerun()
        
        with col_a3:
            if st.button("Delete Student", use_container_width=True):
                delete_student(selected_id)
                st.rerun()
    else:
        st.info("No students found")
    
    conn.close()

def add_student():
    st.subheader("Add New Student")
    
    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            email = st.text_input("Email*")
        
        with col2:
            full_name = st.text_input("Full Name*")
            roll_number = st.text_input("Roll Number*")
            batch = st.text_input("Batch*")
        
        department = st.selectbox(
            "Department*",
            ["Computer Science", "Electronics", "Mechanical", "Civil", 
             "Electrical", "AI & ML", "Data Science", "Other"]
        )
        
        contact_number = st.text_input("Contact Number")
        
        submitted = st.form_submit_button("Add Student", type="primary")
        
        if submitted:
            # Basic validation
            if not all([username, password, email, full_name, roll_number, batch, department]):
                st.error("Please fill all required fields (*)")
            else:
                # Register student
                from app import register_user
                success, message = register_user(
                    username=username,
                    password=password,
                    email=email,
                    role='student',
                    full_name=full_name,
                    batch=batch,
                    department=department,
                    roll_number=roll_number,
                    contact_number=contact_number
                )
                
                if success:
                    st.success("Student added successfully!")
                    st.balloons()
                else:
                    st.error(f"Failed to add student: {message}")

def show_reports():
    st.subheader("Student Reports")
    
    # Statistics
    conn = get_db_connection()
    cursor = conn.cursor()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        total_students = cursor.fetchone()[0]
        st.metric("Total Students", total_students)
    
    with col2:
        cursor.execute("SELECT COUNT(DISTINCT department) FROM students")
        departments = cursor.fetchone()[0]
        st.metric("Departments", departments)
    
    with col3:
        cursor.execute("SELECT COUNT(DISTINCT batch) FROM students")
        batches = cursor.fetchone()[0]
        st.metric("Batches", batches)
    
    # Department distribution
    st.subheader("Department Distribution")
    
    cursor.execute("SELECT department, COUNT(*) as count FROM students GROUP BY department")
    dept_data = cursor.fetchall()
    
    if dept_data:
        import pandas as pd
        df = pd.DataFrame(dept_data, columns=['Department', 'Count'])
        st.dataframe(df, use_container_width=True)
    
    conn.close()

def view_student_profile(student_id):
    st.info(f"Viewing profile of student {student_id}")

def toggle_student_status(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_active FROM users WHERE id = ?", (student_id,))
    current_status = cursor.fetchone()[0]
    
    new_status = 0 if current_status else 1
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, student_id))
    conn.commit()
    
    action = "deactivated" if new_status == 0 else "activated"
    st.success(f"Student {action} successfully!")
    
    conn.close()

def delete_student(student_id):
    if st.checkbox("Confirm deletion (this action is permanent)"):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (student_id,))
            conn.commit()
            st.success("Student deleted successfully!")
        except Exception as e:
            st.error(f"Error deleting student: {e}")
        finally:
            conn.close()
