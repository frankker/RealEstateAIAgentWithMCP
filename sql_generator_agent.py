import os
import logging
import random
from typing import List, Dict, Any, Optional
import psycopg2
import together
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langsmith import traceable

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SQLGeneratorAgent:
    """
    Specialized agent responsible for generating SQL queries from natural language
    """
    
    def __init__(self):
        # Database configuration
        self.pg_user = os.getenv("PG_USER")
        self.pg_password = os.getenv("PG_PASSWORD")
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT")
        self.pg_database = os.getenv("PG_DATABASE")
        
        logger.info(f"[SQL Generator Agent] Initialized with DB: {self.pg_host}:{self.pg_port}/{self.pg_database}")
    
    @traceable(
        name="sql_generator_generate_sql",
        tags=["sql-generator", "llm", "real-estate"],
        metadata={"agent_type": "sql_generator"}
    )
    async def generate_sql(self, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Generate SQL query from natural language input
        
        Args:
            message: User's natural language input
            conversation_history: Previous conversation context
            config: LangSmith configuration
            
        Returns:
            Dict containing status, sql_query, message, and row_count
        """
        logger.info(f"[SQL Generator Agent] Generating SQL for: {message}")
        
        try:
            # Create prompt with conversation history
            prompt = self._build_sql_prompt(message, conversation_history)
            
            # Generate SQL using Together API
            sql_output = await self._call_together_api_with_tracing(prompt)
            
            logger.info(f"[SQL Generator Agent] Generated SQL: {sql_output}")
            
            # Validate SQL format
            is_valid = self._is_valid_sql(sql_output)
            
            if is_valid:
                # Execute SQL to check for data
                row_count = await self._execute_sql_with_tracing(sql_output)
                
                if row_count is not None and row_count > 0:
                    result = {
                        "status": "valid_with_data",
                        "sql_query": sql_output,
                        "row_count": row_count,
                        "message": "SQL generated successfully"
                    }
                elif row_count is not None and row_count == 0:
                    result = {
                        "status": "valid_no_data",
                        "sql_query": sql_output,
                        "row_count": 0,
                        "message": self._get_no_data_message()
                    }
                else:
                    # SQL execution error
                    result = {
                        "status": "invalid",
                        "sql_query": None,
                        "message": "Generated SQL had execution errors"
                    }
            else:
                result = {
                    "status": "invalid",
                    "sql_query": None,
                    "message": "As a real estate AI agent, I am not intelligent enough to answer your question for now."
                }
            
            return result
                
        except Exception as e:
            logger.error(f"[SQL Generator Agent] Error generating SQL: {e}", exc_info=True)
            
            return {
                "status": "invalid",
                "sql_query": None,
                "message": "Error occurred while generating SQL query"
            }
    
    @traceable(
        name="together_api_call",
        tags=["together-ai", "llm-call"],
        metadata={"model": "mistralai/Mistral-7B-Instruct-v0.3"}
    )
    async def _call_together_api_with_tracing(self, prompt: str) -> str:
        """Call Together API with LangSmith tracing"""
        response = together.Complete.create(
            prompt=prompt,
            model="mistralai/Mistral-7B-Instruct-v0.3",
            max_tokens=128,
            temperature=0.2,
            stop=["\n"]
        )
        
        sql_output = response['choices'][0]['text'].strip()
        return sql_output
    
    @traceable(
        name="sql_execution",
        tags=["database", "execution"],
        metadata={"operation": "query_execution"}
    )
    async def _execute_sql_with_tracing(self, sql: str) -> Optional[int]:
        """Execute SQL query with LangSmith tracing"""
        return self._execute_sql_query(sql)
    
    def _build_sql_prompt(self, current_message: str, conversation_history: List[Dict]) -> str:
        """Build prompt for SQL generation including conversation history"""
        history_text = ""
        for msg in conversation_history:
            role = msg["role"]
            if 'sql_query' in msg:
                content = msg["sql_query"]
            else:
                content = msg["content"]
            prefix = "User" if role == "user" else "Assistant"
            history_text += f"{prefix}: {content}\n"
        
        # Add current message
        history_text += f"User: {current_message}\n"

        return f"""
You are a helpful assistant that generates valid PostgreSQL SELECT queries from a conversation.

The SQL must query from a table called `london_properties` with the following columns:
- address
- description
- price
- bedroom_no
- bathroom_no
- reception_no
- type (possible values: bungalow, terraced, flats, semi_detached, or detached)

The user may not express everything in one message. Combine all previous user messages to determine intent.

Only return the SQL query, nothing else.

If the combined user intent is not clear enough to form a valid query, return exactly: As a real estate AI agent, I am not intelligent enough to answer your question for now.

Conversation so far:
{history_text}
SQL:
"""
    
    def _is_valid_sql(self, text: str) -> bool:
        """Basic heuristic to verify SQL script format"""
        sql_keywords = ["SELECT", "FROM", "WHERE"]
        return all(keyword in text.upper() for keyword in sql_keywords)
    
    def _execute_sql_query(self, sql: str) -> Optional[int]:
        """Execute SQL query and return row count"""
        try:
            conn = psycopg2.connect(
                dbname=self.pg_database,
                user=self.pg_user,
                password=self.pg_password,
                host=self.pg_host,
                port=self.pg_port
            )
            cur = conn.cursor()
            cur.execute(sql)
            row_count = cur.rowcount
            cur.close()
            conn.close()
            return row_count
        except Exception as e:
            logger.error(f"[SQL Generator Agent] SQL execution error: {e}")
            return None
    
    def _get_no_data_message(self) -> str:
        """Get random message for no data found"""
        options = [
            "Sorry, we can't seem to find any availabilities that match your requirements.",
            "Sorry, no availability found.",
            "Oops, nothing found."
        ]
        return random.choice(options)