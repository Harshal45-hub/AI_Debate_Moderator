#!/usr/bin/env python3
"""
FIXED Core Debate Engine - Guaranteed to speak both agents
"""

import asyncio
import aiohttp
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict

from voice_engine import FixedVoiceEngine, VoiceConfig

@dataclass
class AgentConfig:
    """Configuration for debate agent"""
    name: str
    position: str  # "for" or "against"
    personality: str
    voice_gender: str = "male"
    voice_speed: int = 180

class ReliableDebateAgent:
    """Agent that always works"""
    
    def __init__(self, config: AgentConfig, api_key: str = ""):
        self.config = config
        self.api_key = api_key
    
    async def get_response(self, topic: str, opponent: str = "", is_opening: bool = False) -> str:
        """Get response - always works"""
        
        # Try API if key exists
        if self.api_key and self.api_key.startswith("sk-"):
            response = await self._try_api(topic, opponent, is_opening)
            if response:
                return response
        
        # Fallback responses
        return self._get_fallback(is_opening, opponent)
    
    async def _try_api(self, topic: str, opponent: str, is_opening: bool) -> str:
        """Try API call"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
            }
            
            if is_opening:
                prompt = f"Topic: {topic}\nGive opening statement as {self.config.name} arguing {self.config.position}:"
            else:
                prompt = f"Topic: {topic}\nOpponent said: '{opponent}'\nRespond as {self.config.name}:"
            
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": f"You are {self.config.name}. {self.config.personality}"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        text = result['choices'][0]['message']['content'].strip()
                        
                        if text.startswith(f"{self.config.name}:"):
                            text = text.replace(f"{self.config.name}:", "").strip()
                        
                        return text
                        
        except Exception as e:
            print(f"⚠️ API skipped for {self.config.name}: {e}")
        
        return None
    
    def _get_fallback(self, is_opening: bool, opponent: str = "") -> str:
        """Fallback responses"""
        if self.config.position == "for":
            if is_opening:
                responses = [
                    f"As {self.config.name}, I firmly believe this is the right direction. The evidence supports our position completely.",
                    f"I'm {self.config.name}, and I'm here to show why this approach benefits everyone involved.",
                    f"This is {self.config.name}. The data clearly indicates we should move forward with this plan.",
                ]
            else:
                if opponent:
                    responses = [
                        f"That's an interesting point, but as {self.config.name}, I see it differently. The benefits outweigh the concerns.",
                        f"I understand your worry, {self.config.name} here, but consider the long-term advantages.",
                        f"While you make a valid argument, the statistics tell a different story that supports my position.",
                    ]
                else:
                    responses = [
                        f"{self.config.name} here. We need to focus on the proven benefits of this approach.",
                        f"The advantages are clear when we look at the data, says {self.config.name}.",
                    ]
        else:  # against
            if is_opening:
                responses = [
                    f"I'm {self.config.name}, and I have serious concerns about this direction we're taking.",
                    f"This is {self.config.name}. We need to carefully consider the risks involved here.",
                    f"As {self.config.name}, I must warn about the potential negative consequences of this approach.",
                ]
            else:
                if opponent:
                    responses = [
                        f"That position overlooks critical issues, says {self.config.name}. We need more consideration.",
                        f"As {self.config.name}, I see significant flaws in that argument that need addressing.",
                        f"We're not looking at all the potential negative outcomes here, warns {self.config.name}.",
                    ]
                else:
                    responses = [
                        f"{self.config.name} speaking. There are better alternatives we should discuss.",
                        f"The evidence against this approach is quite compelling, notes {self.config.name}.",
                    ]
        
        return random.choice(responses)

class WorkingDebateSystem:
    """DEBATE SYSTEM THAT WORKS - Both agents WILL speak"""
    
    def __init__(self, topic: str, agent1: ReliableDebateAgent, agent2: ReliableDebateAgent):
        self.topic = topic
        self.agent1 = agent1
        self.agent2 = agent2
        self.voice_engine = FixedVoiceEngine()
        self.history = []
        
        print("\n" + "="*60)
        print("🤖 WORKING AI VERBAL DEBATE")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"FOR: {agent1.config.name} ({agent1.config.voice_gender} voice)")
        print(f"AGAINST: {agent2.config.name} ({agent2.config.voice_gender} voice)")
        print("="*60)
    
    async def conduct_debate(self):
        """Conduct debate - BOTH AGENTS WILL SPEAK"""
        
        print("\n🎙️ Starting in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            await asyncio.sleep(1)
        
        # TEST BOTH VOICES FIRST
        print("\n🔊 TESTING BOTH VOICES...")
        print("="*50)
        
        # Test Agent 1 voice
        voice1 = VoiceConfig(
            name=self.agent1.config.name,
            voice_gender=self.agent1.config.voice_gender,
            voice_speed=self.agent1.config.voice_speed
        )
        print(f"\nTesting {self.agent1.config.name} voice...")
        self.voice_engine.speak(f"This is {self.agent1.config.name} testing my voice.", voice1)
        await asyncio.sleep(1)
        
        # Test Agent 2 voice
        voice2 = VoiceConfig(
            name=self.agent2.config.name,
            voice_gender=self.agent2.config.voice_gender,
            voice_speed=self.agent2.config.voice_speed
        )
        print(f"\nTesting {self.agent2.config.name} voice...")
        self.voice_engine.speak(f"This is {self.agent2.config.name} testing my voice.", voice2)
        await asyncio.sleep(1)
        
        print("\n✅ Voice test complete! Starting debate...")
        print("="*50)
        
        # OPENING STATEMENTS
        print("\n📣 OPENING STATEMENTS")
        print("="*50)
        
        # Agent 1 opening
        print(f"\n{self.agent1.config.name} preparing statement...")
        opening1 = await self.agent1.get_response(self.topic, is_opening=True)
        self.voice_engine.speak(opening1, voice1)
        self.history.append(f"{self.agent1.config.name}: {opening1}")
        await asyncio.sleep(1)
        
        # Agent 2 opening
        print(f"\n{self.agent2.config.name} preparing statement...")
        opening2 = await self.agent2.get_response(self.topic, opening1, is_opening=True)
        self.voice_engine.speak(opening2, voice2)
        self.history.append(f"{self.agent2.config.name}: {opening2}")
        await asyncio.sleep(1)
        
        # DEBATE ROUNDS - SIMPLE AND RELIABLE
        for round_num in range(1, 5):  # 4 rounds
            print(f"\n🔄 ROUND {round_num}")
            print("="*50)
            
            # Agent 1 responds
            last = opening2 if round_num == 1 else self.history[-1].split(": ", 1)[1]
            print(f"\n{self.agent1.config.name} responding...")
            resp1 = await self.agent1.get_response(self.topic, last)
            self.voice_engine.speak(resp1, voice1)
            self.history.append(f"{self.agent1.config.name}: {resp1}")
            await asyncio.sleep(0.5)
            
            # Agent 2 responds
            print(f"\n{self.agent2.config.name} responding...")
            resp2 = await self.agent2.get_response(self.topic, resp1)
            self.voice_engine.speak(resp2, voice2)
            self.history.append(f"{self.agent2.config.name}: {resp2}")
            await asyncio.sleep(0.5)
        
        # CLOSING STATEMENTS
        print("\n📣 CLOSING STATEMENTS")
        print("="*50)
        
        print(f"\n{self.agent1.config.name} final words...")
        close1 = await self.agent1.get_response(self.topic, "Final summary please.")
        self.voice_engine.speak(close1, voice1)
        await asyncio.sleep(1)
        
        print(f"\n{self.agent2.config.name} final words...")
        close2 = await self.agent2.get_response(self.topic, "Final summary please.")
        self.voice_engine.speak(close2, voice2)
        
        # FINAL
        await asyncio.sleep(1)
        print("\n" + "="*60)
        print("✅ DEBATE COMPLETED SUCCESSFULLY!")
        print(f"Total exchanges: {len(self.history)}")
        print("="*60)
        
        # Save transcript
        self._save_transcript()
    
    def _save_transcript(self):
        """Save transcript"""
        filename = f"debate_{datetime.now().strftime('%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(f"Topic: {self.topic}\n\n")
            for line in self.history:
                f.write(f"{line}\n\n")
        print(f"💾 Transcript: {filename}")

# PRESET AGENTS
def create_working_agents(api_key: str = ""):
    """Create agents that actually work"""
    
    agent1 = ReliableDebateAgent(
        AgentConfig(
            name="Alex",
            position="for",
            personality="Logical, analytical, cites data and statistics",
            voice_gender="male",
            voice_speed=170
        ),
        api_key
    )
    
    agent2 = ReliableDebateAgent(
        AgentConfig(
            name="Jordan",
            position="against",
            personality="Passionate, ethical, focuses on human impact",
            voice_gender="female",
            voice_speed=190
        ),
        api_key
    )
    
    return agent1, agent2