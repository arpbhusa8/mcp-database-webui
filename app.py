import asyncio
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()
DB_LINK = os.getenv("DB_LINK") # DB connection string

def create_agent():
    # Create configuration dictionary
    config = {
        "mcpServers": {
            "postgres": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-postgres",
                    DB_LINK
                ]
            }
        }
    }

    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent with the client
    return MCPAgent(llm=llm, client=client, max_steps=30)

async def run_agent_query(query):
    agent = create_agent()
    
    # Add context about the database schema (not mandatory but can be helpful for the LLM)
    full_query = f"The table is `users.users`, and among other columns, it contains `age`, `is_active` and `country_code`. {query}"
    
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