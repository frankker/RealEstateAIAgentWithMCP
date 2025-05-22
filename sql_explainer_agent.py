import logging
from typing import Dict, Any
import together
from langchain_core.runnables import RunnableConfig
from langsmith import traceable
import os

logger = logging.getLogger(__name__)

class SQLExplainerAgent:
    """
    Specialized agent responsible for explaining SQL queries in layman terms
    """
    
    def __init__(self):
        logger.info("[SQL Explainer Agent] Initialized")
    
    @traceable(
        name="sql_explainer_explain_sql",
        tags=["sql-explainer", "llm", "real-estate"],
        metadata={"agent_type": "sql_explainer"}
    )
    async def explain_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Generate layman explanation for SQL query
        
        Args:
            sql_query: The SQL query to explain
            
        Returns:
            Dict containing explanation and status
        """
        logger.info(f"[SQL Explainer Agent] Explaining SQL: {sql_query}")
        
        if not sql_query:
            return {
                "explanation": "Sorry, I cannot explain the SQL as none was generated.",
                "status": "error"
            }
        
        try:
            # Build the explanation prompt
            prompt = self._build_explanation_prompt(sql_query)
            
            # Call Together API with tracing
            explanation = await self._call_together_api_with_tracing(prompt)
            
            # Calculate quality score
            quality_score = self.get_explanation_quality_score(explanation)
            
            logger.info(f"[SQL Explainer Agent] Generated explanation: {explanation}")
            
            result = {
                "explanation": explanation,
                "status": "success",
                "quality_score": quality_score
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[SQL Explainer Agent] Error explaining SQL: {e}", exc_info=True)
            
            return {
                "explanation": "There was an error explaining the SQL query.",
                "status": "error"
            }
    
    @traceable(
        name="together_api_explanation_call",
        tags=["together-ai", "explanation", "llm-call"],
        metadata={"model": "mistralai/Mistral-7B-Instruct-v0.3"}
    )
    async def _call_together_api_with_tracing(self, prompt: str) -> str:
        """Call Together API with LangSmith tracing"""
        response = together.Complete.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            prompt=prompt,
            max_tokens=100,
            temperature=0.3,
            stop=["\n"]
        )
        
        explanation = response['choices'][0]['text'].strip().capitalize()
        return explanation
    
    def _build_explanation_prompt(self, sql_query: str) -> str:
        """Build prompt for SQL explanation"""
        return f"""
You are an AI that summarizes SQL queries as simple, clear search descriptions for retail real estate users.

Only describe what the query is trying to search for, based on the filter conditions in the WHERE clause. Do not explain SQL syntax. Keep it short, natural, and to the point.

Examples:
SQL: SELECT * FROM london_properties WHERE type = 'flats' AND bedroom_no > 3
→ Showing flats with more than 3 bedrooms.

SQL: SELECT * FROM london_properties WHERE price < 700000 AND type = 'bungalow'
→ Showing bungalows priced under 700,000.

SQL: SELECT * FROM london_properties
→ Showing all properties.

SQL: SELECT * FROM london_properties WHERE type = 'detached' AND bedroom_no = 2 AND bathroom_no = 2
→ Showing detached homes with 2 bedrooms and 2 bathrooms.

Now summarize this query:
SQL: {sql_query}
→
""".strip()
    
    def get_explanation_quality_score(self, explanation: str) -> float:
        """
        Calculate quality score for explanation (for future improvements)
        
        Args:
            explanation: The generated explanation
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Simple heuristic scoring - can be enhanced with more sophisticated metrics
        if not explanation or len(explanation.strip()) < 10:
            return 0.0
        
        # Check for key indicators of good explanations
        good_indicators = [
            "showing" in explanation.lower(),
            "properties" in explanation.lower() or "homes" in explanation.lower(),
            any(word in explanation.lower() for word in ["bedroom", "bathroom", "price", "type"])
        ]
        
        score = sum(good_indicators) / len(good_indicators)
        
        # Penalize overly long explanations
        if len(explanation) > 200:
            score *= 0.8
        
        return score