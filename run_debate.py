#!/usr/bin/env python3
"""
UPDATED Main Runner - Token aware debate
"""

import asyncio
import os
from dotenv import load_dotenv

# Import token-aware version
try:
    from debate_core import TokenAwareDebateSystem, create_token_aware_agents
    TOKEN_AWARE_AVAILABLE = True
except ImportError:
    print("⚠️ tiktoken not installed. Install with: pip install tiktoken")
    TOKEN_AWARE_AVAILABLE = False
    from debate_core import WorkingDebateSystem, create_working_agents

# Load environment
load_dotenv()

# Topics with token estimates
TOPICS = [
    "AI creates more jobs than it destroys (debate)",
    "Remote work increases productivity (debate)",
    "Social media improves communication (debate)",
    "Electric cars help the environment (debate)",
    "Online education is effective (debate)",
]

def select_topic():
    """Select debate topic"""
    print("\n📝 Select debate topic:")
    for i, topic in enumerate(TOPICS, 1):
        print(f"{i}. {topic}")
    
    try:
        choice = int(input(f"\nChoice (1-{len(TOPICS)}): "))
        return TOPICS[choice - 1]
    except:
        return TOPICS[0]

async def main():
    """Main function with token awareness"""
    
    print("\n" + "="*60)
    if TOKEN_AWARE_AVAILABLE:
        print("🤖 TOKEN-AWARE AI DEBATE")
        print("AI will avoid incomplete statements")
    else:
        print("🤖 AI VERBAL DEBATE (Basic)")
    print("="*60)
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("\n🔑 OpenRouter API Key (optional for better responses)")
        print("Get free key: https://openrouter.ai/keys")
        print("Press Enter to use fallback responses")
        api_key = input("API key: ").strip()
    
    # Select topic
    topic = select_topic()
    
    if TOKEN_AWARE_AVAILABLE and api_key:
        print("\n🎯 Using token-aware system")
        print("Each response limited to ~80 tokens (complete sentences)")
        
        # Create token-aware agents
        print("\n🎭 Creating token-aware agents...")
        agent1, agent2 = create_token_aware_agents(api_key)
        
        # Create and run debate
        debate = TokenAwareDebateSystem(topic, agent1, agent2)
        
    else:
        print("\n🎯 Using basic system")
        if not TOKEN_AWARE_AVAILABLE:
            print("Install tiktoken for token awareness: pip install tiktoken")
        
        # Create basic agents
        from debate_core import WorkingDebateSystem, create_working_agents
        agent1, agent2 = create_working_agents(api_key)
        debate = WorkingDebateSystem(topic, agent1, agent2)
    
    # Display setup
    print(f"\n⚙️  Debate Setup:")
    print(f"   Topic: {topic}")
    print(f"   FOR: {agent1.config.name}")
    print(f"   AGAINST: {agent2.config.name}")
    print(f"   Mode: {'Token-aware' if TOKEN_AWARE_AVAILABLE and api_key else 'Basic'}")
    print("="*60)
    
    # Start debate
    print("\n🎧 Ensure speakers are ON!")
    input("\nPress Enter to start debate...")
    
    try:
        await debate.conduct_debate()
    except KeyboardInterrupt:
        print("\n\n⚠️ Debate interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Debate complete!")

if __name__ == "__main__":
    # Install tiktoken if not available
    if not TOKEN_AWARE_AVAILABLE:
        print("\n⚠️ For token awareness, install: pip install tiktoken")
        print("Proceeding with basic system...\n")
    
    asyncio.run(main())