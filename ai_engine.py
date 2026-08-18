import streamlit as st
from google import genai
from google.genai import types

# Initialize the Gemini API client using secrets.toml
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_conversation_hooks(target_name: str, reflection_text: str, interest_text: str, observation_text: str) -> str:
    """
    Engine 1: Takes RIO inputs and generates actionable conversation hooks.
    """
    prompt = f"""
    You are helping me send a casual text message to my friend, {target_name}.
    
    Here is my context:
    - Reflection: {reflection_text}
    - Interests: {interest_text}
    - Observations: {observation_text}
    
    Task: Generate exactly 4 casual conversation starters based strictly on this data.
    
    Strict Rules:
    1. Keep it short and punchy (1 to 2 sentences maximum).
    2. Sound like a real, normal person texting on WhatsApp.
    3. NEVER use formal, cheesy, or overly enthusiastic words. 
    4. DO NOT invent facts, memories, or scenarios. Only use the exact details provided in the context.
    5. Format as a simple numbered list. Do not include any introductory or concluding text.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return "API_ERROR_QUOTA_EXHAUSTED"


def refine_generic_hook(generic_hook: str, original_rio_notes: str) -> str:
    """
    Engine 2: Socratic coach that helps deepen a specific generic hook.
    """
    prompt = f"""
    You are a Socratic communication coach. The user wants to start a conversation using this hook:
    "{generic_hook}"

    Here is the background R.I.O. context available for this person:
    {original_rio_notes}

    Task:
    Ask the user 1 or 2 targeted, probing questions to help them recall a specific detail, memory, or feeling from their context. 
    Do not rewrite the hook yet; your goal is purely to prompt the user for richer details so they can make the hook 10x better.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return "API_ERROR_QUOTA_EXHAUSTED"


def chat_as_persona(contact_name: str, personality_traits: list, location_setting: str, chat_history: str, user_latest_message: str) -> str:
    """
    Engine 3: Roleplay persona for practice chat mode.
    """
    traits_str = ", ".join(personality_traits) if isinstance(personality_traits, list) else personality_traits
    
    system_instruction = f"""
    You are roleplaying as {contact_name}.
    Personality traits: {traits_str}.
    Current location/setting: {location_setting}.

    Strict Behavioral Rules:
    1. Stay 100% in character at all times. Never break character or acknowledge that you are an AI.
    2. Adjust your conversational energy, resistance, and style strictly to your personality traits.
    3. Keep your responses realistic for casual messaging or spoken chat—concise and natural.
    """

    # --- LOGIC: REDUCE TOKENS ---
    # Split the history into lines, and only keep the last 14 lines (approx 7 exchanges)
    history_lines = chat_history.split("\n")
    recent_history = "\n".join(history_lines[-14:]) 

    full_prompt = f"""
    Recent Conversation History:
    {recent_history}

    User: {user_latest_message}
    {contact_name}:
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        return "API_ERROR_QUOTA_EXHAUSTED"


def evaluate_practice_session(full_chat_transcript: str, contact_name: str) -> str:
    """
    Engine 4: Post-chat auditor that provides scoring and feedback.
    """
    prompt = f"""
    You are a master interpersonal communication coach. Review the following practice conversation transcript between the user and {contact_name}:

    --- TRANSCRIPT START ---
    {full_chat_transcript}
    --- TRANSCRIPT END ---

    Task:
    Provide a direct, honest evaluation of the user's conversational skill during this chat.
    Structure your response strictly in this layout:

    ### Score: X/10

    ### Strengths
    * [Bullet point 1]
    * [Bullet point 2]

    ### Weaknesses & Areas for Growth
    * [Bullet point 1]
    * [Bullet point 2]

    ### Key Takeaway for Real Life
    [1-2 sentences summarizing the most critical improvement to make before talking to {contact_name} in person.]
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
         return "API_ERROR_QUOTA_EXHAUSTED"