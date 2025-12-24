import streamlit as st
import re
from app import register_user

def show():
    st.title("🎓 Student Registration")
    
    with st.form("student_signup_form", clear_on_submit=False):
        st.subheader("Create Your Account")
        
        # Account Information
        st.write("### Account Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Username*",
                help="Choose a unique username (4-20 characters)"
            )
            email = st.text_input(
                "Email*",
                help="Use your college email if possible"
            )
        
        with col2:
            password = st.text_input(
                "Password*",
                type="password",
                help="At least 8 characters"
            )
            confirm_password = st.text_input(
                "Confirm Password*",
                type="password"
            )
        
        # Personal Information
        st.divider()
        st.write("### Personal Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            full_name = st.text_input("Full Name*")
            batch = st.selectbox(
                "Batch*",
                ["2020-2024", "2021-2025", "2022-2026", "2023-2027", "2024-2028", "Other"]
            )
        
        with col4:
            department = st.selectbox(
                "Department*",
                [
                    "Computer Science and Engineering",
                    "Electronics and Communication Engineering",
                    "Mechanical Engineering",
                    "Civil Engineering",
                    "Electrical and Electronics Engineering",
                    "Artificial Intelligence and Machine Learning",
                    "Data Science",
                    "Information Science",
                    "Other"
                ]
            )
            roll_number = st.text_input("Roll Number*")
        
        # Additional Information
        st.divider()
        st.write("### Additional Information")
        
        contact_number = st.text_input("Contact Number")
        
        # Terms and Conditions
        st.divider()
        
        terms_accepted = st.checkbox("I agree to the Terms and Conditions*", value=False)
        
        # Submit button
        submitted = st.form_submit_button("Create Account", type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            # Required fields
            required = [username, email, password, confirm_password, 
                       full_name, batch, department, roll_number]
            if not all(required):
                errors.append("All fields marked with * are required")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if len(password) < 6:
                errors.append("Password must be at least 6 characters")
            
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append("Invalid email format")
            
            if not terms_accepted:
                errors.append("You must agree to the terms")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Register user
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
                    st.success("🎉 Registration successful! Please login.")
                    st.balloons()
                else:
                    st.error(f"Registration failed: {message}")
