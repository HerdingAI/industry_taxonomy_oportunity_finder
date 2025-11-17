#!/usr/bin/env python3
"""Test API connectivity"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

print("Testing API connection...")
print(f"API Key loaded: {os.getenv('OPENROUTER_API_KEY')[:20]}...")
print(f"Model: {os.getenv('OPENROUTER_MODEL')}")

try:
    llm = ChatOpenAI(
        model=os.getenv('OPENROUTER_MODEL', 'openrouter/sherlock-think-alpha'),
        openai_api_key=os.getenv('OPENROUTER_API_KEY'),
        openai_api_base='https://openrouter.ai/api/v1',
        temperature=0.7
    )
    
    print("\nSending test request...")
    response = llm.invoke("Say 'API connected successfully' if you can read this.")
    print(f"\n✅ Response: {response.content}")
    print("\n✅ API connection working!")
    
except Exception as e:
    print(f"\n❌ API Error: {e}")
    import traceback
    traceback.print_exc()
