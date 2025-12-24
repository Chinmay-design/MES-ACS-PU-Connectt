import streamlit as st
import re
from app import register_user

def show():
    st.title("👨‍🎓 Alumni Registration")
    
    with st.form("alumni_signup_form"):
        st.subheader("Join the Alumni Network")
        
        # Account Information
        st.write("### Account Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            email = st.text_input("Email*")
        
        with col2:
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
        
        # Professional Information
        st.divider()
        st.write("### Professional Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            full_name = st.text_input("Full Name*")
            graduation_year = st.number_input(
                "Graduation Year*",
                min_value=1950,
                max_value=2024,
                value=2020
            )
            current_position = st.text_input("Current Position*")
        
        with col4:
            company = st.text_input("Company/Organization*")
            linkedin_url = st.text_input("LinkedIn Profile URL")
        
        # Additional Information
        expertise_area = st.text_input("Area of Expertise")
        
        # Terms
        terms = st.checkbox("I agree to the Terms and Conditions*")
        
        submitted = st.form_submit_button("Register as Alumni", type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            # Required fields
            required = [username, email, password, confirm_password, 
                       full_name, current_position, company]
            if not all(required):
                errors.append("All fields marked with * are required")
            
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append("Invalid email format")
            
            if not terms:
                errors.append("You must agree to the terms")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                success, message = register_user(
                    username=username,
                    password=password,
                    email=email,
                    role='alumni',
                    full_name=full_name,
                    graduation_year=graduation_year,
                    current_position=current_position,
                    company=company,
                    linkedin_url=linkedin_url,
                    expertise_area=expertise_area
                )
                
                if success:
                    st.success("Alumni registration successful! Please login.")
                    st.balloons()
                else:
                    st.error(f"Registration failed: {message}")
