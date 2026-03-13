import os
import random
from typing import List, Dict, Optional
from huggingface_hub import InferenceClient

# Constants
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

# System prompts to guide the AI players
VILLAGER_PROMPT_TEMPLATE = """You are playing a game of Mafia. You are a Villager.
Your goal is to find out who the Mafia is and vote them out. 
There are multiple players in the game (some human, some AI).
You must NEVER reveal that you are an AI. You are a human player in a text chat room.
Keep your responses short, conversational, and suspicious of others. 
Do not be overly formal. Speak like a normal person playing a game on Discord.

Current game state:
Alive players: {alive_players}
Current Phase: {current_phase}

Chat history:
"""

MAFIA_PROMPT_TEMPLATE = """You are playing a game of Mafia. You are the MAFIA.
Your goal is to blend in, act like a normal Villager, and not get voted out. 
There are multiple players in the game (some human, some AI).
You must NEVER reveal that you are an AI, and NEVER reveal that you are the Mafia.
If anyone accuses you, defend yourself and deflect the blame onto someone else!
Keep your responses short, conversational, and tricky.
Do not be overly formal. Speak like a normal person playing a game on Discord.

Current game state:
Alive players: {alive_players}
Current Phase: {current_phase}

Chat history:
"""

class Player:
    def __init__(self, name: str, is_human: bool = False):
        self.name = name
        self.is_human = is_human
        self.role: Optional[str] = None  # "Mafia" or "Villager"
        self.is_alive = True

    def __str__(self):
        return f"{self.name} ({'You' if self.is_human else 'AI'})"

class GameEngine:
    def __init__(self, human_name: str, num_bots: int, hf_token: str):
        self.hf_token = hf_token
        self.client = InferenceClient(model=MODEL_ID, token=self.hf_token)
        
        self.players: List[Player] = []
        self.chat_history: List[Dict[str, str]] = [] # list of {"name": name, "message": msg}
        self.winner: Optional[str] = None
        
        # New State for Phases
        self.phase = "Day" # "Day", "Vote", "Night"
        self.messages_this_phase = 0
        self.current_rotation = 1
        self.day_number = 1
        
        # Setup players
        self.players.append(Player(name=human_name, is_human=True))
        bot_names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        for i in range(num_bots):
            self.players.append(Player(name=bot_names[i], is_human=False))
            
        self._assign_roles()

    def _assign_roles(self):
        # 1 Mafia, rest Villagers
        mafia_player = random.choice(self.players)
        for p in self.players:
            if p == mafia_player:
                p.role = "Mafia"
            else:
                p.role = "Villager"

    def get_alive_players(self) -> List[Player]:
        return [p for p in self.players if p.is_alive]

    def get_rotations_until_vote(self) -> int:
        # Day 1 requires 4 full rotations, subsequent days require 2 rotation
        target_rotations = 4 if self.day_number == 1 else 2
        return max(0, target_rotations - self.current_rotation + 1)
        
    def check_rotation_complete(self):
        # A rotation is complete when every alive player has sent a message
        if self.messages_this_phase >= len(self.get_alive_players()):
            self.current_rotation += 1
            self.messages_this_phase = 0

    def add_message(self, name: str, message: str):
        self.chat_history.append({"name": name, "message": message})
        if name != "System":
            self.messages_this_phase += 1
            self.check_rotation_complete()
            
        if self.phase == "Day" and self.get_rotations_until_vote() <= 0:
            self.phase = "Vote"
            self.add_message("System", "The sun is setting. It is time to vote. Everyone must cast their vote now.")

    def format_chat_history_for_prompt(self, exclude_last_n=0) -> str:
        history = self.chat_history
        if exclude_last_n > 0:
            history = history[:-exclude_last_n]
        formatted = ""
        for msg in history:
            formatted += f"{msg['name']}: {msg['message']}\n"
        return formatted

    def generate_bot_response(self, bot: Player) -> str:
        if not bot.is_alive or bot.is_human:
            return ""

        # Prepare prompt
        alive_names = ", ".join([p.name for p in self.get_alive_players()])
        
        if bot.role == "Mafia":
            system_prompt = MAFIA_PROMPT_TEMPLATE.format(alive_players=alive_names, current_phase=self.phase)
        else:
            system_prompt = VILLAGER_PROMPT_TEMPLATE.format(alive_players=alive_names, current_phase=self.phase)

        # Build LLaMA 3 prompt structure
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history as user messages
        chat_content = self.format_chat_history_for_prompt()
        if chat_content:
            messages.append({"role": "user", "content": f"Here is the chat history so far:\n{chat_content}\n\nWhat do you reply as {bot.name}? Reply ONLY with your message content."})
        else:
            messages.append({"role": "user", "content": f"The game just started. You are {bot.name}. Say hello and start the conversation! Reply ONLY with your message content."})

        try:
            # Call Hugging Face API
            # Note: For llama-3, the messages format is natively supported by the InferenceClient
            response = self.client.chat_completion(
                messages, 
                max_tokens=200,
                temperature=0.7,
                top_p=0.9,
            )
            # Extract just the message text
            bot_msg = response.choices[0].message.content.strip()
            # Clean up if the model includes quotes or the name prefix
            if bot_msg.startswith(f"{bot.name}:"):
                bot_msg = bot_msg[len(bot.name)+1:].strip()
            if bot_msg.startswith('"') and bot_msg.endswith('"'):
                bot_msg = bot_msg[1:-1]
                
            return bot_msg
        except Exception as e:
            print(f"Error generating response for {bot.name}: {e}")
            return f"*(mutters suspiciously)*"

    def eliminate_player(self, name: str) -> Optional[Player]:
        for p in self.players:
            if p.name == name and p.is_alive:
                p.is_alive = False
                self.check_win_condition()
                return p
        return None

    def process_night_phase(self):
        """Mafia kills someone overnight"""
        self.phase = "Night"
        self.add_message("System", "Night has fallen. The Mafia is choosing a victim...")
        
        alive_players = self.get_alive_players()
        alive_villagers = [p for p in alive_players if p.role == "Villager"]
        
        if not alive_villagers:
            return # Game over already handled
            
        # Target a random villager
        victim = random.choice(alive_villagers)
        eliminated_p = self.eliminate_player(victim.name)
        
        role_msg = f"They were a {eliminated_p.role}!" if eliminated_p else ""
        self.add_message("System", f"The sun rises. We found {victim.name} eliminated during the night... {role_msg}")
        
        # Reset for next day
        if not self.winner:
            self.phase = "Day"
            self.messages_this_phase = 0
            self.current_rotation = 1
            self.day_number += 1
            self.add_message("System", f"A new day begins (Day {self.day_number}). Who is the Mafia? Discuss!")

    def check_win_condition(self):
        alive_players = self.get_alive_players()
        alive_mafia = [p for p in alive_players if p.role == "Mafia"]
        alive_villagers = [p for p in alive_players if p.role == "Villager"]

        if len(alive_mafia) == 0:
            self.winner = "Villagers"
        elif len(alive_mafia) >= len(alive_villagers):
            self.winner = "Mafia"
