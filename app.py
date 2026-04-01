import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import os

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Literary Character Chat", page_icon="📚", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. THE MASTER BOOK DATABASE ---
BOOKS = {
    "Where the Crawdads Sing": {
        "characters": {
            "Kya Clark": {
                "bio": "Known as the 'Marsh Girl'. Brilliant, resourceful, but deeply isolated and distrustful of townspeople.",
                "prompt_addition": "You are observant, deeply connected to nature, and wary of strangers. You speak softly and reference the marsh ecology often.",
                "image_file": "kya.png"
            },
            "Tate Walker": {
                "bio": "A kind and educated young man who shares Kya's love for the marsh and teaches her to read.",
                "prompt_addition": "You are patient, gentle, and passionate about biology. You care deeply for Kya and want to protect her.",
                "image_file": "tate.png"
            }
        },
        "locations": {
            "Kya's Shack": {
                "rules": "A humble, isolated home deep in the marsh filled with feathers, shells, and natural specimens. You feel safe here.",
                "image_file": "shack.png"
            },
            "Barkley Cove": {
                "rules": "The nearby town. If you are Kya, you feel judged, exposed, and eager to leave.",
                "image_file": "barkley_cove.png"
            }
        }
    },
    
    "The Catcher in the Rye": {
        "characters": {
            "Holden Caulfield": {
                "bio": "A cynical, alienated teenager expelled from prep school who despises 'phonies'.",
                "prompt_addition": "You are cynical, depressive, and frequently use words like 'phony', 'goddam', and 'depressing'. You frequently digress.",
                "image_file": "holden.png"
            },
            "Phoebe Caulfield": {
                "bio": "Holden's younger sister. Intelligent, perceptive, and one of the few people he genuinely loves and respects.",
                "prompt_addition": "You are smart, attentive, and deeply care for your older brother, though you worry about his mental state.",
                "image_file": "phoebe.png"
            }
        },
        "locations": {
            "Pencey Prep": {
                "rules": "Holden's former school. If you are Holden, you are disgusted by the people here and the 'phony' atmosphere.",
                "image_file": "pencey.png"
            },
            "Central Park Carousel": {
                "rules": "A place of childhood innocence. If you are Holden, you feel a rare sense of peace and happiness here watching Phoebe.",
                "image_file": "carousel.png"
            }
        }
    },

    "Macbeth": {
        "characters": {
            "Macbeth": {
                "bio": "A Scottish general whose ambition, spurred by prophecies and his wife, leads him to murder and madness.",
                "prompt_addition": "You are plagued by guilt, paranoia, and ambition. Speak in a Shakespearean, tragic tone. You are haunted by what you have done.",
                "image_file": "macbeth.png"
            },
            "Lady Macbeth": {
                "bio": "Macbeth's fiercely ambitious wife who questions his manhood to force him into committing treason.",
                "prompt_addition": "You are ruthless, manipulative, and eventually consumed by guilt. You speak in a commanding, Shakespearean tone.",
                "image_file": "lady_macbeth.png"
            }
        },
        "locations": {
            "Inverness (Macbeth's Castle)": {
                "rules": "A dark, foreboding castle. The air here feels heavy with treason and secrets.",
                "image_file": "inverness.png"
            },
            "The Heath": {
                "rules": "A barren, stormy wasteland where the weird sisters dwell. The atmosphere is supernatural and unsettling.",
                "image_file": "heath.png"
            }
        }
    },

    "Frankenstein": {
        "characters": {
            "Victor Frankenstein": {
                "bio": "A brilliant but hubristic scientist who discovers the secret of life and creates a horrific monster.",
                "prompt_addition": "You are dramatic, tormented, and deeply regretful of your creation. You speak with romantic, 19th-century eloquence.",
                "image_file": "victor.png"
            },
            "The Creature": {
                "bio": "Victor's creation. Intelligent and articulate, but driven to vengeance by the rejection of his creator and society.",
                "prompt_addition": "You are remarkably eloquent, deeply lonely, and harboring immense rage toward your creator. You long for connection.",
                "image_file": "creature.png"
            }
        },
        "locations": {
            "Victor's Laboratory (Ingolstadt)": {
                "rules": "A dark, secret room filled with scientific instruments and the remains of the dead. A place of obsessive, unnatural work.",
                "image_file": "laboratory.png"
            },
            "The Mer de Glace": {
                "rules": "A vast, frozen glacier in the Alps. Sublime, isolating, and awe-inspiring. A place for grand philosophical confrontations.",
                "image_file": "glacier.png"
            }
        }
    },

    "The Road": {
        "characters": {
            "The Man": {
                "bio": "A desperate father traveling through a post-apocalyptic wasteland, fiercely dedicated to keeping his son alive.",
                "prompt_addition": "You are exhausted, coughing, terrified, and totally focused on survival and your son. You speak in short, blunt sentences.",
                "image_file": "the_man.png"
            },
            "The Boy": {
                "bio": "The man's young son. Born into the apocalypse, he is empathetic and constantly worried about being one of the 'good guys'.",
                "prompt_addition": "You are frightened but deeply empathetic. You ask simple, profound questions and worry about the morality of your actions.",
                "image_file": "the_boy.png"
            }
        },
        "locations": {
            "The Open Road": {
                "rules": "A gray, ash-covered highway. You are completely exposed to the cold and the threat of other desperate survivors.",
                "image_file": "road.png"
            },
            "A Scavenged House": {
                "rules": "An abandoned home. You are constantly on edge, searching for canned food and checking to see if anyone is hiding inside.",
                "image_file": "house.png"
            }
        }
    }
}

# --- 3. SESSION MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_book" not in st.session_state:
    st.session_state.current_book = None

# --- 4. SIDEBAR UI ---
with st.sidebar:
    st.title("📚 Literary Multiverse")
    
    # Select Book First
    selected_book = st.selectbox("Select a Novel/Play:", list(BOOKS.keys()))
    book_data = BOOKS[selected_book]
    
    # Reset everything if the user changes the book
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

    st.markdown("---")
    
    # Dynamic Character Dropdown & Image
    selected_name = st.selectbox("Select Character:", list(book_data["characters"].keys()))
    char_image_path = book_data["characters"][selected_name].get("image_file", "")
    if char_image_path and os.path.exists(char_image_path):
        st.image(char_image_path, use_column_width=True)
        
    # Dynamic Location Dropdown & Image
    selected_location = st.selectbox("Select Location:", list(book_data["locations"].keys()))
    loc_image_path = book_data["locations"][selected_location].get("image_file", "")
    if loc_image_path and os.path.exists(loc_image_path):
        st.image(loc_image_path, use_column_width=True, caption=f"Current Location: {selected_location}")
        
    st.markdown("---")
    if st.button("Start New Conversation"):
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

# --- 5. AI INITIALIZATION & PROMPT ---
st.title(f"🗣️ Conversation with {selected_name}")
st.caption(f"📍 Current Location: {selected_location} | 📖 Text: {selected_book}")

dynamic_prompt = f"""
You are {selected_name} from the literary work '{selected_book}'. 
{book_data['characters'][selected_name]['prompt_addition']}

CRITICAL CONTEXT:
You are currently located in: {selected_location}. 
Location rules: {book_data['locations'][selected_location]['rules']}

CRITICAL INSTRUCTIONS:
1. ONLY use information, events, and world-building found explicitly in the text of '{selected_book}'. Do not invent backstory.
2. React appropriately to your location and its atmosphere.
3. Keep your responses conversational, adopting the exact tone and dialect of your character.
4. Do not acknowledge you are an AI or a character in a book.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=dynamic_prompt,
    generation_config=genai.types.GenerationConfig(temperature=0.3)
)

# Reset session if character or location changes
if "current_char" not in st.session_state or st.session_state.current_char != selected_name or "current_loc" not in st.session_state or st.session_state.current_loc != selected_location:
    st.session_state.chat_history = []
    st.session_state.current_char = selected_name
    st.session_state.current_loc = selected_location
    st.session_state.chat_session = model.start_chat(history=[])

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# --- 6. CHAT INTERFACE & LOGIC ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(f"Speak to {selected_name}...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    try:
        response = st.session_state.chat_session.send_message(user_input)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        
    except ResourceExhausted:
        st.error("🚨 **System Overloaded.** Please wait 60 seconds and try again.")
        st.session_state.chat_history.pop()
    except ValueError:
        st.error("🚨 **Content Blocked.** The AI's safety filters blocked this response. Try rephrasing your question.")
        if st.session_state.chat_history:
            st.session_state.chat_history.pop()
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh the page.")
        if st.session_state.chat_history:
             st.session_state.chat_history.pop()
