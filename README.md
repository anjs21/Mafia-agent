# 🕵️ AI Mafia Game

Welcome to **AI Mafia Game**, a text-based adaptation of the classic social deduction game where you play alongside AI agents! 

You must deduce who the Mafia is based on their chat responses before they eliminate everyone in town. Will you find the imposter, or will they successfully blend in?

---

## 🌟 Features
- **100% Offline AI Integration**: The game leverages [Ollama](https://ollama.com/) to run Llama 3.1 entirely on your local machine. No API keys, no internet dependency, and no usage limits!
- **Interactive UI**: A clean, responsive interface powered by [Streamlit](https://streamlit.io/).
- **Dynamic Phases**: The game strictly follows Day (Chatting), Voting, and Night (Mafia Kill) phases.
- **Round-Based Voting**: Every alive AI agent and player takes equal turns chatting so you have enough clues before making a choice.

---

## 🛠️ Prerequisites

Since this game uses large language models locally, you will need to install **Ollama**. Check out the [Ollama website](https://ollama.com/) for detailed setup depending on your OS.

### For Linux/macOS:
You can quickly install Ollama via your terminal:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### For Windows:
Download the installer directly from the [Ollama Download Page](https://ollama.com/download).

---

## 🚀 Installation & Setup

Follow these steps to get your game up and running locally.

### 1. Clone the repository
First, clone this codebase onto your machine and navigate into the folder:
```bash
git clone https://github.com/anjs21/Mafia-agent.git
cd Mafia-agent
```

### 2. Download the AI Model
Since the AI agents are powered by local LLMs, you need to download the `llama3.1` model onto your computer. Make sure the Ollama application is running in the background, then pull the model:
```bash
ollama run llama3.1
```
*(Note: The model is roughly ~4.7GB and only needs to be downloaded once. Once you see a success message and a chat prompt, you can type `/bye` to exit).*

### 3. Install Python Dependencies
It is highly recommended to use a Python virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Next, install the required packages:
```bash
pip install -r requirements.txt
```

### 4. Run the Game!
Start the Streamlit development server:
```bash
streamlit run app.py
```
A browser tab will automatically open *(usually at `http://localhost:8501`)*, and you can start playing!

---

## 📜 How to Play
1. **Configure the Match**: Use the sidebar to set your name and how many AI bots you want to play against. Click **Start Game**.
2. **Day Phase**: Talk to the group! The AI Bots will try their best to simulate real players. If they are the Mafia, they will act defensively to blend in.
3. **Voting Phase**: After everyone has spoken for the round, voting will open in the sidebar. Select your suspect to eliminate them. The chat will reveal their true role!
4. **Night Phase**: If the Mafia survives the vote, they will blindly eliminate a Villager during the night.
5. **Win Conditions**: You win if all Mafia members are discovered and eliminated. The Mafia wins if their numbers equal or exceed the remaining Villagers. Good luck!
