import streamlit as st
import time
from api_connect import (supasafe, fetch_user, get_user_contacts, create_contact, delete_contact, 
                         update_contact_rio, update_contact_settings, save_data_points, 
                         get_data_points, update_data_point, save_practice_session)
from ai_engine import (generate_conversation_hooks, refine_generic_hook, 
                        chat_as_persona, evaluate_practice_session)

# --- STATE MANAGEMENT ---
if "navigation" not in st.session_state:
    st.session_state.navigation = {"phase": 0}
if "username" not in st.session_state:
    st.session_state.username = None
if "current_contact" not in st.session_state:
    st.session_state.current_contact = None
if "selected_hook" not in st.session_state:
    st.session_state.selected_hook = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

def change_phase(new_phase):
    st.session_state.navigation["phase"] = new_phase
    st.rerun()

phase = st.session_state.navigation["phase"]

# --- PAGE 1: LOGIN / REGISTER ---
if phase == 0:
    st.title("RIO: Conversation Architect")
    tabs1, tabs2 = st.tabs(["Login", "Register"])
    
    with tabs1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            auth = fetch_user(username)
            if auth and auth[0]["Password"] == password: 
                st.session_state.username = username
                st.success("Logged in successfully!")
                time.sleep(1)
                change_phase(1)
            else:
                st.error("Invalid credentials")
                
    with tabs2:
        new_username = st.text_input("New Username", key="reg_user")
        new_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            if new_username and new_password:
                try:
                    supasafe.table("Users").insert({"Username": new_username, "Password": new_password}).execute()
                    st.success("Account setup! Proceed to login.")
                except Exception as e:
                    st.error(f"Error saving to database: {e}")
            else:
                st.warning("Please enter a username and password.")

# --- PAGE 2: USERS PROFILE DASHBOARD ---
elif phase == 1:
    st.header("Your Contacts")
    contacts = get_user_contacts(st.session_state.username)
    
    for c in contacts:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"👤 {c['contact_name']}", key=c['id']):
                st.session_state.current_contact = c
                change_phase(2)
        with col2:
            if st.button("❌", key=f"del_{c['id']}"):
                delete_contact(c['id'])
                st.rerun()
                
    st.divider()
    new_contact_name = st.text_input("Create new profile")
    if st.button("+ Create new"):
        if new_contact_name:
            create_contact(st.session_state.username, new_contact_name)
            st.rerun()


# --- PAGE 3: CLICKING ON A USER (RIO ENTRY) ---
elif phase == 2:
    contact = st.session_state.current_contact
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(f"{contact['contact_name']}'s Profile")
    with col2:
        if st.button("⚙️ Settings"):
            change_phase(5)
            
    if st.button("🔙 Back to Contacts"):
        change_phase(1)

    st.subheader("R.I.O Data")
    ref = st.text_area("Reflection (Memories, context):", value=contact.get("reflection", ""))
    obs = st.text_area("Observation (What you noticed):", value=contact.get("observation", ""))
    int_ = st.text_area("Interest (What they love):", value=contact.get("interest", ""))
    
    if st.button("💾 Save Profile"):
        update_contact_rio(contact['id'], ref, int_, obs)
        st.session_state.current_contact['reflection'] = ref
        st.session_state.current_contact['observation'] = obs
        st.session_state.current_contact['interest'] = int_
        st.success("Saved!")

    if st.button("🚀 Generate Data Points"):
        with st.spinner("Analyzing profile..."):
            hooks_text = generate_conversation_hooks(
                contact['contact_name'], ref, int_, obs
            )
            if hooks_text == "API_ERROR_QUOTA_EXHAUSTED":
                st.error("API limit reached. Please wait a moment and try again.")
            else:
                hooks_list = [h.strip() for h in hooks_text.split("\n") if h.strip()]
                save_data_points(contact['id'], hooks_list)
                change_phase(3)


# --- PAGE 4: GENERATED DATA POINTS ---
elif phase == 3:
    contact = st.session_state.current_contact
    st.header(f"Data Points for {contact['contact_name']}")
    
    if st.button("🔙 Back to Profile"):
        change_phase(2)

    data_points = get_data_points(contact['id'])
    
    for dp in data_points:
        if st.button(dp['hook_text'], key=dp['id']):
            st.session_state.selected_hook = dp
            change_phase(4)
            
    st.divider()
    if st.button("🎙️ Practice (Simulate Chat)"):
        st.session_state.chat_history = ""
        change_phase(6)


# --- PAGE 5: DEEPENING A DATA POINT ---
elif phase == 4:
    hook = st.session_state.selected_hook
    contact = st.session_state.current_contact
    st.subheader("Refine Data Point")
    st.info(f"Current Hook: {hook['hook_text']}")
    
    if st.button("🔙 Back to Data Points"):
        change_phase(3)
        
    original_notes = f"Ref: {contact['reflection']} | Obs: {contact['observation']} | Int: {contact['interest']}"
    
    if st.button("Ask AI to help me articulate better"):
        with st.spinner("Thinking..."):
            coaching_q = refine_generic_hook(hook['hook_text'], original_notes)
            if coaching_q == "API_ERROR_QUOTA_EXHAUSTED":
                st.error("API limit reached. Please wait a moment and try again.")
            else:
                st.write(coaching_q)
            
    refined_input = st.text_input("Enter your newly refined data point:")
    if st.button("Save Refined Hook"):
        update_data_point(hook['id'], refined_input)
        st.success("Saved!")
        time.sleep(1)
        change_phase(3)


# --- PAGE 6: USER SETTINGS ---
elif phase == 5:
    contact = st.session_state.current_contact
    st.header("Edit Personality")
    if st.button("🔙 Back"):
        change_phase(2)
        
    edit_name = st.text_input("Name", value=contact['contact_name'])
    traits = st.multiselect("Personality Traits:", 
                            ["Humorous", "Shy", "Chatty", "Direct", "Sarcastic", "Intellectual"], 
                            default=contact.get('personality_traits', []))
    
    if st.button("Save Settings"):
        update_contact_settings(contact['id'], edit_name, traits)
        st.session_state.current_contact['contact_name'] = edit_name
        st.session_state.current_contact['personality_traits'] = traits
        st.success("Updated!")


# --- PAGE 7: PRACTICE CHAT ---
elif phase == 6:
    contact = st.session_state.current_contact
    st.header(f"Practice with {contact['contact_name']}")
    
    location = st.selectbox("Setting:", ["WhatsApp", "In the parlour", "At a cafe", "At work"])
    
    if st.button("End & Evaluate"):
        change_phase(7)
        
    st.divider()
    st.text_area("Chat History", value=st.session_state.chat_history, height=300, disabled=True)
    
    user_msg = st.chat_input(f"Type your message to {contact['contact_name']}...")
    
    if user_msg:
        st.session_state.chat_history += f"\nYou: {user_msg}"
        with st.spinner(f"{contact['contact_name']} is typing..."):
            ai_reply = chat_as_persona(
                contact['contact_name'], 
                contact.get('personality_traits', []), 
                location, 
                st.session_state.chat_history, 
                user_msg
            )
            
        if ai_reply == "API_ERROR_QUOTA_EXHAUSTED":
            st.error("⚠️ The AI needs a breather. You've hit the API limit for now. Please wait a moment before sending another message.")
            st.session_state.chat_history = st.session_state.chat_history.rsplit(f"\nYou: {user_msg}", 1)[0]
        else:
            st.session_state.chat_history += f"\n{contact['contact_name']}: {ai_reply}"
            
        st.rerun()


# --- PAGE 8: POST-CHAT EVALUATION ---
elif phase == 7:
    contact = st.session_state.current_contact
    st.header("Session Review")
    
    if st.button("🏠 Back to Dashboard"):
        change_phase(1)
        
    with st.spinner("Analyzing conversation..."):
        evaluation = evaluate_practice_session(st.session_state.chat_history, contact['contact_name'])
        if evaluation == "API_ERROR_QUOTA_EXHAUSTED":
             st.error("API limit reached. Could not generate evaluation.")
        else:
             st.markdown(evaluation)
        
    if st.button("💾 Save Review") and evaluation != "API_ERROR_QUOTA_EXHAUSTED":
        save_practice_session(contact['id'], st.session_state.chat_history, evaluation)
        st.success("Review saved!")