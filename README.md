# AI Master Control Program (MCP) Server

The AI MCP Server enables AI models, including locally hosted models with Ollama, to interact with your computer system. It acts as a bridge that allows AI models to:

- Execute system commands
- Create, read, update, and delete files
- Control other programs
- Communicate with each other

## Architecture

The system consists of:

1. **MCP Server**: Central server that processes requests from AI models
2. **Client Library**: Enables easy integration with AI models
3. **Model Connectors**: Interfaces with various AI model backends (Ollama, etc.)
4. **Task Execution Engine**: Performs system operations and program control

## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://github.com/ollama/ollama) (optional, for local model hosting)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/master_mcp_server.git
   cd master_mcp_server
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Usage

### Starting the Server

Run the MCP server:

```
python startup.py
```

By default, the server will listen on `0.0.0.0:8000`.

### Connecting AI Models

To connect an AI model to the MCP server, use the client library:

```python
from mcp_client import MCPClient

# Initialize client
client = MCPClient("http://localhost:8000", "your-secret-api-key")

# Connect to an Ollama model
result = client.connect_model("llama2", "ollama", {"host": "http://localhost:11434"})
print(f"Connection result: {result}")
```

### Executing System Operations

Once connected, AI models can perform various system operations:

```python
# Execute a command
result = client.execute_system_command("llama2", "echo", ["Hello, World!"])

# Write a file
result = client.write_file("llama2", "test.txt", "This is a test file created by an AI!")

# Read a file
result = client.read_file("llama2", "test.txt")

# Start a program
result = client.start_program("llama2", "notepad.exe")

# Stop a program
result = client.stop_program("llama2", pid)

# Query another model
result = client.query_model("llama2", "llama2", "What is the capital of France?")
```

## API Reference

### Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/connect_model` | POST | Connect to an AI model |
| `/disconnect_model/{model_id}` | POST | Disconnect from an AI model |
| `/list_models` | GET | List all connected models |
| `/execute_task` | POST | Execute a task requested by an AI model |
| `/task_status/{task_id}` | GET | Get the status of a task |

### Client Methods

| Method | Description |
|--------|-------------|
| `connect_model(model_id, model_type, config)` | Connect to an AI model |
| `disconnect_model(model_id)` | Disconnect from an AI model |
| `list_models()` | List all connected models |
| `execute_system_command(model_id, command, args, working_dir, timeout)` | Execute a system command |
| `execute_file_operation(model_id, operation, path, content)` | Execute a file operation |
| `control_program(model_id, action, program_path, args, pid)` | Control a program |
| `query_model(model_id, target_model, prompt)` | Query an AI model |

## Security Considerations

**IMPORTANT**: This server grants AI models significant access to your system. Use with caution.

Security measures implemented:
- API key authentication
- Logging of all operations
- Configurable permissions (coming soon)
- Rate limiting (coming soon)

## Extension Points

The MCP server can be extended to support:
- Additional AI model backends
- More sophisticated program control
- GUI interaction capabilities
- Web browsing capabilities
- Network operation capabilities

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.