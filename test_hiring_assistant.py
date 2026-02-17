"""
Test script for the hiring assistant chatbot.
Tests the complete conversation flow via API calls.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_chat_endpoint(message, conversation_state=None):
    """Send a message to the chat endpoint and return the response."""
    payload = {
        "message": message,
        "conversation_state": conversation_state
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat/hiring",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 8000")
        print("Run: cd backend && python main.py")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def display_response(data):
    """Display the assistant's response and collected info."""
    if not data:
        return
    
    print(f"🤖 Assistant: {data['response']}\n")
    
    # Show collected candidate info
    if data.get('candidate_info'):
        info = data['candidate_info']
        collected = {k: v for k, v in info.items() if v is not None}
        if collected:
            print("📋 Collected Information:")
            for key, value in collected.items():
                print(f"   - {key}: {value}")
            print()
    
    # Show stage
    print(f"📍 Stage: {data['stage']}")
    
    # Show if conversation ended
    if data.get('conversation_ended'):
        print("✅ Conversation Ended")
    
    print()

def run_complete_flow():
    """Run a complete conversation flow test."""
    print_section("TalentScout Hiring Assistant - Test Script")
    
    conversation_state = None
    
    # Test messages simulating a complete conversation
    test_messages = [
        "Hello",
        "My name is Sarah Johnson",
        "sarah.johnson@email.com",
        "+1-555-123-4567",
        "I have 7 years of experience",
        "I'm interested in the Senior Full Stack Developer position",
        "I'm located in Austin, Texas",
        "My tech stack includes Python, Django, React, TypeScript, PostgreSQL, Redis, Docker, and AWS",
        "Thank you, I'm done for now",
        "bye"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"👤 User ({i}/{len(test_messages)}): {message}")
        
        data = test_chat_endpoint(message, conversation_state)
        
        if data:
            display_response(data)
            conversation_state = data['conversation_state']
            
            # Show tech questions if generated
            if data.get('tech_questions'):
                print("❓ Technical Questions Generated:")
                for tech, questions in data['tech_questions'].items():
                    print(f"\n   {tech}:")
                    for j, q in enumerate(questions, 1):
                        print(f"   {j}. {q}")
                print()
            
            if data.get('conversation_ended'):
                print_section("Conversation Completed Successfully!")
                break
        else:
            print("❌ Test failed - could not get response")
            break
        
        # Small delay between messages
        time.sleep(1)
    
    print_section("Test Complete")

def test_individual_endpoint():
    """Test individual messages for debugging."""
    print_section("Individual Message Test")
    
    print("Enter messages to test (type 'exit' to quit):")
    conversation_state = None
    
    while True:
        message = input("\n👤 You: ").strip()
        
        if message.lower() in ['exit', 'quit', 'q']:
            break
        
        if not message:
            continue
        
        data = test_chat_endpoint(message, conversation_state)
        
        if data:
            display_response(data)
            conversation_state = data['conversation_state']
            
            if data.get('tech_questions'):
                print("❓ Technical Questions:")
                for tech, questions in data['tech_questions'].items():
                    print(f"\n   {tech}:")
                    for j, q in enumerate(questions, 1):
                        print(f"   {j}. {q}")
                print()
            
            if data.get('conversation_ended'):
                print("Conversation ended. Starting fresh...")
                conversation_state = None

def test_api_health():
    """Test if the API is running."""
    print_section("API Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend API is running!")
            print(f"   Message: {data.get('message')}")
            print(f"   Endpoints: {data.get('endpoints')}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        print("   Make sure the backend is running:")
        print("   cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🎯 TalentScout Hiring Assistant - Test Suite\n")
    print("Choose a test mode:")
    print("1. Complete conversation flow (automated)")
    print("2. Individual message testing (interactive)")
    print("3. API health check only")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        if test_api_health():
            print("\nStarting automated conversation flow test...\n")
            time.sleep(2)
            run_complete_flow()
    elif choice == "2":
        if test_api_health():
            print("\nStarting interactive testing mode...\n")
            time.sleep(1)
            test_individual_endpoint()
    elif choice == "3":
        test_api_health()
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice. Exiting.")
