import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp_coordinator import MCPCoordinator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS with maximum permissiveness for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Initialize MCP Coordinator
mcp_coordinator = MCPCoordinator()

@app.post("/api/properties")
async def chat(request: Request):
    try:
        logger.info("Received chat request")
        body = await request.json()
        logger.info(f"Request body: {body}")

        user_input = body.get('message')
        session_id = body.get('session_id')

        if not session_id:
            return JSONResponse(status_code=400, content={"error": "session_id is required"})

        logger.info(f"[Session {session_id}] Processing input: {user_input}")

        result = await mcp_coordinator.process_request(user_input, session_id)

        logger.info(f"MCP response: {result}")
        
        return JSONResponse(
            content={"response": result},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )