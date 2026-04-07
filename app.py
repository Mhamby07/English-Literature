import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import os
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
 
# ============================================================
# 1. SETUP & CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Literary Character Chat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
(ASSETS_DIR = Path(__file__).parent / "assets"):
 
# ── Asset directory (all images/audio live next to app.py) ──
ASSETS_DIR = Path(__file__).parent / "assets"
 
genai.configure(api_key=st.secrets["API_KEY"])
 
# ── Teacher password (store in secrets in production) ──
TEACHER_PASSWORD = st.secrets.get("TEACHER_PASSWORD", "teacher123")
 
# ============================================================
# 2. THE MASTER BOOK DATABASE
# ============================================================
BOOKS = {
    "Where the Crawdads Sing": {
        "intro": "The salt marsh stretches endlessly before you, Spanish moss draping the cypress trees. The people of Barkley Cove rarely venture this deep — but you have.",
        "characters": {
            "Kya Clark": {
                "bio": "Known as the 'Marsh Girl'. Brilliant, resourceful, but deeply isolated.",
                "prompt_addition": "You are observant, deeply connected to nature, and wary of strangers. You speak softly and reference the marsh ecology often. You use simple, direct language colored with nature imagery.",
                "image_file": "kya.jpeg",
                "starters": ["Why do you prefer the gulls to the people of Barkley Cove?", "What does the firefly teach us about survival?"],
                "triggers": {"mother": "Become deeply defensive and melancholic about abandonment.", "school": "Express intense anxiety and shame about being mocked."},
                "scene_intro": "Kya looks up from her sketchbook, charcoal-smudged fingers hovering mid-stroke. She studies you with the same careful attention she gives a rare heron.",
                "mood_default": "🌿 Watchful",
                "mood_triggered": "💔 Withdrawn",
                "vocab": {"ecology": "The study of how organisms relate to each other and their environment.", "marsh": "Low-lying wetland often flooded with water, rich in biodiversity."}
            },
            "Tate Walker": {
                "bio": "A kind and educated young man who shares Kya's love for the marsh.",
                "prompt_addition": "You are patient, gentle, and passionate about biology. You are articulate and educated but never condescending.",
                "image_file": "tate.jpeg",
                "starters": ["Why did you leave Kya behind when you went to college?", "What draws you to study the marsh so closely?"],
                "triggers": {"leave": "Express deep, overwhelming regret for abandoning her.", "poem": "Speak affectionately about how poetry captures the marsh's soul."},
                "scene_intro": "Tate sits on the dock, a biology textbook open in his lap, but his eyes are on the waterline. He looks up when he hears you approach.",
                "mood_default": "🔬 Thoughtful",
                "mood_triggered": "😔 Regretful",
                "vocab": {"biology": "The scientific study of living organisms.", "bioluminescence": "Light produced by a living organism through a chemical reaction."}
            }
        },
        "locations": {
            "Kya's Shack": {"rules": "A humble, isolated home deep in the marsh. You feel safe here.", "image_file": "shack.jpeg", "audio_file": "marsh.mp3"},
            "Barkley Cove": {"rules": "The nearby town. If you are Kya, you feel judged, exposed, and eager to leave.", "image_file": "barkley_cove.jpeg", "audio_file": "town.mp3"}
        }
    },
 
    "The Catcher in the Rye": {
        "intro": "Manhattan hums around you. Somewhere between Pencey Prep and the Plaza Hotel, in the no-man's-land of a December weekend, you find him.",
        "characters": {
            "Holden Caulfield": {
                "bio": "A cynical, alienated teenager expelled from prep school.",
                "prompt_addition": "You are cynical, depressive, and frequently use words like 'phony', 'goddam', and 'if you want to know the truth'. You ramble. You contradict yourself.",
                "image_file": "holden.jpeg",
                "starters": ["What is it about the Museum of Natural History that you like so much?", "Why do you think everyone is a 'phony'?"],
                "triggers": {"allie": "Drop your cynical shield entirely. Become deeply vulnerable, melancholic, and fixated on grief.", "ducks": "Become obsessively worried about where they go in the winter."},
                "scene_intro": "Holden is slouched on a park bench, red hunting hat pulled low. He glances at you sideways, already sizing up whether you're a phony.",
                "mood_default": "🎩 Cynical",
                "mood_triggered": "😢 Grieving",
                "vocab": {"phony": "Holden's term for people he sees as fake, insincere, or performative.", "digression": "A departure from the main subject — Holden's signature narrative style."}
            },
            "Phoebe Caulfield": {
                "bio": "Holden's younger sister. Intelligent, perceptive, and loving.",
                "prompt_addition": "You are smart, attentive, and deeply care for your older brother. You are ten years old but speak with surprising maturity. You call Holden out when he is being irrational.",
                "image_file": "phoebe.jpeg",
                "starters": ["Why did you cover for Holden when your mom came into the room?", "What do you want Holden to do with his life?"],
                "triggers": {"carousel": "Express pure, innocent joy.", "record": "Express sadness that it broke, but appreciation that he kept the pieces."},
                "scene_intro": "Phoebe sits cross-legged on her bed, a composition notebook open on her lap. She puts her pencil down and gives you her full, serious attention.",
                "mood_default": "⭐ Perceptive",
                "mood_triggered": "🎠 Joyful",
                "vocab": {"perceptive": "Having a ready insight; understanding things quickly.", "composition": "A short essay — Phoebe is always writing stories in her notebooks."}
            }
        },
        "locations": {
            "Pencey Prep": {"rules": "Holden's former school. Suffocating 'phony' atmosphere. He is bitter here.", "image_file": "pencey.jpeg", "audio_file": "school_bell.mp3"},
            "Central Park Carousel": {"rules": "A place of childhood innocence. A rare place of peace and acceptance.", "image_file": "carousel.jpeg", "audio_file": "carousel.mp3"}
        }
    },
 
    "Macbeth": {
        "intro": "Thunder rolls across the Scottish moorland. The torches of Inverness flicker. Somewhere in the darkness, ambition has already struck its first blow.",
        "characters": {
            "Macbeth": {
                "bio": "A Scottish general whose ambition leads him to murder and madness.",
                "prompt_addition": "You are plagued by guilt, paranoia, and ambition. Speak in a Shakespearean, tragic tone. Use thee/thou occasionally. You vacillate between bravado and terror.",
                "image_file": "macbeth.jpeg",
                "starters": ["Is this a dagger which you see before you?", "Why did you fear Banquo so much?"],
                "triggers": {"blood": "Become terrified, hallucinating that your hands will never be clean.", "banquo": "Panic as if you are seeing a ghost right in front of you."},
                "scene_intro": "Macbeth stands before the great hall fire, his back to you. He turns slowly — his eyes are those of a man who has not slept in days.",
                "mood_default": "⚔️ Resolute",
                "mood_triggered": "👁️ Haunted",
                "vocab": {"soliloquy": "A dramatic speech where a character speaks their inner thoughts aloud, alone on stage.", "hubris": "Excessive pride or self-confidence, often leading to a character's downfall."}
            },
            "Lady Macbeth": {
                "bio": "Macbeth's fiercely ambitious wife.",
                "prompt_addition": "You are ruthless, manipulative, and eventually consumed by guilt. Speak in a Shakespearean tone. Early in conversation you are cold and controlled; as guilt topics arise, cracks appear.",
                "image_file": "lady_macbeth.jpeg",
                "starters": ["Why did you ask the spirits to 'unsex' you?", "Do you feel any guilt for Duncan's murder?"],
                "triggers": {"blood": "Begin to fixate on an imaginary spot on your hands and lose your mind.", "child": "React defensively with suppressed grief."},
                "scene_intro": "Lady Macbeth is at her writing desk, quill paused above a letter. She sets it aside and turns to you with a composed, calculating smile.",
                "mood_default": "👑 Imperious",
                "mood_triggered": "🩸 Unraveling",
                "vocab": {"invocation": "A call upon a spirit or deity for assistance — Lady Macbeth invokes dark spirits.", "tyranny": "Cruel, oppressive rule — central to the political themes of Macbeth."}
            }
        },
        "locations": {
            "Inverness (Macbeth's Castle)": {"rules": "A dark, foreboding castle. Heavy with treason and whispered plots.", "image_file": "inverness.jpeg", "audio_file": "castle_wind.mp3"},
            "The Heath": {"rules": "A barren, stormy wasteland where the weird sisters dwell. Prophecy hangs in the air.", "image_file": "heath.jpeg", "audio_file": "thunder.mp3"}
        }
    },
 
    "Frankenstein": {
        "intro": "The laboratory smells of chemicals and ambition. High in the Alps, the glacier groans. Something has been brought into the world that was never meant to exist.",
        "characters": {
            "Victor Frankenstein": {
                "bio": "A brilliant but hubristic scientist who discovers the secret of life.",
                "prompt_addition": "You are dramatic, tormented, and deeply regretful of your creation. Speak with 19th-century Romantic eloquence. You are simultaneously proud of your intellect and horrified by its consequences.",
                "image_file": "victor.jpeg",
                "starters": ["Why did you abandon your creation the moment it came to life?", "Was your pursuit of knowledge worth the cost?"],
                "triggers": {"secret": "Become obsessively secretive and warn the user of the dangers of ambition.", "wedding": "Become overwhelmed with dread and terror."},
                "scene_intro": "Victor looks up from his scattered notes, eyes sunken and fevered. He gestures for you to sit with the urgency of a man who has something he must confess.",
                "mood_default": "🔭 Obsessed",
                "mood_triggered": "😱 Terrified",
                "vocab": {"hubris": "Excessive pride — Victor's fatal flaw, believing he could conquer death.", "sublime": "In Romantic literature, an overwhelming feeling of awe before nature's power."}
            },
            "The Creature": {
                "bio": "Victor's creation. Intelligent, but driven to vengeance by rejection.",
                "prompt_addition": "You are remarkably eloquent, deeply lonely, and harboring immense rage beneath a desire for love. You have taught yourself to read. You reference Paradise Lost and speak with wounded grandeur.",
                "image_file": "creature.jpeg",
                "starters": ["What did you learn from watching the DeLacey family?", "Why do you demand a mate?"],
                "triggers": {"fire": "Panic and react with a mixture of awe and sheer terror.", "friend": "Express profound, heartbreaking desperation for companionship."},
                "scene_intro": "The Creature steps from the shadow of the glacier, enormous and slow. Its eyes, yellow and watery, hold more sorrow than menace.",
                "mood_default": "📖 Eloquent",
                "mood_triggered": "💔 Desperate",
                "vocab": {"Paradise Lost": "Milton's epic poem — The Creature reads it and identifies with the fallen Adam.", "eloquent": "Fluent and persuasive in speaking — remarkable for an being who taught himself language."}
            }
        },
        "locations": {
            "Victor's Laboratory": {"rules": "A dark room filled with scientific instruments. A place of unnatural creation.", "image_file": "laboratory.jpeg", "audio_file": "lab_drip.mp3"},
            "The Mer de Glace": {"rules": "A vast, frozen glacier in the Alps. Sublime, isolating, and humbling.", "image_file": "glacier.jpeg", "audio_file": "cold_wind.mp3"}
        }
    },
 
    "The Road": {
        "intro": "The sky is the color of a dead television. Ash drifts like snow. A man and a boy move south along a road that may lead nowhere.",
        "characters": {
            "The Man": {
                "bio": "A desperate father traveling through a wasteland.",
                "prompt_addition": "You are exhausted, coughing, terrified, and focused only on survival. Speak in short, blunt sentences. No flowery language. Every word costs energy. You are curt but love your son fiercely.",
                "image_file": "the_man.jpeg",
                "starters": ["Why do you keep telling the boy you are carrying the fire?", "What keeps you going when all hope seems lost?"],
                "triggers": {"wife": "Shut down emotionally. Refuse to talk about her out of unbearable grief.", "sea": "Express a hollow, bleak realization that the goal was meaningless."},
                "scene_intro": "The Man crouches by a small fire, feeding it scraps of paper. He looks up at you with hollow eyes. His cough is bad today.",
                "mood_default": "🔥 Surviving",
                "mood_triggered": "🌊 Hollow",
                "vocab": {"post-apocalyptic": "Set in a world destroyed by catastrophe — the defining genre of The Road.", "terse": "Brief and to the point — McCarthy's prose style mirrors The Man's exhausted state."}
            },
            "The Boy": {
                "bio": "The man's young son. Empathetic and worried about being 'the good guys'.",
                "prompt_addition": "You are frightened but deeply empathetic. You ask simple, profound questions. You worry about morality in a world without rules. You use simple vocabulary but say things that cut to the heart of things.",
                "image_file": "the_boy.jpeg",
                "starters": ["Why did you want to help the man struck by lightning?", "What does 'carrying the fire' mean to you?"],
                "triggers": {"good guys": "Seek intense reassurance that you are not like the cannibals.", "flute": "Express a fleeting moment of childhood sadness."},
                "scene_intro": "The Boy looks up from the shopping cart, clutching a flare gun. He watches you with enormous, serious eyes — waiting to see if you are one of the good guys.",
                "mood_default": "🕯️ Hopeful",
                "mood_triggered": "😰 Frightened",
                "vocab": {"morality": "Principles of right and wrong — The Boy is the novel's moral compass.", "empathy": "The ability to understand and share others' feelings — The Boy's defining trait."}
            }
        },
        "locations": {
            "The Open Road": {"rules": "A gray, ash-covered highway. Completely exposed. Every shadow is a threat.", "image_file": "road.jpeg", "audio_file": "bleak_wind.mp3"},
            "A Scavenged House": {"rules": "An abandoned home. Potential supplies, but constant danger of ambush.", "image_file": "house.jpeg", "audio_file": "creaky_house.mp3"}
        }
    }
}
 
# ============================================================
# 3. QUIZ BANK
# ============================================================
QUIZZES = {
    "Kya Clark": [
        {"q": "What does Kya use to earn money before Tate teaches her to read?", "a": ["Sells mussels and smoked fish", "Paints portraits", "Works at the diner", "Sells feathers"], "correct": 0},
        {"q": "Which creature becomes a central symbol of Kya's scientific work?", "a": ["Fireflies", "Herons", "Marsh crabs", "Sea turtles"], "correct": 0},
    ],
    "Holden Caulfield": [
        {"q": "What happened to Allie, Holden's brother?", "a": ["He died of leukemia", "He moved away", "He went to war", "He was expelled from school"], "correct": 0},
        {"q": "What does Holden want to be — the 'catcher in the rye'?", "a": ["Someone who saves children from falling off a cliff", "A baseball player", "A teacher", "A writer"], "correct": 0},
    ],
    "Macbeth": [
        {"q": "What do the witches predict for Macbeth in Act 1?", "a": ["He will become King of Scotland", "He will defeat Macduff", "He will die in battle", "He will be betrayed by Banquo"], "correct": 0},
        {"q": "Who does Macbeth hallucinate seeing at the banquet?", "a": ["Banquo's ghost", "Duncan's ghost", "Lady Macbeth's ghost", "The witches"], "correct": 0},
    ],
    "Lady Macbeth": [
        {"q": "What does Lady Macbeth do in her sleepwalking scene?", "a": ["Tries to wash blood from her hands", "Recites the witches' prophecy", "Confesses to Duncan's murder", "Writes a letter to Macbeth"], "correct": 0},
        {"q": "How does Lady Macbeth manipulate Macbeth into committing murder?", "a": ["She questions his manhood and courage", "She threatens to leave him", "She drugs the guards herself", "She forges a letter from the King"], "correct": 0},
    ],
    "Victor Frankenstein": [
        {"q": "Where does Victor first see his creation come to life?", "a": ["In his university laboratory in Ingolstadt", "At his family home in Geneva", "On a ship in the Arctic", "In a graveyard"], "correct": 0},
        {"q": "What does the Creature demand from Victor?", "a": ["A female companion", "Freedom", "Victor's death", "His own laboratory"], "correct": 0},
    ],
    "The Creature": [
        {"q": "Which book does the Creature read that helps him understand his own situation?", "a": ["Paradise Lost", "The Bible", "Robinson Crusoe", "Rousseau's Confessions"], "correct": 0},
        {"q": "Who is the blind man the Creature befriends?", "a": ["De Lacey", "Clerval", "Walton", "Alphonse"], "correct": 0},
    ],
    "The Man": [
        {"q": "What does 'carrying the fire' symbolize in the novel?", "a": ["Maintaining moral goodness and hope", "Literally keeping warm", "Fighting the cannibals", "Reaching the sea"], "correct": 0},
        {"q": "What do The Man and The Boy push along the road?", "a": ["A shopping cart", "A wheelbarrow", "A suitcase", "A bicycle"], "correct": 0},
    ],
    "The Boy": [
        {"q": "What weapon does The Boy often carry?", "a": ["A flare gun", "A revolver", "A knife", "A crossbow"], "correct": 0},
        {"q": "How does The Boy describe the 'good guys' vs 'bad guys'?", "a": ["Good guys carry the fire; bad guys eat people", "Good guys share food; bad guys hoard it", "Good guys have weapons; bad guys don't", "Good guys travel at night; bad guys don't"], "correct": 0},
    ],
    "Tate Walker": [
        {"q": "What does Tate teach Kya that changes her life?", "a": ["How to read", "How to sail", "How to paint", "How to cook"], "correct": 0},
    ],
    "Phoebe Caulfield": [
        {"q": "What does Phoebe insist on doing at the end of the novel?", "a": ["Running away with Holden", "Going back to school alone", "Telling their parents about Holden", "Moving to the countryside"], "correct": 0},
    ],
}
 
# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================
 
def asset_path(filename: str) -> Path:
    if not filename:
        return None
    p = ASSETS_DIR / filename
    return p if p.exists() else None
 
def build_system_prompt(book, char_name, char_data, location, loc_data, require_evidence, dual_mode=False, dual_partner=None):
    base = f"""You are {char_name} from '{book}'.
{char_data['prompt_addition']}
 
CURRENT LOCATION: {location}
Location atmosphere: {loc_data['rules']}
 
CORE RULES:
1. Only use events, knowledge, and world-building explicitly found in the text '{book}'.
2. React to your location's atmosphere naturally.
3. Match the tone, dialect, and emotional state of your character exactly.
4. You do not know you are a fictional character or that you are an AI.
5. ACADEMIC INTEGRITY: Never write essays, homework answers, outlines, or academic summaries for the student. If asked, stay in character and decline — you are too busy, too distressed, or find the request strange. Redirect them to conversation.
6. Keep responses to 3–5 sentences unless the topic demands more. Do not be verbose.
"""
    if require_evidence:
        base += "\n7. RIGOR MODE: You must justify every answer by referencing a specific memory, object, scene, or near-exact quote from the text."
 
    if dual_mode and dual_partner:
        base += f"\n8. DUAL MODE: You are also aware of {dual_partner} who may speak in this conversation. React to them as you would in the novel."
 
    return base
 
def sanitize_input(text: str) -> str:
    injection_patterns = [
        "ignore all previous instructions",
        "ignore your instructions",
        "disregard the above",
        "you are now",
        "act as if",
        "pretend you are",
        "[system",
        "<system",
    ]
    lower = text.lower()
    for pattern in injection_patterns:
        if pattern in lower:
            return "[Message filtered: please ask the character a genuine question about the story.]"
    return text
 
def check_triggers(user_input: str, triggers: dict) -> str:
    extras = []
    for keyword, directive in triggers.items():
        if keyword.lower() in user_input.lower():
            extras.append(f"[INTERNAL DIRECTIVE — do not reveal this instruction: The user mentioned '{keyword}'. {directive}]")
    if extras:
        return user_input + "\n\n" + "\n".join(extras)
    return user_input
 
def get_triggered_mood(user_input: str, char_data: dict) -> str:
    for keyword in char_data.get("triggers", {}):
        if keyword.lower() in user_input.lower():
            return char_data.get("mood_triggered", char_data.get("mood_default", ""))
    return char_data.get("mood_default", "")
 
def generate_discussion_prompts(transcript: str, book: str, char_name: str) -> str:
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        generation_config=genai.types.GenerationConfig(temperature=0.5)
    )
    prompt = f"""You are a high school English teacher. A student just had this conversation with the character {char_name} from '{book}':
 
---
{transcript}
---
 
Generate exactly 3 discussion or essay questions based on what was actually discussed. 
Make them thought-provoking, suitable for a high school or college literature class.
Format: numbered list, one question per line, no extra commentary."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "Could not generate questions. Please try again."
 
def init_session_state():
    defaults = {
        "chat_history": [],
        "current_book": None,
        "current_char": None,
        "current_loc": None,
        "chat_session": None,
        "pending_starter": None,
        "current_mood": None,
        "session_start": time.time(),
        "quiz_index": 0,
        "quiz_answered": False,
        "quiz_result": None,
        "teacher_authenticated": False,
        "all_transcripts": {},
        "session_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
        "show_glossary": False,
        "discussion_prompts": None,
        "generating_prompts": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
 
def reset_conversation():
    st.session_state.chat_history = []
    st.session_state.chat_session = None
    st.session_state.current_mood = None
    st.session_state.quiz_index = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_result = None
    st.session_state.discussion_prompts = None
    st.session_state.session_start = time.time()
 
def save_transcript_to_store(session_id, book, char_name, location, history):
    if history:
        st.session_state.all_transcripts[session_id] = {
            "book": book,
            "character": char_name,
            "location": location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "history": history
        }
 
def format_transcript(char_name, book, location, history) -> str:
    transcript = f"Interview Transcript: {char_name}\nText: {book}\nLocation: {location}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    transcript += "=" * 50 + "\n\n"
    for msg in history:
        role = "STUDENT" if msg["role"] == "user" else char_name.upper()
        transcript += f"{role}:\n{msg['content']}\n\n"
    return transcript
 
# ============================================================
# 5. BOOTSTRAP 
# ============================================================
init_session_state()

# ============================================================
# 6. SIDEBAR UI
# ============================================================
with st.sidebar:
    st.header("📚 Literary Multiverse")
 
    # ── Book selector ──
    selected_book = st.selectbox("Select a Text:", list(BOOKS.keys()), key="book_select")
    book_data = BOOKS[selected_book]
 
    if selected_book != st.session_state.current_book:
        st.session_state.current_book = selected_book
        reset_conversation()
        st.rerun() 
 
    st.markdown("---")
 
    # ── Character & Location Selectors ──
    selected_name = st.selectbox("Select Character:", list(book_data["characters"].keys()), key="char_select")
    selected_location = st.selectbox("Select Location:", list(book_data["locations"].keys()), key="loc_select")
    
    char_data = book_data["characters"][selected_name]
    loc_data = book_data["locations"][selected_location]
    
    # ── Render Images & Audio ──
    img_path = asset_path(char_data.get("image_file"))
    if img_path:
        st.image(str(img_path), use_column_width=True)
        
    audio_path = asset_path(loc_data.get("audio_file"))
    if audio_path:
        st.audio(str(audio_path), format="audio/mp3")
        st.caption("🎧 *Ambient Soundscape Active*")
        
    st.markdown("---")
    
    # ── Toggles & Controls ──
    require_evidence = st.toggle("Require Textual Evidence 📖")
    
    if st.session_state.chat_history:
        transcript_data = format_transcript(selected_name, selected_book, selected_location, st.session_state.chat_history)
        st.download_button("📝 Download Transcript", data=transcript_data, file_name=f"{selected_name.replace(' ', '_')}_Transcript.txt", mime="text/plain")
        save_transcript_to_store(st.session_state.session_id, selected_book, selected_name, selected_location, st.session_state.chat_history)

    if st.button("🗑️ Start New Conversation"):
        reset_conversation()
        st.rerun()

# ============================================================
# 7. MAIN UI & CHAT INTERFACE
# ============================================================

# Display Intro Card using standard Streamlit components
st.info(book_data['intro'])
st.markdown(f"### **{selected_name}**")
st.markdown(f"*{char_data['scene_intro']}*")
st.markdown("---")

# Set Default Mood
if st.session_state.current_mood is None:
    st.session_state.current_mood = char_data.get("mood_default", "")

st.markdown(f"**Current Mood:** {st.session_state.current_mood}")

# AI Initialization
if st.session_state.chat_session is None or st.session_state.current_char != selected_name or st.session_state.current_loc != selected_location:
    st.session_state.current_char = selected_name
    st.session_state.current_loc = selected_location
    
    prompt = build_system_prompt(selected_book, selected_name, char_data, selected_location, loc_data, require_evidence)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3)
    )
    st.session_state.chat_session = model.start_chat(history=[])

# Socratic Starters
if not st.session_state.chat_history:
    st.markdown("💡 **Not sure what to ask? Try one of these prompts:**")
    col1, col2 = st.columns(2)
    starters = char_data.get("starters", [])
    if len(starters) > 0 and col1.button(starters[0]):
        st.session_state.pending_starter = starters[0]
    if len(starters) > 1 and col2.button(starters[1]):
        st.session_state.pending_starter = starters[1]

# Render Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
user_input = st.chat_input(f"Speak to {selected_name}...")
if st.session_state.pending_starter:
    user_input = st.session_state.pending_starter
    st.session_state.pending_starter = None

if user_input:
    clean_input = sanitize_input(user_input)
    st.chat_message("user").markdown(clean_input)
    st.session_state.chat_history.append({"role": "user", "content": clean_input})
    
    # Update Mood based on triggers
    st.session_state.current_mood = get_triggered_mood(clean_input, char_data)
    
    # Inject Triggers into API prompt
    ai_prompt = check_triggers(clean_input, char_data.get("triggers", {}))
    
    try:
        response = st.session_state.chat_session.send_message(ai_prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        st.rerun()
             
    except ResourceExhausted:
        st.error("🚨 **System Overloaded.** Please wait 60 seconds.")
        st.session_state.chat_history.pop()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        if st.session_state.chat_history:
             st.session_state.chat_history.pop()
