#!/usr/bin/env python3
"""
Test script to validate browser_open_page function directly
"""
import asyncio
import sys
import os

# Add current directory to path so we can import server modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import browser_open_page

async def test_browser_open_page():
    """Test the browser_open_page function directly"""
    print("Testing browser_open_page function...")
    
    try:
        # Test with simple URL first
        print("\n1. Testing with example.com...")
        result = await browser_open_page("https://example.com", "load", 15000)
        print(f"Result: {result}")
        
        if "error" not in result:
            print("✓ example.com test successful!")
            
            # Test with the problematic MSCI URL
            print("\n2. Testing with MSCI URL...")
            result2 = await browser_open_page("https://www.msci.com/indexes", "load", 30000)
            print(f"Result: {result2}")
            
            if "error" not in result2:
                print("✓ MSCI URL test successful!")
            else:
                print(f"✗ MSCI URL failed: {result2['error']}")
        else:
            print(f"✗ example.com failed: {result['error']}")
            
    except Exception as e:
        print(f"✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browser_open_page()) 