#!/usr/bin/env python3
"""
Simple test for X Business Radar functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligent_agent import IntelligentTwitterAgent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_radar():
    """Test the radar tool with simple output"""
    agent = None
    try:
        print("Starting X Business Radar test...")
        agent = IntelligentTwitterAgent(headless=False)
        
        print("Testing radar with 'automation' search...")
        result = agent._use_radar_tool('automation', 'detailed')
        
        print("\n" + "="*50)
        print("RADAR RESULTS:")
        print("="*50)
        print(result)
        print("="*50)
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if agent:
            try:
                agent.shutdown()
                print("Agent shutdown complete")
            except:
                pass

if __name__ == "__main__":
    test_radar() 