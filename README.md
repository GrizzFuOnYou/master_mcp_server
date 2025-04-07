# AI Master Control Program (MCP) Server

The AI MCP Server enables AI models, including locally hosted models with Ollama and Claude Desktop, to interact with your computer system. It acts as a bridge that allows AI models to:

- Execute system commands
- Create, read, update, and delete files
- Control other programs
- Communicate with each other

## Architecture

The system consists of:

1. **MCP Server**: Central server that processes requests from AI models
2. **Client Library**: Enables easy integration with AI models
3. **Model Connectors**: Interfaces with various AI model backends (Ollama, Claude Desktop, etc.)
4. **Task Execution Engine**: Performs system operations and program control

## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://github.com/ollama/ollama) (optional, for local model hosting)
- [Claude Desktop](https://claude.ai/desktop) (recommended default model)

### Automated Installation

For quick and easy installation, use the provided installation script:

```bash
# Clone the repository
git clone https://github.com/GrizzFuOnYou/master_mcp_server.git
cd master_mcp_server

# Run the installation script
python install.py
```

The installation script will:
1. Verify Python version compatibility
2. Install all dependencies
3. Create a directory structure
4. Configure environment variables
5. Create platform-specific startup scripts
6. Set up Claude Desktop as the default AI model

### Manual Setup

If you prefer manual installation:

1. Clone the repository:
   ```
   git clone https://github.com/GrizzFuOnYou/master_mcp_server.git
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

#### Using Startup Script (Recommended)

After installation:
- **Windows**: Run `start_mcp_server.bat`
- **Linux/Mac**: Run `./start_mcp_server.sh`

#### Manual Start

Run the MCP server:

```
python startup.py
```

By default, the server will listen on `0.0.0.0:8000`.

### Connecting AI Models

#### Claude Desktop (Default)

Claude Desktop is configured as the default model. To use it:

1. Make sure Claude Desktop is running on your system
2. The server will automatically attempt to connect on startup
3. Claude Desktop should be available at the default location: `http://localhost:5000/api`

If you need to manually connect:

```python
from mcp_client import MCPClient

# Initialize client
client = MCPClient("http://localhost:8000", "your-secret-api-key")

# Connect to Claude Desktop
result = client.connect_model("claude-desktop", "claude", {"api_url": "http://localhost:5000/api"})
print(f"Connection result: {result}")
```

#### Claude Desktop Connection JSON

If you need to manually configure Claude Desktop integration, use the following JSON configuration:

```json
{
  "model_id": "claude-desktop",
  "model_type": "claude",
  "config": {
    "api_url": "http://localhost:5000/api",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

#### Ollama Models

To connect to an Ollama model:

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
result = client.execute_system_command("claude-desktop", "echo", ["Hello, World!"])

# Write a file
result = client.write_file("claude-desktop", "test.txt", "This is a test file created by Claude!")

# Read a file
result = client.read_file("claude-desktop", "test.txt")

# Start a program
result = client.start_program("claude-desktop", "notepad.exe")

# Stop a program
result = client.stop_program("claude-desktop", pid)

# Query the AI model
result = client.query_model("claude-desktop", "claude-desktop", "What is the capital of France?")
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

## Model Configuration

### Claude Desktop Configuration

To connect to Claude Desktop, use the following configuration:

```json
{
  "api_url": "http://localhost:5000/api",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### Ollama Configuration

To connect to an Ollama model, use the following configuration:

```json
{
  "host": "http://localhost:11434"
}
```

## Security Considerations

**IMPORTANT**: This server grants AI models significant access to your system. Use with caution.

Security measures implemented:
- API key authentication
- Logging of all operations
- Configurable permissions (coming soon)
- Rate limiting (coming soon)

## Troubleshooting

### Claude Desktop Connection Issues

If you encounter issues connecting to Claude Desktop:

1. Ensure Claude Desktop is running
2. Verify the API URL (default: `http://localhost:5000/api`)
3. Check the logs for specific error messages
4. Restart Claude Desktop and try again

### Ollama Connection Issues

If you encounter issues connecting to Ollama:

1. Ensure Ollama is running (`ollama serve`)
2. Verify the model exists (`ollama list`)
3. Check the API URL (default: `http://localhost:11434`)
4. Try pulling the model again (`ollama pull modelname`)

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