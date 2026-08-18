import streamlit as st
from supabase import create_client, Client

# Initialize the Supabase client using secrets.toml
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supasafe: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- 1. USER AUTHENTICATION & FETCHING ---

def fetch_user(usern: str, mode: str = "verification"):
    """
    Fetches user record from the Users table by Username.
    """
    try:
        response = supasafe.table("Users").select("*").eq("Username", usern).execute()
        return response.data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return []


# --- 2. CONTACTS MANAGEMENT (PAGE 2, 3, 6) ---

def get_user_contacts(username: str):
    """
    Fetches all contact profiles created by a specific user.
    """
    try:
        response = supasafe.table("contacts").select("*").eq("username", username).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching contacts: {e}")
        return []

def create_contact(username: str, contact_name: str):
    """
    Creates a new contact profile for the logged-in user.
    """
    try:
        payload = {
            "username": username,
            "contact_name": contact_name,
            "reflection": "",
            "interest": "",
            "observation": "",
            "personality_traits": []
        }
        response = supasafe.table("contacts").insert(payload).execute()
        return response.data
    except Exception as e:
        st.error(f"Error creating contact: {e}")
        return None

def delete_contact(contact_id: str):
    """
    Deletes a contact profile and associated data.
    """
    try:
        supasafe.table("contacts").delete().eq("id", contact_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting contact: {e}")
        return False

def update_contact_rio(contact_id: str, reflection: str, interest: str, observation: str):
    """
    Updates the Reflection, Interest, and Observation fields for a contact (Page 3).
    """
    try:
        payload = {
            "reflection": reflection,
            "interest": interest,
            "observation": observation
        }
        response = supasafe.table("contacts").update(payload).eq("id", contact_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error saving RIO notes: {e}")
        return None

def update_contact_settings(contact_id: str, contact_name: str, personality_traits: list):
    """
    Updates contact name and personality traits (Page 6).
    """
    try:
        payload = {
            "contact_name": contact_name,
            "personality_traits": personality_traits
        }
        response = supasafe.table("contacts").update(payload).eq("id", contact_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating contact settings: {e}")
        return None


# --- 3. DATA POINTS & HOOKS (PAGE 4, 5) ---

def save_data_points(contact_id: str, hooks: list):
    """
    Saves generated conversation hooks for a contact.
    Clears old generated hooks first to avoid duplicates.
    """
    try:
        # Clear existing unrefined points for fresh generation
        supasafe.table("data_points").delete().eq("contact_id", contact_id).execute()
        
        payload = [{"contact_id": contact_id, "hook_text": h, "is_refined": False} for h in hooks]
        response = supasafe.table("data_points").insert(payload).execute()
        return response.data
    except Exception as e:
        st.error(f"Error saving data points: {e}")
        return None

def get_data_points(contact_id: str):
    """
    Retrieves all hooks associated with a contact.
    """
    try:
        response = supasafe.table("data_points").select("*").eq("contact_id", contact_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching data points: {e}")
        return []

def update_data_point(data_point_id: str, refined_text: str):
    """
    Updates a generic hook into a refined, deepened data point (Page 5).
    """
    try:
        payload = {
            "hook_text": refined_text,
            "is_refined": True
        }
        response = supasafe.table("data_points").update(payload).eq("id", data_point_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error refining data point: {e}")
        return None


# --- 4. PRACTICE SESSION REVIEWS (PAGE 8) ---

def save_practice_session(contact_id: str, transcript: str, evaluation_report: str):
    """
    Saves chat transcript and AI audit report to practice_sessions.
    """
    try:
        payload = {
            "contact_id": contact_id,
            "transcript": transcript,
            "evaluation_report": evaluation_report
        }
        response = supasafe.table("practice_sessions").insert(payload).execute()
        return response.data
    except Exception as e:
        st.error(f"Error saving practice session: {e}")
        return None