"""
Example usage of the MCP Real Estate Agent System
"""

import asyncio
import json
from mcp_coordinator import MCPCoordinator

async def main():
    """Example usage of the MCP system"""
    
    # Initialize the MCP coordinator
    coordinator = MCPCoordinator()
    
    # Example session
    session_id = "test_session_001"
    
    # Test queries
    test_queries = [
        "I'm looking for a 2-bedroom flat in London under £500,000",
        "Show me detached houses with at least 3 bedrooms",
        "Find bungalows with 2 bathrooms",
        "What properties do you have?",  # Should show all
        "I want a mansion with 10 bedrooms and a swimming pool",  # Should find no results
    ]
    
    print("🏠 MCP Real Estate Agent System Demo")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 30)
        
        # Process the query
        response = await coordinator.process_request(query, session_id)
        
        # Display results
        print(f"📋 Response: {response.get('content', 'N/A')}")
        
        if 'sql_query' in response:
            print(f"🔧 Generated SQL: {response['sql_query']}")
            
        if 'sql_explanation' in response:
            print(f"💡 Explanation: {response['sql_explanation']}")
            
        if 'row_count' in response:
            print(f"📊 Results found: {response['row_count']}")
    
    # Show conversation history
    print("\n📚 Session History:")
    print("-" * 20)
    history = coordinator.get_session_history(session_id)
    for msg in history:
        role = msg['role'].title()
        content = msg.get('content', 'N/A')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', 'N/A')
        print(f"{role}: {content}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())