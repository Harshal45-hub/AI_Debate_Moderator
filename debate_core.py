#!/usr/bin/env python3
"""
UPDATED Core Debate Engine - Token aware responses
"""

import asyncio
import aiohttp
import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict
import tiktoken  # For token counting

from voice_engine import FixedVoiceEngine, VoiceConfig

@dataclass
class AgentConfig:
    """Configuration for debate agent"""
    name: str
    position: str  # "for" or "against"
    personality: str
    voice_gender: str = "male"
    voice_speed: int = 180
    max_tokens: int = 200  # Maximum tokens per response

class TokenAwareDebateAgent:
    """Agent that's aware of token limits"""
    
    def __init__(self, config: AgentConfig, api_key: str = ""):
        self.config = config
        self.api_key = api_key
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4 tokenizer
        self.conversation_history: List[Dict] = []
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def _truncate_history(self, max_tokens: int = 300):
        """Truncate conversation history to fit token limit"""
        total_tokens = 0
        truncated_history = []
        
        # Add history in reverse (most recent first)
        for msg in reversed(self.conversation_history):
            msg_tokens = self.count_tokens(f"{msg['speaker']}: {msg['content']}")
            if total_tokens + msg_tokens <= max_tokens:
                truncated_history.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        self.conversation_history = truncated_history
    
    async def get_response(self, topic: str, opponent: str = "", is_opening: bool = False) -> str:
        """Get response with token awareness"""
        
        # If no API key, use fallback
        if not self.api_key or not self.api_key.startswith("sk-"):
            return self._get_fallback_response(is_opening, opponent)
        
        # Try API with token-aware prompt
        response = await self._get_api_response(topic, opponent, is_opening)
        if response:
            return response
        
        # Fallback if API fails
        return self._get_fallback_response(is_opening, opponent)
    
    async def _get_api_response(self, topic: str, opponent: str, is_opening: bool) -> str:
        """Get response from API with token constraints"""
        try:
            # Build prompt with token awareness
            prompt = self._build_token_aware_prompt(topic, opponent, is_opening)
            
            # Calculate available tokens for response
            prompt_tokens = self.count_tokens(prompt)
            max_response_tokens = self.config.max_tokens
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
            }
            
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system", 
                        "content": f"""You are {self.config.name}, arguing {self.config.position} the topic.
Personality: {self.config.personality}

TOKEN CONSTRAINTS:
- Maximum response length: {max_response_tokens} tokens (approx {max_response_tokens//4} words)
- Your response MUST be complete within this limit
- DO NOT start sentences you can't finish
- Keep responses concise and self-contained
- If a point is complex, break it into smaller statements

FORMAT REQUIREMENTS:
- Complete your thoughts
- End with proper punctuation
- No trailing incomplete sentences
- Response must be grammatically complete"""
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_response_tokens,
                "stop": [".", "!", "?"]  # Stop at sentence boundaries
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=15
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        text = result['choices'][0]['message']['content'].strip()
                        
                        # Ensure response is complete
                        text = self._ensure_complete_response(text)
                        
                        # Check token count
                        token_count = self.count_tokens(text)
                        if token_count > max_response_tokens * 1.1:  # 10% buffer
                            print(f"⚠️ {self.config.name}: Response truncated ({token_count} tokens)")
                            text = self._truncate_to_tokens(text, max_response_tokens)
                        
                        # Store in history
                        self.conversation_history.append({
                            "speaker": self.config.name,
                            "content": text,
                            "tokens": token_count,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Truncate history if needed
                        self._truncate_history()
                        
                        return text
                        
        except Exception as e:
            print(f"⚠️ API error for {self.config.name}: {str(e)[:100]}")
        
        return None
    
    def _build_token_aware_prompt(self, topic: str, opponent: str, is_opening: bool) -> str:
        """Build prompt that considers token limits"""
        
        if is_opening:
            return f"""TOPIC: {topic}

Give your OPENING STATEMENT as {self.config.name} arguing {self.config.position}.

IMPORTANT: You have {self.config.max_tokens} tokens maximum.
Make your opening statement complete, concise, and impactful within this limit.
Focus on one or two key points maximum.

Your opening statement:"""
        
        else:
            # Include recent history (truncated)
            history_context = ""
            if self.conversation_history:
                recent = self.conversation_history[-3:]  # Last 3 exchanges
                history_context = "\nRecent exchanges:\n" + "\n".join(
                    [f"{msg['speaker']}: {msg['content']}" for msg in recent]
                )
            
            return f"""TOPIC: {topic}
{history_context}

OPPONENT'S LATEST STATEMENT: "{opponent}"

Respond as {self.config.name} arguing {self.config.position}.

TOKEN LIMIT: {self.config.max_tokens} tokens maximum.
- Counter their point concisely
- Add ONE new supporting argument
- Complete ALL sentences
- End with proper punctuation
- DO NOT start new points you can't finish

Your response:"""
    
    def _ensure_complete_response(self, text: str) -> str:
        """Ensure response ends with complete sentence"""
        
        # Remove trailing whitespace
        text = text.strip()
        
        # If empty, return fallback
        if not text:
            return "I need to reconsider that point carefully."
        
        # Ensure it ends with punctuation
        if text[-1] not in ['.', '!', '?']:
            # Find last sentence end
            last_period = text.rfind('.')
            last_excl = text.rfind('!')
            last_question = text.rfind('?')
            last_end = max(last_period, last_excl, last_question)
            
            if last_end != -1:
                # Truncate at last complete sentence
                text = text[:last_end + 1]
            else:
                # No complete sentences, add period
                text = text + '.'
        
        # Remove any "I think..." or "In my opinion..." if truncated
        incomplete_phrases = [
            "although", "however", "but", "while", "despite", 
            "on the other hand", "in contrast", "nevertheless"
        ]
        
        # Check if ends with conjunction (likely incomplete)
        words = text.lower().split()
        if len(words) > 2 and words[-1] in incomplete_phrases:
            # Remove last incomplete phrase
            text = ' '.join(words[:-1]).capitalize() + '.'
        
        return text
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit token limit"""
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate tokens
        truncated_tokens = tokens[:max_tokens]
        
        # Decode back to text
        truncated_text = self.tokenizer.decode(truncated_tokens)
        
        # Ensure it ends with complete sentence
        return self._ensure_complete_response(truncated_text)
    
    def _get_fallback_response(self, is_opening: bool, opponent: str = "") -> str:
        """Get token-aware fallback responses"""
        
        if self.config.position == "for":
            if is_opening:
                responses = [
                    "I support this position because the benefits are clear and significant.",
                    "The evidence strongly favors this approach for several key reasons.",
                    "This direction offers important advantages we should embrace.",
                ]
            else:
                if opponent:
                    responses = [
                        "That's a valid concern, but the data supports my position more strongly.",
                        "While you raise good points, the advantages outweigh them significantly.",
                        "I understand your perspective, but consider the proven benefits instead.",
                    ]
                else:
                    responses = [
                        "The statistics clearly support moving forward with this plan.",
                        "We should focus on the demonstrated advantages of this approach.",
                    ]
        else:  # against
            if is_opening:
                responses = [
                    "I have serious concerns about this direction due to significant risks.",
                    "We should reconsider this approach because of potential negative impacts.",
                    "The evidence suggests we need more caution before proceeding.",
                ]
            else:
                if opponent:
                    responses = [
                        "That argument overlooks important risks we must consider.",
                        "There are significant flaws in that position we need to address.",
                        "We're not accounting for all potential negative consequences.",
                    ]
                else:
                    responses = [
                        "The risks involved require more careful consideration.",
                        "There are better alternatives we should explore instead.",
                    ]
        
        # Ensure responses fit token limit
        response = random.choice(responses)
        tokens = self.count_tokens(response)
        
        if tokens > self.config.max_tokens:
            # Truncate if needed
            response = self._truncate_to_tokens(response, self.config.max_tokens)
        
        return response

class TokenAwareDebateSystem:
    """Debate system with token awareness"""
    
    def __init__(self, topic: str, agent1: TokenAwareDebateAgent, agent2: TokenAwareDebateAgent):
        self.topic = topic
        self.agent1 = agent1
        self.agent2 = agent2
        self.voice_engine = FixedVoiceEngine()
        self.debate_history: List[Dict] = []
        
        print("\n" + "="*60)
        print("🤖 TOKEN-AWARE AI DEBATE")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"FOR: {agent1.config.name} ({agent1.config.max_tokens} tokens max)")
        print(f"AGAINST: {agent2.config.name} ({agent2.config.max_tokens} tokens max)")
        print("="*60)
    
    async def conduct_debate(self):
        """Conduct token-aware debate"""
        
        print("\n🎙️ Starting debate...")
        await asyncio.sleep(2)
        
        # Test voices
        print("\n🔊 Testing voices...")
        voice1 = VoiceConfig(
            name=self.agent1.config.name,
            voice_gender=self.agent1.config.voice_gender,
            voice_speed=self.agent1.config.voice_speed
        )
        voice2 = VoiceConfig(
            name=self.agent2.config.name,
            voice_gender=self.agent2.config.voice_gender,
            voice_speed=self.agent2.config.voice_speed
        )
        
        self.voice_engine.speak(f"Testing {self.agent1.config.name} voice.", voice1)
        await asyncio.sleep(1)
        self.voice_engine.speak(f"Testing {self.agent2.config.name} voice.", voice2)
        await asyncio.sleep(1)
        
        print("\n✅ Voices ready. Starting debate...")
        print("="*50)
        
        # OPENING STATEMENTS
        print("\n📣 OPENING STATEMENTS")
        print("="*50)
        
        # Agent 1 opening
        print(f"\n{self.agent1.config.name}: Preparing opening (max {self.agent1.config.max_tokens} tokens)...")
        opening1 = await self.agent1.get_response(self.topic, is_opening=True)
        token_count1 = self.agent1.count_tokens(opening1)
        print(f"   Tokens used: {token_count1}/{self.agent1.config.max_tokens}")
        self.voice_engine.speak(opening1, voice1)
        self.debate_history.append({"speaker": self.agent1.config.name, "text": opening1, "tokens": token_count1})
        await asyncio.sleep(1)
        
        # Agent 2 opening
        print(f"\n{self.agent2.config.name}: Preparing opening (max {self.agent2.config.max_tokens} tokens)...")
        opening2 = await self.agent2.get_response(self.topic, opening1, is_opening=True)
        token_count2 = self.agent2.count_tokens(opening2)
        print(f"   Tokens used: {token_count2}/{self.agent2.config.max_tokens}")
        self.voice_engine.speak(opening2, voice2)
        self.debate_history.append({"speaker": self.agent2.config.name, "text": opening2, "tokens": token_count2})
        await asyncio.sleep(1)
        
        # DEBATE ROUNDS
        for round_num in range(1, 5):
            print(f"\n🔄 ROUND {round_num}")
            print("="*50)
            
            # Agent 1 responds
            last_statement = self.debate_history[-1]["text"]
            print(f"\n{self.agent1.config.name}: Responding to opponent...")
            resp1 = await self.agent1.get_response(self.topic, last_statement)
            token1 = self.agent1.count_tokens(resp1)
            print(f"   Tokens: {token1}/{self.agent1.config.max_tokens}")
            
            if self._check_completeness(resp1):
                self.voice_engine.speak(resp1, voice1)
                self.debate_history.append({"speaker": self.agent1.config.name, "text": resp1, "tokens": token1})
            else:
                print("   ⚠️ Response incomplete, using fallback")
                fallback1 = "Let me rephrase that point more clearly."
                self.voice_engine.speak(fallback1, voice1)
                self.debate_history.append({"speaker": self.agent1.config.name, "text": fallback1, "tokens": self.agent1.count_tokens(fallback1)})
            
            await asyncio.sleep(0.5)
            
            # Agent 2 responds
            print(f"\n{self.agent2.config.name}: Responding to opponent...")
            resp2 = await self.agent2.get_response(self.topic, resp1)
            token2 = self.agent2.count_tokens(resp2)
            print(f"   Tokens: {token2}/{self.agent2.config.max_tokens}")
            
            if self._check_completeness(resp2):
                self.voice_engine.speak(resp2, voice2)
                self.debate_history.append({"speaker": self.agent2.config.name, "text": resp2, "tokens": token2})
            else:
                print("   ⚠️ Response incomplete, using fallback")
                fallback2 = "I need to address that point differently."
                self.voice_engine.speak(fallback2, voice2)
                self.debate_history.append({"speaker": self.agent2.config.name, "text": fallback2, "tokens": self.agent2.count_tokens(fallback2)})
            
            await asyncio.sleep(0.5)
        
        # CLOSING
        print("\n📣 CLOSING STATEMENTS")
        print("="*50)
        
        print(f"\n{self.agent1.config.name}: Final statement...")
        close1 = await self.agent1.get_response(self.topic, "Give your final complete summary.")
        token_close1 = self.agent1.count_tokens(close1)
        print(f"   Tokens: {token_close1}/{self.agent1.config.max_tokens}")
        self.voice_engine.speak(close1, voice1)
        
        await asyncio.sleep(1)
        
        print(f"\n{self.agent2.config.name}: Final statement...")
        close2 = await self.agent2.get_response(self.topic, "Give your final complete summary.")
        token_close2 = self.agent2.count_tokens(close2)
        print(f"   Tokens: {token_close2}/{self.agent2.config.max_tokens}")
        self.voice_engine.speak(close2, voice2)
        
        # SUMMARY
        await asyncio.sleep(1)
        print("\n" + "="*60)
        print("📊 DEBATE STATISTICS")
        print("="*60)
        
        total_tokens = sum(item["tokens"] for item in self.debate_history)
        avg_tokens = total_tokens / len(self.debate_history) if self.debate_history else 0
        
        print(f"Total exchanges: {len(self.debate_history)}")
        print(f"Total tokens used: {total_tokens}")
        print(f"Average tokens per response: {avg_tokens:.1f}")
        print(f"Topic: {self.topic}")
        print("="*60)
        
        # Save transcript with token info
        self._save_token_aware_transcript()
    
    def _check_completeness(self, text: str) -> bool:
        """Check if response is complete"""
        if not text:
            return False
        
        # Check for proper ending
        if text[-1] not in ['.', '!', '?']:
            return False
        
        # Check for incomplete conjunctions at end
        incomplete_indicators = ['although', 'but', 'however', 'while', 'though', 'despite']
        words = text.lower().strip().split()
        
        if len(words) > 0 and words[-1] in incomplete_indicators:
            return False
        
        # Check sentence balance (rough check)
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            return False
        
        # Last sentence should have reasonable length
        last_sentence = sentences[-1]
        if len(last_sentence.split()) < 2:  # Very short last sentence
            return False
        
        return True
    
    def _save_token_aware_transcript(self):
        """Save transcript with token information"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debate_tokens_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("TOKEN-AWARE AI DEBATE TRANSCRIPT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Topic: {self.topic}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Agent FOR: {self.agent1.config.name} ({self.agent1.config.max_tokens} token limit)\n")
            f.write(f"Agent AGAINST: {self.agent2.config.name} ({self.agent2.config.max_tokens} token limit)\n")
            f.write("="*60 + "\n\n")
            
            for i, exchange in enumerate(self.debate_history, 1):
                f.write(f"Exchange {i}: {exchange['speaker']}\n")
                f.write(f"Tokens: {exchange['tokens']}\n")
                f.write(f"Statement: {exchange['text']}\n")
                f.write("-"*40 + "\n")
        
        print(f"💾 Token-aware transcript: {filename}")

# Create token-aware agents
def create_token_aware_agents(api_key: str = ""):
    """Create agents with token awareness"""
    
    agent1 = TokenAwareDebateAgent(
        AgentConfig(
            name="Alex",
            position="for",
            personality="Logical, analytical, cites data and statistics. Keeps responses concise and complete.",
            voice_gender="male",
            voice_speed=170,
            max_tokens=80  # ~20-25 words
        ),
        api_key
    )
    
    agent2 = TokenAwareDebateAgent(
        AgentConfig(
            name="Jordan",
            position="against",
            personality="Passionate, ethical, focuses on human impact. Ensures responses are self-contained.",
            voice_gender="female",
            voice_speed=190,
            max_tokens=200  # ~20-25 words
        ),
        api_key
    )
    
    return agent1, agent2