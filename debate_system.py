import asyncio
import threading
import queue
from datetime import datetime
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import aiohttp
import pyttsx3


# ========== CONFIGURATION ==========
API_KEY = os.getenv("OPENROUTER_API_KEY")  # Replace with your key
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ========== DATA CLASSES ==========
@dataclass
class DebateAgentConfig:
    name: str
    position: str  # "for" or "against"
    personality: str
    voice_speed: int = 180
    voice_gender: str = "male"
    temperature: float = 0.8

@dataclass
class DebateRound:
    speaker: str
    text: str
    timestamp: datetime = field(default_factory=datetime.now)

# ========== VOICE ENGINE ==========
class VoiceEngine:
    def __init__(self):
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            self.voices = {
                'male': voices[0].id if len(voices) > 0 else None,
                'female': voices[1].id if len(voices) > 1 else voices[0].id if voices else None
            }
            self.engine.setProperty('rate', 180)
            print(f"✓ Voice engine initialized")
        except Exception as e:
            print(f"✗ Voice engine error: {e}")
            self.engine = None
    
    def speak(self, text: str, agent_config: DebateAgentConfig):
        if not self.engine:
            print(f"\n🎤 [{agent_config.name}]: {text}")
            return
        
        # Set voice properties
        voice_id = self.voices.get(agent_config.voice_gender)
        if voice_id:
            self.engine.setProperty('voice', voice_id)
        
        self.engine.setProperty('rate', agent_config.voice_speed)
        
        # Speak
        print(f"\n🎤 [{agent_config.name}]: {text}")
        print("-" * 50)
        self.engine.say(text)
        self.engine.runAndWait()

# ========== OPENROUTER AGENT ==========
class OpenRouterDebateAgent:
    def __init__(self, config: DebateAgentConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        self.conversation_history = []
        
        # System prompt for OpenRouter
        self.system_prompt = f"""You are {config.name}, debating {config.position} the topic.
Personality: {config.personality}

Rules:
1. Be persuasive and logical
2. Counter opponent's points directly
3. Stay concise (20-40 words)
4. Speak naturally like human debate
5. Never mention being an AI
6. Use persuasive language and rhetorical questions

Respond ONLY with your debate statement."""
    
    async def generate_response(self, topic: str, opponent_statement: str = "") -> str:
        """Generate response using OpenRouter API"""
        
        # Format prompt
        prompt = f"""DEBATE TOPIC: {topic}

OPPONENT'S LAST STATEMENT: "{opponent_statement}"

Previous context: {self._get_recent_history()}

As {self.config.name} arguing {self.config.position}, respond:"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
            "X-Title": "AI Debate System"
        }
        
        payload = {
            "model": "openai/gpt-3.5-turbo",  # You can change this
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": 150
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        reply = result['choices'][0]['message']['content'].strip()
                        
                        # Clean response
                        if reply.startswith(f"{self.config.name}:"):
                            reply = reply.replace(f"{self.config.name}:", "").strip()
                        
                        # Store history
                        self.conversation_history.append({
                            "speaker": self.config.name,
                            "content": reply,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        return reply
                    else:
                        error_text = await response.text()
                        print(f"OpenRouter API error {response.status}: {error_text}")
                        return "Let me reconsider that point for a moment."
                        
        except Exception as e:
            print(f"Network error: {e}")
            return "I need to gather my thoughts on this."
    
    def _get_recent_history(self):
        if not self.conversation_history:
            return "This is the opening statement."
        
        recent = self.conversation_history[-3:]  # Last 3 exchanges
        return "\n".join([f"{item['speaker']}: {item['content']}" for item in recent])

# ========== DEBATE SYSTEM ==========
class VerbalDebateSystem:
    def __init__(self, topic: str, agent1: OpenRouterDebateAgent, agent2: OpenRouterDebateAgent):
        self.topic = topic
        self.agent1 = agent1
        self.agent2 = agent2
        self.voice_engine = VoiceEngine()
        self.debate_history = []
        self.max_rounds = 6
        
        print("\n" + "="*60)
        print(f"🤖 AI VERBAL DEBATE")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"FOR: {agent1.config.name} ({agent1.config.personality})")
        print(f"AGAINST: {agent2.config.name} ({agent2.config.personality})")
        print("="*60 + "\n")
    
    async def conduct_debate(self):
        """Run the verbal debate"""
        
        print("🎙️ Starting debate in 3 seconds...")
        await asyncio.sleep(3)
        
        # Opening statements
        print("\n📣 OPENING STATEMENTS")
        print("="*50)
        
        # Agent 1 opening
        opening1 = await self.agent1.generate_response(self.topic)
        self.voice_engine.speak(opening1, self.agent1.config)
        self.debate_history.append(DebateRound(self.agent1.config.name, opening1))
        
        await asyncio.sleep(1)
        
        # Agent 2 opening
        opening2 = await self.agent2.generate_response(self.topic, opening1)
        self.voice_engine.speak(opening2, self.agent2.config)
        self.debate_history.append(DebateRound(self.agent2.config.name, opening2))
        
        # Debate rounds
        for round_num in range(1, self.max_rounds + 1):
            print(f"\n🔄 ROUND {round_num}")
            print("="*50)
            
            # Agent 1 responds
            last_statement = self.debate_history[-1].text
            response1 = await self.agent1.generate_response(self.topic, last_statement)
            self.voice_engine.speak(response1, self.agent1.config)
            self.debate_history.append(DebateRound(self.agent1.config.name, response1))
            
            await asyncio.sleep(0.5)
            
            # Agent 2 responds
            response2 = await self.agent2.generate_response(self.topic, response1)
            self.voice_engine.speak(response2, self.agent2.config)
            self.debate_history.append(DebateRound(self.agent2.config.name, response2))
            
            # Pause between rounds
            if round_num < self.max_rounds:
                await asyncio.sleep(1)
        
        # Closing statements
        print("\n📣 CLOSING STATEMENTS")
        print("="*50)
        
        closing1 = await self.agent1.generate_response(
            self.topic, 
            "Give your final summary statement."
        )
        self.voice_engine.speak(closing1, self.agent1.config)
        
        await asyncio.sleep(1)
        
        closing2 = await self.agent2.generate_response(
            self.topic, 
            "Give your final summary statement."
        )
        self.voice_engine.speak(closing2, self.agent2.config)
        
        print("\n" + "="*60)
        print("🏁 DEBATE CONCLUDED")
        print("="*60)
        
        self.save_transcript()
    
    def save_transcript(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debate_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"DEBATE TRANSCRIPT\n")
            f.write(f"Topic: {self.topic}\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write("="*60 + "\n\n")
            
            for i, turn in enumerate(self.debate_history, 1):
                f.write(f"Turn {i}: {turn.speaker}\n")
                f.write(f"{turn.text}\n")
                f.write("-"*40 + "\n")
        
        print(f"💾 Transcript saved to: {filename}")

# ========== PRESET AGENTS ==========
def create_debate_agents(api_key: str):
    """Create two debate agents"""
    
    # Agent FOR the topic
    agent_for = OpenRouterDebateAgent(
        config=DebateAgentConfig(
            name="Alex",
            position="for",
            personality="Logical, data-driven, cites statistics, calm and rational",
            voice_speed=170,
            voice_gender="male",
            temperature=0.7
        ),
        api_key=api_key
    )
    
    # Agent AGAINST the topic
    agent_against = OpenRouterDebateAgent(
        config=DebateAgentConfig(
            name="Jordan",
            position="against",
            personality="Passionate, focuses on ethics and human impact, persuasive",
            voice_speed=190,
            voice_gender="female",
            temperature=0.8
        ),
        api_key=api_key
    )
    
    return agent_for, agent_against

# ========== MAIN RUNNER ==========
async def main():
    """Main function to run the debate"""
    
    # Get API key from environment or direct input
    api_key = API_KEY
    if api_key.startswith("your-"):
        api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Select topic
    topics = [
        "AI will create more jobs than it destroys",
        "Remote work is more productive than office work",
        "Social media has improved human connection",
        "College should be free for everyone",
        "AI should be regulated by governments"
    ]
    
    print("\n📝 Select a debate topic:")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic}")
    print("6. Custom topic")
    
    try:
        choice = int(input("\nEnter choice (1-6): "))
        if choice == 6:
            topic = input("Enter your topic: ")
        else:
            topic = topics[choice - 1]
    except:
        topic = topics[0]
    
    # Create agents
    print("\n🎭 Creating debate agents...")
    agent_for, agent_against = create_debate_agents(api_key)
    
    print(f"\n⚙️  Debate Setup:")
    print(f"   Topic: {topic}")
    print(f"   For: {agent_for.config.name}")
    print(f"   Against: {agent_against.config.name}")
    
    input("\n🎧 Press Enter to start (ensure speakers are on!)...")
    
    # Run debate
    debate = VerbalDebateSystem(topic, agent_for, agent_against)
    
    try:
        await debate.conduct_debate()
    except KeyboardInterrupt:
        print("\n\n⚠️ Debate interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n✨ Done!")

if __name__ == "__main__":
    asyncio.run(main())