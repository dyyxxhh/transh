#!/usr/bin/env python3
"""
Command output translator using OpenAI-compatible API with caching.
Usage: transh [options] "command"
"""

import os
import sys
import subprocess
import json
import hashlib
import signal
from pathlib import Path
from typing import Optional, Dict
import requests


# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\n\nInterrupted by user. Exiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# Default configuration
DEFAULT_CONFIG = {
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "api_key": "",
    "target_language": "Chinese",
    "stream": True
}

CONFIG_FILE = Path.home() / ".transh_config.json"
CACHE_DIR = Path.home() / ".transh_cache"
LANG_FILE = Path.home() / ".transh_lang.json"

# Built-in UI texts (English)
UI_TEXTS_EN = {
    "executing": "Executing",
    "output_length": "Command output ({} chars)",
    "translating": "Translating to {}...",
    "translation": "=== {} Translation ===",
    "translation_end": "=" * 27,
    "no_output": "No output to translate.",
    "translation_failed": "Translation failed.",
    "cached": "[Using cached translation]",
    "config_missing": "Configuration not found. Please run: transh -c",
    "current_language": "Current target language: {}",
    "enter_new_language": "Enter new target language: ",
    "translating_ui": "Translating UI texts to",
    "language_changed": "✓ Language changed and UI texts translated!",
    "usage": "Usage: transh [options] \"command\"",
    "examples": """Examples:
  transh "npm -h"              # Translate command output
  transh -t "hello"            # Translate text directly
  transh -t "hello" -l "日本語"  # Translate to Japanese temporarily
  transh -f out.txt in.txt     # Translate file
  transh -c                    # Configure AI settings
  transh -l                    # Change target language
  transh -l "日本語"             # Change target language directly
  transh -r "npm -h"           # Force refresh cache""",
    "options": """Options:
  -c              Interactive configuration
  -t "text"       Translate text directly
  -f output.txt   Translate input file and save to output
  -l [language]   Change target language (interactive if no language specified)
  -r              Force refresh cache (ignore existing cache)
  --vi-env        View current configuration
  -h, --help      Show this help message""",
    "file_not_found": "Error: File '{}' not found",
    "error": "Error: {}",
    "translation_saved": "✓ Translation saved to {}",
    "no_command": "Error: No command specified",
    "require_text": "Error: -t requires a text argument",
    "require_files": "Error: -f requires input and output file arguments"
}


def get_cache_path(text: str) -> Path:
    """Generate cache file path based on text hash."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create cache directory: {e}")
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return CACHE_DIR / f"{text_hash}.json"


def load_cache(text: str, target_lang: str) -> Optional[str]:
    """Load translation from cache if exists."""
    try:
        cache_file = get_cache_path(text)
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                if cache_data.get("target_language") == target_lang:
                    return cache_data.get("translation")
    except Exception:
        pass
    return None


def save_cache(text: str, translation: str, target_lang: str):
    """Save translation to cache."""
    try:
        cache_file = get_cache_path(text)
        cache_data = {
            "summary": text[:200] + ("..." if len(text) > 200 else ""),
            "target_language": target_lang,
            "translation": translation
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Silently ignore cache save errors
        pass


def load_config() -> Optional[Dict]:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return None
    return None


def save_config(config: Dict):
    """Save configuration to file."""
    try:
        # Ensure config directory exists
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error: Failed to save config: {e}")
        sys.exit(1)


def load_ui_texts() -> Dict[str, str]:
    """Load UI texts in target language."""
    if LANG_FILE.exists():
        try:
            with open(LANG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with default to ensure all keys exist
                result = UI_TEXTS_EN.copy()
                result.update(loaded)
                return result
        except Exception:
            pass
    return UI_TEXTS_EN.copy()


def save_ui_texts(texts: Dict[str, str]):
    """Save translated UI texts."""
    try:
        LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LANG_FILE, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save language file: {e}")


def interactive_config():
    """Interactive configuration setup."""
    ui = load_ui_texts()
    print("=== AI Configuration ===\n")
    
    config = load_config() or DEFAULT_CONFIG.copy()
    
    try:
        base_url = input(f"API Base URL [{config['base_url']}]: ").strip()
        if base_url:
            config['base_url'] = base_url
        
        model = input(f"Model [{config['model']}]: ").strip()
        if model:
            config['model'] = model
        
        api_key = input(f"API Key [{'*' * 8 if config['api_key'] else 'not set'}]: ").strip()
        if api_key:
            config['api_key'] = api_key
        
        target_lang = input(f"Target Language [{config['target_language']}]: ").strip()
        if target_lang:
            config['target_language'] = target_lang
        
        stream_input = input(f"Enable streaming output? (y/n) [{'y' if config.get('stream', True) else 'n'}]: ").strip().lower()
        if stream_input in ['y', 'n']:
            config['stream'] = (stream_input == 'y')
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(0)
    
    save_config(config)
    print("\n✓ Configuration saved!")
    
    # Translate UI texts if target language is not English
    if config['target_language'].lower() != "english":
        translating_text = ui.get('translating_ui', 'Translating UI texts to')
        print(f"\n{translating_text} {config['target_language']}...")
        translated_texts = translate_ui_texts(config)
        if translated_texts:
            save_ui_texts(translated_texts)
            print(ui.get("language_changed", "✓ Language changed and UI texts translated!"))
    else:
        # Remove custom language file if English
        if LANG_FILE.exists():
            LANG_FILE.unlink()
    
    return config


def translate_ui_texts(config: Dict) -> Optional[Dict[str, str]]:
    """Translate built-in UI texts to target language."""
    ui_json = json.dumps(UI_TEXTS_EN, ensure_ascii=False, indent=2)
    prompt = f"""Translate the following JSON values to {config['target_language']}. 
Rules:
1. Keep all keys in English unchanged
2. Only translate the string values
3. Keep {{}} placeholders exactly as they are (do not translate them)
4. Output valid JSON only, no explanations or markdown

{ui_json}"""
    
    # Force non-streaming for JSON translation
    translation = call_ai_api(prompt, config, is_json=True, force_no_stream=True)
    if translation:
        try:
            # Clean up potential markdown code blocks
            clean_translation = translation.strip()
            if clean_translation.startswith('```'):
                lines = clean_translation.split('\n')
                clean_translation = '\n'.join(lines[1:-1]) if len(lines) > 2 else clean_translation
            
            return json.loads(clean_translation)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response: {translation[:200]}...")
    return None


def change_language(new_lang: Optional[str] = None):
    """Change target language and retranslate UI texts."""
    config = load_config()
    if not config:
        ui = load_ui_texts()
        print(ui.get("config_missing", UI_TEXTS_EN["config_missing"]))
        return
    
    ui = load_ui_texts()
    
    # If language not provided, ask interactively
    if not new_lang:
        try:
            # Display current language using localized text
            current_lang_text = ui.get("current_language", "Current target language: {}")
            if "{}" in current_lang_text:
                print(current_lang_text.format(config['target_language']))
            else:
                print(f"{current_lang_text} {config['target_language']}")
            
            # Prompt for new language using localized text
            new_lang = input(ui.get("enter_new_language", "Enter new target language: ")).strip()
        except KeyboardInterrupt:
            print("\n\nLanguage change cancelled.")
            sys.exit(0)
    
    if new_lang:
        old_lang = config['target_language']
        config['target_language'] = new_lang
        save_config(config)
        
        if new_lang.lower() != "english":
            translating_text = ui.get('translating_ui', 'Translating UI texts to')
            print(f"\n{translating_text} {new_lang}...")
            translated_texts = translate_ui_texts(config)
            if translated_texts:
                save_ui_texts(translated_texts)
                print(ui.get("language_changed", "✓ Language changed and UI texts translated!"))
            else:
                # If translation fails, keep old language
                config['target_language'] = old_lang
                save_config(config)
                print(ui.get("translation_failed", "Failed to translate UI texts. Language not changed."))
        else:
            # Remove custom language file if switching back to English
            if LANG_FILE.exists():
                LANG_FILE.unlink()
            print("✓ Language changed to English!")


def view_config():
    """Display current configuration."""
    config = load_config()
    ui = load_ui_texts()
    
    if not config:
        print(ui.get("config_missing", UI_TEXTS_EN["config_missing"]))
        return
    
    print("=== Current Configuration ===")
    print(f"Base URL: {config['base_url']}")
    print(f"Model: {config['model']}")
    print(f"API Key: {'*' * 8 if config['api_key'] else 'not set'}")
    print(f"Target Language: {config['target_language']}")
    print(f"Streaming: {'Enabled' if config.get('stream', False) else 'Disabled'}")
    print(f"Cache Directory: {CACHE_DIR}")
    print(f"Config File: {CONFIG_FILE}")
    print(f"Language File: {LANG_FILE}")
    print("=" * 30)


def run_command(cmd: str) -> str:
    """Execute shell command and return combined output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        if not output:
            output = f"Command exited with code {result.returncode} (no output)"
        return output
    except Exception as e:
        return f"Error executing command: {e}"


def call_ai_api(text: str, config: Dict, is_json: bool = False, force_no_stream: bool = False) -> Optional[str]:
    """Call OpenAI-compatible API for translation."""
    if not config.get('api_key'):
        print("Error: API key not configured. Please run: transh -c")
        return None
    
    url = f"{config['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    system_content = f"You are a translator. Translate the given text into {config['target_language']}. Only output the translation, no explanations."
    if is_json:
        system_content += " Output valid JSON only."
    
    # Force non-streaming for JSON or when explicitly requested
    use_stream = config.get('stream', True) and not is_json and not force_no_stream
    
    payload = {
        "model": config['model'],
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text}
        ],
        "stream": use_stream
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60, stream=use_stream)
        response.raise_for_status()
        
        if use_stream:
            # Handle streaming response
            full_text = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_text += content
                        except json.JSONDecodeError:
                            continue
            print()  # New line after streaming
            return full_text
        else:
            # Handle non-streaming response
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
            
    except KeyboardInterrupt:
        print("\n\nTranslation interrupted by user.")
        sys.exit(0)
    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Failed to parse API response: {e}")
        return None


def translate_text(text: str, config: Dict, use_cache: bool = True, temp_language: Optional[str] = None) -> Optional[str]:
    """Translate text with caching support."""
    ui = load_ui_texts()
    
    # Use temporary language if provided, otherwise use config language
    target_lang = temp_language if temp_language else config['target_language']
    
    # Create a temporary config with the override language if needed
    effective_config = config.copy()
    if temp_language:
        effective_config['target_language'] = temp_language
    
    # Check cache only if not using temporary language and cache is enabled
    if use_cache and not temp_language:
        cached = load_cache(text, target_lang)
        if cached:
            print(ui.get("cached", "[Using cached translation]"))
            # Print cached translation
            print(cached)
            return cached
    
    # Translate
    print(ui.get("translating", "Translating to {}...").format(target_lang))
    translation = call_ai_api(text, effective_config)
    
    # Save to cache only if not using temporary language
    if translation and not temp_language:
        save_cache(text, translation, target_lang)
    
    return translation


def show_help():
    """Show help message."""
    ui = load_ui_texts()
    print(ui.get("usage", UI_TEXTS_EN["usage"]))
    print()
    print(ui.get("options", UI_TEXTS_EN["options"]))
    print()
    print(ui.get("examples", UI_TEXTS_EN["examples"]))


def main():
    ui = load_ui_texts()
    
    # Parse arguments
    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        show_help()
        sys.exit(0)
    
    # Handle special options
    if "-c" in sys.argv:
        interactive_config()
        sys.exit(0)
    
    if "--vi-env" in sys.argv:
        view_config()
        sys.exit(0)
    
    # Handle -l (change language) - only if it's the ONLY operation
    # Skip if -l is used with -t, -f, or a command (temporary language mode)
    # Check if there's a command (non-option argument that's not after -l)
    has_command = False
    for i, arg in enumerate(sys.argv[1:], 1):
        # Skip the argument after -l
        if i > 1 and sys.argv[i-1] == "-l":
            continue
        # If it's not an option and not right after an option that takes args
        if not arg.startswith("-") and (i == 1 or sys.argv[i-1] not in ["-t", "-f", "-l"]):
            has_command = True
            break
    
    if "-l" in sys.argv and "-t" not in sys.argv and "-f" not in sys.argv and not has_command:
        idx = sys.argv.index("-l")
        # Check if next argument exists and is not another option
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("-"):
            # Direct language change
            change_language(sys.argv[idx + 1])
        else:
            # Interactive language change
            change_language()
        sys.exit(0)
    
    # Load config
    config = load_config()
    if not config:
        print(ui.get("config_missing", UI_TEXTS_EN["config_missing"]))
        sys.exit(1)
    
    use_cache = "-r" not in sys.argv
    
    # Check for temporary language override (-l used with other commands)
    temp_language = None
    for i, arg in enumerate(sys.argv):
        if arg == "-l" and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
            temp_language = sys.argv[i + 1]
            break
    
    # Handle -t (translate text directly)
    if "-t" in sys.argv:
        idx = sys.argv.index("-t")
        if idx + 1 < len(sys.argv):
            text = sys.argv[idx + 1]
            translation = translate_text(text, config, use_cache, temp_language)
            if not translation:
                print(ui.get("translation_failed", "Translation failed."))
                sys.exit(1)
        else:
            print(ui.get("require_text", "Error: -t requires a text argument"))
            sys.exit(1)
        sys.exit(0)
    
    # Handle -f (translate file)
    if "-f" in sys.argv:
        idx = sys.argv.index("-f")
        if idx + 1 < len(sys.argv) and idx + 2 < len(sys.argv):
            output_file = sys.argv[idx + 1]
            input_file = sys.argv[idx + 2]
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                translation = translate_text(text, config, use_cache, temp_language)
                if translation:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(translation)
                    saved_text = ui.get("translation_saved", "✓ Translation saved to {}")
                    if "{}" in saved_text:
                        print(saved_text.format(output_file))
                    else:
                        print(f"{saved_text} {output_file}")
                else:
                    print(ui.get("translation_failed", "Translation failed."))
                    sys.exit(1)
            except FileNotFoundError:
                error_text = ui.get("file_not_found", "Error: File '{}' not found")
                if "{}" in error_text:
                    print(error_text.format(input_file))
                else:
                    print(f"Error: File '{input_file}' not found")
                sys.exit(1)
            except Exception as e:
                error_text = ui.get("error", "Error: {}")
                if "{}" in error_text:
                    print(error_text.format(e))
                else:
                    print(f"Error: {e}")
                sys.exit(1)
        else:
            print(ui.get("require_files", "Error: -f requires input and output file arguments"))
            sys.exit(1)
        sys.exit(0)
    
    # Default: translate command output
    command = sys.argv[-1]
    if command.startswith("-"):
        print(ui.get("no_command", "Error: No command specified"))
        show_help()
        sys.exit(1)
    
    executing_text = ui.get('executing', 'Executing')
    print(f"{executing_text}: {command}")
    output = run_command(command)
    
    output_len_text = ui.get("output_length", "Command output ({} chars)")
    if "{}" in output_len_text:
        print(output_len_text.format(len(output)))
    else:
        print(f"Command output ({len(output)} chars)")
    
    print("---")
    print(output)
    print("---")
    
    if not output.strip():
        print(ui.get("no_output", "No output to translate."))
        sys.exit(0)
    
    translation = translate_text(output, config, use_cache, temp_language)
    if not translation:
        print(ui.get("translation_failed", "Translation failed."))
        sys.exit(1)


if __name__ == "__main__":
    main()
