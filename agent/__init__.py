"""
Agent package initialization.
Handles environment variables and client initialization.
"""
import os

from cozepy import COZE_CN_BASE_URL, AsyncCoze, AsyncTokenAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
COZE_API_TOKEN = os.getenv("COZE_API_TOKEN")
BOT_ID = os.getenv("BOT_ID")

mcp_servers = os.getenv("MCP_SERVERS") or ''
MCP_SERVERS = [url.strip() for url in mcp_servers.split(",") if url.strip()]

if not COZE_API_TOKEN:
    raise ValueError("COZE_API_TOKEN environment variable is required")

if not BOT_ID:
    raise ValueError("BOT_ID environment variable is required")

# Initialize Coze client
acoze_client = AsyncCoze(auth=AsyncTokenAuth(token=COZE_API_TOKEN), base_url=COZE_CN_BASE_URL)

# Export the client and constants for use by other modules
__all__ = ['acoze_client', 'BOT_ID', 'COZE_API_TOKEN', 'MCP_SERVERS']
