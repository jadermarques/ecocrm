import streamlit as st
import pandas as pd
from api_client import APIClient

st.title("👥 User Management")
st.caption("Manage system users and permissions")

client = APIClient()

# Tab structure
tab1, tab2 = st.tabs(["User List", "Create New User"])

# --- User List Tab ---
with tab1:
    st.subheader("Existing Users")
    
    if st.button("🔄 Refresh List", key="refresh_users"):
        st.rerun()
    
    users = client.list_users()
    
    if users:
        # Prepare data for display
        user_data = []
        for user in users:
            user_data.append({
                "ID": user.get("id"),
                "Email": user.get("email"),
                "Full Name": user.get("full_name"),
                "Role": user.get("role"),
                "Active": "✅" if user.get("is_active") else "❌",
                "Superuser": "⭐" if user.get("is_superuser") else "",
            })
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.caption(f"Total Users: {len(users)}")
    else:
        st.info("No users found in the system.")

# --- Create User Tab ---
with tab2:
    st.subheader("Create New User")
    
    with st.form("create_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email *", 
                placeholder="user@example.com",
                help="User's email address (used for login)"
            )
            full_name = st.text_input(
                "Full Name *", 
                placeholder="John Doe",
                help="User's display name"
            )
        
        with col2:
            password = st.text_input(
                "Password *", 
                type="password",
                placeholder="Minimum 8 characters",
                help="Initial password (user should change after first login)"
            )
            role = st.selectbox(
                "Role *",
                options=["user", "admin", "agent"],
                help="User role determines access level"
            )
        
        is_superuser = st.checkbox(
            "Superuser",
            help="Superusers have full system access (use with caution)"
        )
        
        st.divider()
        
        submitted = st.form_submit_button("🆕 Create User", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            if not email or not password or not full_name:
                st.error("❌ Please fill all required fields (marked with *)")
            elif len(password) < 8:
                st.error("❌ Password must be at least 8 characters long")
            elif "@" not in email:
                st.error("❌ Please enter a valid email address")
            else:
                # Create user
                user_data = {
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "role": role,
                    "is_superuser": is_superuser
                }
                
                with st.spinner("Creating user..."):
                    result = client.create_user(user_data)
                
                if result and "error" not in result:
                    st.success(f"✅ User '{email}' created successfully!")
                    st.balloons()
                    st.info("💡 Tip: Switch to the 'User List' tab to see the new user.")
                else:
                    error_msg = result.get("error", "Unknown error") if result else "Connection error"
                    st.error(f"❌ Failed to create user: {error_msg}")

# Info section
with st.expander("ℹ️ Role Descriptions"):
    st.markdown("""
    **Role Definitions:**
    
    - **User**: Standard user with basic access to the system
    - **Admin**: Administrative user with elevated permissions
    - **Agent**: Service agent with access to bot and customer management tools
    
    **Superuser Status:**
    - Superusers have unrestricted access to all system features
    - Only grant superuser status to trusted administrators
    """)
