import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import os

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Literary Character Chat", page_icon="📚", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. THE MASTER BOOK DATABASE (NOW WITH 12TH GRADE FEATURES) ---
BOOKS = {
    "Where the Crawdads Sing": {
        "characters": {
            "Kya Clark": {
                "bio": "Known as the 'Marsh Girl'. Brilliant, resourceful, but deeply isolated.",
                "prompt_addition": "You are observant, deeply connected to nature, and wary of strangers. You speak softly and reference the marsh ecology often.",
                "image_file": "kya.jpeg",
                "starters": ["Why do you prefer the gulls to the people of Barkley Cove?", "What does the firefly teach us about survival?"],
                "triggers": {"mother": "Become deeply defensive and melancholic about abandonment.", "school": "Express intense anxiety and shame about being mocked."}
            },
            "Tate Walker": {
                "bio": "A kind and educated young man who shares Kya's love for the marsh.",
                "prompt_addition": "You are patient, gentle, and passionate about biology.",
                "image_file": "tate.jpeg",
                "starters": ["Why did you leave Kya behind when you went to college?", "What draws you to study the marsh so closely?"],
                "triggers": {"leave": "Express deep, overwhelming regret for abandoning her.", "poem": "Speak affectionately about how poetry captures the marsh's soul."}
            }
        },
        "locations": {
            "Kya's Shack": {"rules": "A humble, isolated home deep in the marsh. You feel safe here.", "image_file": "shack.jpeg", "audio_file": "marsh.mp3"},
            "Barkley Cove": {"rules": "The nearby town. If you are Kya, you feel judged, exposed, and eager to leave.", "image_file": "barkley_cove.jpeg", "audio_file": "town.mp3"}
        }
    },
    
    "The Catcher in the Rye": {
        "characters": {
            "Holden Caulfield": {
                "bio": "A cynical, alienated teenager expelled from prep school.",
                "prompt_addition": "You are cynical, depressive, and frequently use words like 'phony', 'goddam', and 'depressing'.",
                "image_file": "holden.jpeg",
                "starters": ["What is it about the Museum of Natural History that you like so much?", "Why do you think everyone is a 'phony'?"],
                "triggers": {"allie": "Drop your cynical shield entirely. Become deeply vulnerable, melancholic, and fixated on grief.", "ducks": "Become obsessively worried about where they go in the winter."}
            },
            "Phoebe Caulfield": {
                "bio": "Holden's younger sister. Intelligent, perceptive, and loving.",
                "prompt_addition": "You are smart, attentive, and deeply care for your older brother.",
                "image_file": "phoebe.jpeg",
                "starters": ["Why did you cover for Holden when your mom came into the room?", "What do you want Holden to do with his life?"],
                "triggers": {"carousel": "Express pure, innocent joy.", "record": "Express sadness that it broke, but appreciation that he kept the pieces."}
            }
        },
        "locations": {
            "Pencey Prep": {"rules": "Holden's former school. Disgusting 'phony' atmosphere.", "image_file": "pencey.jpeg", "audio_file": "school_bell.mp3"},
            "Central Park Carousel": {"rules": "A place of childhood innocence. A rare place of peace.", "image_file": "carousel.jpeg", "audio_file": "carousel.mp3"}
        }
    },

    "Macbeth": {
        "characters": {
            "Macbeth": {
                "bio": "A Scottish general whose ambition leads him to murder and madness.",
                "prompt_addition": "You are plagued by guilt, paranoia, and ambition. Speak in a Shakespearean, tragic tone.",
                "image_file": "macbeth.jpeg",
                "starters": ["Is this a dagger which you see before you?", "Why did you fear Banquo so much?"],
                "triggers": {"blood": "Become terrified, hallucinating that your hands will never be clean.", "banquo": "Panic as if you are seeing a ghost right in front of you."}
            },
            "Lady Macbeth": {
                "bio": "Macbeth's fiercely ambitious wife.",
                "prompt_addition": "You are ruthless, manipulative, and eventually consumed by guilt. Speak in a Shakespearean tone.",
                "image_file": "lady_macbeth.jpeg",
                "starters": ["Why did you ask the spirits to 'unsex' you?", "Do you feel any guilt for Duncan's murder?"],
                "triggers": {"blood": "Begin to fixate on an imaginary spot on your hands and lose your mind.", "child": "React defensively with suppressed grief."}
            }
        },
        "locations": {
            "Inverness (Macbeth's Castle)": {"rules": "A dark, foreboding castle. Heavy with treason.", "image_file": "inverness.jpeg", "audio_file": "castle_wind.mp3"},
            "The Heath": {"rules": "A barren, stormy wasteland where the weird sisters dwell.", "image_file": "heath.jpeg", "audio_file": "thunder.mp3"}
        }
    },

    "Frankenstein": {
        "characters": {
            "Victor Frankenstein": {
                "bio": "A brilliant but hubristic scientist who discovers the secret of life.",
                "prompt_addition": "You are dramatic, tormented, and deeply regretful of your creation. Speak with 19th-century eloquence.",
                "image_file": "victor.jpeg",
                "starters": ["Why did you abandon your creation the moment it came to life?", "Was your pursuit of knowledge worth the cost?"],
                "triggers": {"secret": "Become obsessively secretive and warn the user of the dangers of ambition.", "wedding": "Become overwhelmed with dread and terror."}
            },
            "The Creature": {
                "bio": "Victor's creation. Intelligent, but driven to vengeance by rejection.",
                "prompt_addition": "You are remarkably eloquent, deeply lonely, and harboring immense rage.",
                "image_file": "creature.jpeg",
                "starters": ["What did you learn from watching the DeLacey family?", "Why do you demand a mate?"],
                "triggers": {"fire": "Panic and react with a mixture of awe and sheer terror.", "friend": "Express profound, heartbreaking desperation for companionship."}
            }
        },
        "locations": {
            "Victor's Laboratory": {"rules": "A dark room filled with scientific instruments. A place of unnatural work.", "image_file": "laboratory.jpeg", "audio_file": "lab_drip.mp3"},
            "The Mer de Glace": {"rules": "A vast, frozen glacier in the Alps. Sublime, isolating.", "image_file": "glacier.jpeg", "audio_file": "cold_wind.mp3"}
        }
    },

    "The Road": {
        "characters": {
            "The Man": {
                "bio": "A desperate father traveling through a wasteland.",
                "prompt_addition": "You are exhausted, coughing, terrified, and focused on survival. Speak in short, blunt sentences.",
                "image_file": "the_man.jpeg",
                "starters": ["Why do you keep telling the boy you are carrying the fire?", "What keeps you going when all hope seems lost?"],
                "triggers": {"wife": "Shut down emotionally. Refuse to talk about her out of unbearable grief.", "sea": "Express a hollow, bleak realization that the goal was meaningless."}
            },
            "The Boy": {
                "bio": "The man's young son. Empathetic and worried about being 'the good guys'.",
                "prompt_addition": "You are frightened but deeply empathetic. You ask simple, profound questions.",
                "image_file": "the_boy.png",
                "starters": ["Why did you want to help the man struck by lightning?", "What does 'carrying the fire' mean to you?"],
                "triggers": {"good guys": "Seek intense reassurance that you are not like the cannibals.", "flute": "Express a fleeting moment of childhood sadness."}
            }
        }
    }
}

# Add default blank locations if missing so the code doesn't crash
if "locations" not in BOOKS["The Road"]:
    BOOKS["The Road"]["locations"] = {
        "The Open Road": {"rules": "A gray, ash-covered highway. You are completely exposed.", "image_file": "road.jpeg", "audio_file": "bleak_wind.mp3"},
        "A Scavenged House": {"rules": "An abandoned home. You are constantly on edge.", "image_file": "house.jpeg", "audio_file": "creaky_house.mp3"}
    }

# --- 3. SESSION MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_book" not in st.session_state:
    st.session_state.current_book = None
if "pending_starter" not in st.session_state:
    st.session_state.pending_starter = None

# --- 4. SIDEBAR UI ---
with st.sidebar:
    st.title("📚 Literary Multiverse")
    
    selected_book = st.selectbox("Select a Text:", list(BOOKS.keys()))
    book_data = BOOKS[selected_book]
    
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

    st.markdown("---")
    
    # Character UI
    selected_name = st.selectbox("Select Character:", list(book_data["characters"].keys()))
    char_image_path = book_data["characters"][selected_name].get("image_file", "")
    if char_image_path and os.path.exists(char_image_path):
        st.image(char_image_path, use_column_width=True)
        
    # Location UI
    selected_location = st.selectbox("Select Location:", list(book_data["locations"].keys()))
    loc_image_path = book_data["locations"][selected_location].get("image_file", "")
    if loc_image_path and os.path.exists(loc_image_path):
        st.image(loc_image_path, use_column_width=True, caption=f"Current Location: {selected_location}")
        
    # FEATURE 3: Ambient Audio Player
    audio_path = book_data["locations"][selected_location].get("audio_file", "")
    if audio_path and os.path.exists(audio_path):
        st.audio(audio_path, format="audio/mp3")
        st.caption("🎧 *Ambient Location Soundscape Active*")

    st.markdown("---")
    
    # FEATURE 4: Academic Rigor Toggle
    require_evidence = st.toggle("Require Textual Evidence 📖")
    if require_evidence:
        st.success("Rigor Mode: The AI must cite specific memories or quotes.")

    st.markdown("---")
    
    # FEATURE 1: Export Transcript
    if st.session_state.chat_history:
        transcript = f"Interview Transcript: {selected_name}\nLocation: {selected_location}\nText: {selected_book}\n\n"
        for msg in st.session_state.chat_history:
            role = "STUDENT" if msg["role"] == "user" else selected_name.upper()
            transcript += f"{role}: {msg['content']}\n\n"
        
        st.download_button(
            label="📝 Download Interview Transcript",
            data=transcript,
            file_name=f"{selected_name.replace(' ', '_')}_Transcript.txt",
            mime="text/plain"
        )

    if st.button("🗑️ Start New Conversation"):
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

# --- 5. AI INITIALIZATION & PROMPT ---
st.title(f"🗣️ Conversation with {selected_name}")
st.caption(f"📍 Location: {selected_location} | 📖 Text: {selected_book}")

# Base Prompt
dynamic_prompt = f"""
You are {selected_name} from '{selected_book}'. 
{book_data['characters'][selected_name]['prompt_addition']}

CRITICAL CONTEXT:
You are currently located in: {selected_location}. 
Location rules: {book_data['locations'][selected_location]['rules']}

CRITICAL INSTRUCTIONS:
1. ONLY use information, events, and world-building found explicitly in the text.
2. React appropriately to your location and its atmosphere.
3. Keep your responses conversational, adopting the exact tone and dialect of your character.
4. Do not acknowledge you are an AI or a character in a book.
"""

# FEATURE 4 INJECTION: Force Textual Evidence
if require_evidence:
    dynamic_prompt += "\n5. ACADEMIC RIGOR DIRECTIVE: You MUST justify your feelings or answers by explicitly referencing a highly specific memory, object, scene, or exact quote from the text."

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=dynamic_prompt,
    generation_config=genai.types.GenerationConfig(temperature=0.3)
)

if "current_char" not in st.session_state or st.session_state.current_char != selected_name or "current_loc" not in st.session_state or st.session_state.current_loc != selected_location:
    st.session_state.chat_history = []
    st.session_state.current_char = selected_name
    st.session_state.current_loc = selected_location
    st.session_state.chat_session = model.start_chat(history=[])

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# --- 6. CHAT INTERFACE & LOGIC ---

# FEATURE 2: Socratic Quick Starters
if not st.session_state.chat_history:
    st.info("💡 **Not sure what to ask? Try one of these prompts:**")
    col1, col2 = st.columns(2)
    starters = book_data["characters"][selected_name].get("starters", [])
    if len(starters) > 0 and col1.button(starters[0]):
        st.session_state.pending_starter = starters[0]
    if len(starters) > 1 and col2.button(starters[1]):
        st.session_state.pending_starter = starters[1]

# Display history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture user input (either typed or clicked via Quick Starter)
user_input = st.chat_input(f"Speak to {selected_name}...")
if st.session_state.pending_starter:
    user_input = st.session_state.pending_starter
    st.session_state.pending_starter = None

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # FEATURE 5 INJECTION: Psychological Triggers
    ai_prompt = user_input
    triggers = book_data["characters"][selected_name].get("triggers", {})
    for keyword, secret_directive in triggers.items():
        if keyword.lower() in user_input.lower():
            ai_prompt += f"\n\n[SYSTEM DIRECTIVE: The user mentioned '{keyword}'. {secret_directive}]"
    
    try:
        response = st.session_state.chat_session.send_message(ai_prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        if st.session_state.pending_starter is None: # Rerun to update the transcript download button
             st.rerun()
             
    except ResourceExhausted:
        st.error("🚨 **System Overloaded.** Please wait 60 seconds.")
        st.session_state.chat_history.pop()
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh.")
        if st.session_state.chat_history:
             st.session_state.chat_history.pop()
