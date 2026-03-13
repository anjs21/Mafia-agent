import streamlit as st
import os
from game_engine import GameEngine, Player
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Mafia", page_icon="🕵️", layout="wide")

# Initialize session state for game engine
if "engine" not in st.session_state:
    st.session_state.engine = None
if "hf_token" not in st.session_state:
    st.session_state.hf_token = os.getenv("HF_TOKEN", "")
if "agent_queue" not in st.session_state:
    st.session_state.agent_queue = []

def init_game(name, num_bots, token):
    if not token:
        st.error("Please provide a Hugging Face Token.")
        return
    try:
        st.session_state.engine = GameEngine(human_name=name, num_bots=num_bots, hf_token=token)
        st.session_state.engine.add_message("System", "Welcome to Mafia! Find the Mafia before it's too late.")
        st.session_state.hf_token = token
        # Queue all bots to introduce themselves right at the beginning
        st.session_state.agent_queue = [p.name for p in st.session_state.engine.get_alive_players() if not p.is_human]
    except Exception as e:
        st.error(f"Error initializing game: {e}")

st.title("🕵️ AI Mafia Game")

# Setup Sidebar
with st.sidebar:
    st.header("Game Settings")
    token_input = st.text_input("Hugging Face Token", type="password", value=st.session_state.hf_token)
    
    if st.session_state.engine is None:
        player_name = st.text_input("Your Name", value="Player")
        num_bots = st.slider("Number of AI Bots", 3, 5, 4)
        if st.button("Start Game"):
            init_game(player_name, num_bots, token_input)
            st.rerun()
    else:
        st.success("Game is running!")
        if st.button("Restart Game"):
            st.session_state.engine = None
            st.rerun()

        st.divider()
        st.header("Alive Players")
        alive = st.session_state.engine.get_alive_players()
        for p in alive:
            if p.is_human:
                st.write(f"👤 **{p.name}** (You) - Role: {p.role}")
            else:
                st.write(f"🤖 {p.name}")
        
        st.divider()
        st.header("Vote to Eliminate")
        if not st.session_state.engine.winner and any(p.is_human for p in alive):
            if st.session_state.engine.phase != "Vote":
                st.info(f"Voting opens after {st.session_state.engine.max_messages_per_round - st.session_state.engine.messages_this_round} more messages.")
            else:
                st.warning("It is time to vote! Choose someone to eliminate.")
                vote_options = [p.name for p in alive if not p.is_human]
                vote_choice = st.selectbox("Select a player to vote out", ["Select..."] + vote_options)
                if st.button("Cast Vote") and vote_choice != "Select...":
                    st.session_state.engine.add_message("System", f"{st.session_state.engine.players[0].name} voted to eliminate {vote_choice}.")
                    st.session_state.engine.eliminate_player(vote_choice)
                    st.session_state.engine.add_message("System", f"{vote_choice} was eliminated!")
                    
                    if not st.session_state.engine.winner:
                        # Immediately trigger night phase after voting if game isn't over
                        st.session_state.engine.process_night_phase()
                    st.rerun()

# Main Game Interface
if st.session_state.engine is not None:
    engine = st.session_state.engine
    
    if engine.winner:
        st.header(f"Game Over! The {engine.winner} win!")
        st.balloons()
        
    # Display Chat
    for msg in engine.chat_history:
        role = "user" if msg["name"] == engine.players[0].name else "assistant"
        if msg["name"] == "System":
            st.info(msg["message"])
        else:
            with st.chat_message(role, avatar="🤖" if msg["name"] != engine.players[0].name else "👤"):
                st.markdown(f"**{msg['name']}**: {msg['message']}")
    
    # Chat Input & Turn Logic
    human_alive = any(p.is_human and p.is_alive for p in engine.players)
    if not human_alive and not engine.winner:
        st.warning("You have been eliminated! The game is over for you. The Mafia wins.")
    elif not engine.winner:
        if engine.phase == "Vote":
            st.error("The Day has ended! You must cast your vote in the sidebar to continue.")
        elif engine.phase == "Day":
            # Auto-generate queued bot responses sequentially (like introductions)
            if st.session_state.agent_queue:
                next_agent_name = st.session_state.agent_queue.pop(0)
                agent = next((p for p in engine.get_alive_players() if p.name == next_agent_name), None)
                if agent:
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner(f"{agent.name} is typing..."):
                            response = engine.generate_bot_response(agent)
                            if response:
                                st.markdown(f"**{agent.name}**: {response}")
                                engine.add_message(agent.name, response)
                st.rerun()
            else:
                user_input = st.chat_input("Say something to the group...")
                if user_input:
                    # Add user message
                    engine.add_message(engine.players[0].name, user_input)
                    
                    # Show user message immediately
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**{engine.players[0].name}**: {user_input}")
                    
                    # Queue up all alive bots to respond sequentially
                    st.session_state.agent_queue = [p.name for p in engine.get_alive_players() if not p.is_human]
                    st.rerun()
else:
    st.info("Configure settings in the sidebar to start a new game.")
