import logging
from typing import Dict, List, Any, Optional
from cachetools import LRUCache
from sql_generator_agent import SQLGeneratorAgent
from sql_explainer_agent import SQLExplainerAgent
from langchain_core.runnables import RunnableConfig
from langsmith import traceable
import os

logger = logging.getLogger(__name__)

class MCPCoordinator:
    """
    Multi-Agent Control Protocol Coordinator
    Orchestrates communication between SQL Generator and SQL Explainer agents
    """
    
    def __init__(self):
        self.sql_generator = SQLGeneratorAgent()
        self.sql_explainer = SQLExplainerAgent()
        # Allow memory for 1000 concurrent sessions
        self.session_store: Dict[str, List[Dict]] = LRUCache(maxsize=1000)
    
    @traceable(
        name="mcp_process_request",
        tags=["mcp", "coordinator", "real-estate"],
        metadata={"agent_type": "coordinator"}
    )
    async def process_request(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Main entry point for processing user requests
        Coordinates between SQL generation and explanation agents
        """
        logger.info(f"[MCP Coordinator][Session {session_id}] Processing: {message}")
        
        # Initialize session history if not present
        if session_id not in self.session_store:
            self.session_store[session_id] = []
        
        conversation_history = self.session_store[session_id]
        
        try:
            # Step 1: Generate SQL using SQL Generator Agent
            sql_result = await self._generate_sql_with_tracing(
                message=message,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            logger.info(f"[MCP Coordinator][Session {session_id}] SQL Generation Result: {sql_result}")
            
            # Step 2: Handle different SQL generation outcomes
            if sql_result["status"] == "valid_with_data":
                # SQL is valid and has data - explain it
                explanation_result = await self._explain_sql_with_tracing(
                    sql_query=sql_result["sql_query"],
                    session_id=session_id
                )
                
                # Construct successful response
                response = {
                    "role": "assistant",
                    "content": "SQL generated successfully",
                    "sql_query": sql_result["sql_query"],
                    "sql_explanation": explanation_result["explanation"],
                    "row_count": sql_result["row_count"]
                }
                
                # Update conversation history with successful interaction
                conversation_history.append({"role": "user", "content": message})
                conversation_history.append(response)
                # Update session store
                self.session_store[session_id] = conversation_history
                
            elif sql_result["status"] == "valid_no_data":
                # SQL is valid but no data found
                response = {
                    "role": "assistant",
                    "content": sql_result["message"]
                }
                
            else:  # invalid
                # SQL generation failed
                response = {
                    "role": "assistant",
                    "content": sql_result["message"]
                }
            
            logger.info(f"[MCP Coordinator][Session {session_id}] Final response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"[MCP Coordinator][Session {session_id}] Error: {e}", exc_info=True)
            
            return {
                "role": "assistant",
                "content": "Sorry, something went wrong with the AI agents.",
            }
    
    @traceable(
        name="sql_generation_step",
        tags=["mcp", "sql-generation"],
        metadata={"step": "generate_sql"}
    )
    async def _generate_sql_with_tracing(
        self, 
        message: str, 
        conversation_history: List[Dict],
        session_id: str
    ) -> Dict[str, Any]:
        """Generate SQL with LangSmith tracing"""
        return await self.sql_generator.generate_sql(
            message=message,
            conversation_history=conversation_history
        )
    
    @traceable(
        name="sql_explanation_step",
        tags=["mcp", "sql-explanation"],
        metadata={"step": "explain_sql"}
    )
    async def _explain_sql_with_tracing(
        self, 
        sql_query: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Explain SQL with LangSmith tracing"""
        return await self.sql_explainer.explain_sql(
            sql_query=sql_query
        )
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.session_store.get(session_id, [])
    
    def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self.session_store:
            del self.session_store[session_id]
            return True
        return False