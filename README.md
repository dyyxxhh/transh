# Command Output Translator

A Python script that executes a shell command, captures its output, and uses AI (DeepSeek or Ollama) to translate the output into Chinese.

## Features

- Execute any shell command and capture stdout
- Translate command output to Chinese using AI
- Support for both DeepSeek (cloud API) and Ollama (local models)
- Configuration via `.env` file
- Simple command-line interface

## Requirements

- Python 3.8+
- `requests` and `python-dotenv` packages

## Installation

1. Clone or download this repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your `.env` file (see Configuration section).

## Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env .env.example  # if you have an example file
```

Edit `.env`:

```ini
# Choose AI backend: deepseek or ollama
AI_BACKEND=deepseek

# DeepSeek configuration
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### DeepSeek Setup

1. Get an API key from [DeepSeek Platform](https://platform.deepseek.com/)
2. Replace `your_api_key_here` with your actual API key

### Ollama Setup

1. Install [Ollama](https://ollama.com/)
2. Pull a model: `ollama pull llama2`
3. Ensure Ollama service is running (`ollama serve`)

## Usage

Basic syntax:

```bash
python3 translate.py "command"
```

Examples:

```bash
# Translate npm help
python3 translate.py "npm -h"

# Translate system information
python3 translate.py "uname -a"

# Translate directory listing
python3 translate.py "ls -la"

# Translate pip help
python3 translate.py "pip --help"
```

The script will:
1. Execute the provided command
2. Display the original output
3. Send the output to the configured AI backend for translation
4. Display the Chinese translation

## How It Works

1. **Command Execution**: Uses Python's `subprocess` module to run the command and capture stdout.
2. **AI Translation**: Sends the captured text to either DeepSeek API or local Ollama instance with a translation prompt.
3. **Output**: Prints both the original output and the Chinese translation.

## Error Handling

- If the command fails, the error message will be captured and translated.
- If the AI API is unavailable or returns an error, the script will exit with an appropriate message.
- Missing API keys or misconfiguration will be reported.

## Limitations

- Maximum token limits apply based on the AI model used.
- Very long command outputs may need to be truncated.
- Translation quality depends on the AI model capabilities.
- Ollama requires the model to support Chinese translation.

## License

MIT