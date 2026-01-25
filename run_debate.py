#!/usr/bin/env python3
"""
FIXED Main Runner - Simple and reliable
"""

import asyncio
import os
from dotenv import load_dotenv
from debate_core import WorkingDebateSystem, create_working_agents

# Load environment
load_dotenv()

# Topics
TOPICS = [
    "Artificial intelligence will create more jobs than it destroys",
    "Remote work is more productive than office work",
    "Social media has improved human connection",
    "Universal Basic Income should be implemented",
    "Electric vehicles are better for the environment",
]

def select_topic():
    """Simple topic selection"""
    print("\n📝 Select debate topic:")
    for i, topic in enumerate(TOPICS, 1):
        print(f"{i}. {topic}")
    
    try:
        choice = int(input(f"\nChoice (1-{len(TOPICS)}): "))
        return TOPICS[choice - 1]
    except:
        return TOPICS[0]

async def main():
    """Main - Simple and working"""
    
    print("\n" + "="*60)
    print("🤖 AI VERBAL DEBATE - WORKING VERSION")
    print("="*60)
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("\n🔑 OpenRouter API Key (optional)")
        print("Press Enter to use fallback responses")
        api_key = input("API key: ").strip()
    
    if api_key:
        print("✓ API key loaded")
    else:
        print("ℹ️ Using fallback responses (no API needed)")
    
    # Select topic
    topic = select_topic()
    
    # Create agents
    print("\n🎭 Creating agents...")
    agent1, agent2 = create_working_agents(api_key)
    
    print(f"\n⚙️  Debate Setup:")
    print(f"   Topic: {topic}")
    print(f"   FOR: {agent1.config.name} ({agent1.config.voice_gender} voice)")
    print(f"   AGAINST: {agent2.config.name} ({agent2.config.voice_gender} voice)")
    print(f"   Rounds: 4")
    print("="*60)
    
    # Important reminder
    print("\n🎧 CRITICAL: Ensure speakers are ON and volume is UP!")
    print("Both agents WILL speak if voices are available.")
    input("\nPress Enter to start debate...")
    
    # Run debate
    debate = WorkingDebateSystem(topic, agent1, agent2)
    
    try:
        await debate.conduct_debate()
    except KeyboardInterrupt:
        print("\n\n⚠️ Debate interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n✨ System complete!")

if __name__ == "__main__":
    asyncio.run(main())