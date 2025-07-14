import asyncio
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()

# MySQL connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "dummy")

def create_agent():
    # Create configuration dictionary for MySQL MCP server
    # Using mysql-mcp-server package (imports as mysql_mcp_server)
    config = {
    # "mcpServers": {
    #     "mysql": {
    #         "command": "uvx",
    #         "args": [
    #             "mysql-mcp-server",
    #             f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #         ]
    #     }
    # }
    "mcpServers": {
    "sql": {
      "command": "uv",
      "args": ["--directory", "/Users/arpanbhusal/dev/MCP", "run", "main.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "Abcd@4321",
        "DB_NAME": "dummy"
      }
    }
  }
}
    
    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)
    
    # Create Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.8,
        max_tokens=1024,
        timeout=2000,
        max_retries=2
    )
    
    # Create agent with the client
    return MCPAgent(llm=llm, client=client, max_steps=30)

async def run_agent_query(query):
    agent = create_agent()
    
    # Add context about the database schema (not mandatory but can be helpful for the LLM)
    full_query = f"""
You are working with MySQL 9.3.0 database.

FORBIDDEN SQL FUNCTIONS (DO NOT USE):
- PERCENTILE_CONT() ❌
- PERCENTILE_DISC() ❌
- WITHIN GROUP ❌

ALLOWED MySQL FUNCTIONS:
- ROW_NUMBER() OVER() ✅
- COUNT() OVER() ✅
- AVG(), MAX(), MIN() ✅

For median calculation, ALWAYS use this pattern:
SELECT age FROM (
  SELECT age, ROW_NUMBER() OVER (ORDER BY age) as row_num,
         COUNT(*) OVER () as total_count
  FROM employee
) ranked
WHERE row_num = CEIL(total_count / 2.0)

User question: {query}
"""

    
    try:
        result = await agent.run(full_query)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    
    query = data['query']
    
    # Run the async function in the Flask context
    result = asyncio.run(run_agent_query(query))
    
    return jsonify(result)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    app.run(debug=True)