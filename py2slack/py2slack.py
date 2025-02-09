import os
import json
from typing import Dict, Optional, Tuple, Any
from importlib.util import find_spec

# pip install slack_sdk
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    slack_sdk_imported = True
except ImportError:
    print("Warning: slack_sdk library not found. Slack functionality will be disabled.")
    slack_sdk_imported = False
    WebClient = Any

# Either file must be prepared.
ENV_FILE = '.env' # Requires python-dotenv library
CONFIG_FILE = 'slack_config.json' # No additional libraries required

"""
Directory Structure:
    your_project
    │
    ├── .env               ← Add to .gitignore to protect sensitive data
    ├── slack_config.json  ← Add to .gitignore to protect sensitive data
    │
    └── utils
        ├── __init__.py    ← Either leave empty or add: from .py2slack import send_slack
        └── py2slack.py ← This file (containing the Slack utility functions)

Configuration Files (prepare ONE of the following):
    1. .env file:
    SLACK_OAUTH_TOKEN=<Your OAuth token>
    SLACK_DEFAULT_CHANNEL=<Slack default channel ID (not name) for notifications>

    2. slack_config.json (alternative to .env):
    {
        "oauth_token": "<Your OAuth token>",
        "default_channel": "<Slack default channel ID (not name) for notifications>"
    }

OAuth Token Setup:
    Please create an App Bot by referring to https://qiita.com/kobayashi_ryo/items/a194e620b49edad27364

    Required Bot Token Scopes:
    - chat:write  : Send messages as @YourBot
    - files:write : Upload, edit, and delete files as @YourBot
    - groups:read : View basic information about private channels @YourBot is added to

    These scopes define the app's permissions in Slack.
    Then, invite the created app bot to the Slack channel where notifications will be sent.

Required Libraries:
    1. slack_sdk: Install using 'pip install slack_sdk'
    2. python-dotenv: Install using 'pip install python-dotenv' (only if using .env file)

Notes:
    1. Prepare EITHER slack_config.json OR .env file, not both.
    2. Add both slack_config.json and .env to .gitignore to prevent committing sensitive data.
    3. Remember to invite the created app bot to the Slack channel where notifications will be sent.
    4. The content of __init__.py affects how to import the send_slack function:

        a. If __init__.py is empty:
            Use: from utils.py2slack import send_slack

        b. If __init__.py contains "from .py2slack import send_slack":
            Use: from utils import send_slack

    This difference stems from Python's module system. Explicit importing in __init__.py
    allows direct import of the function from the utils package.
"""

def load_env_vars() -> Dict[str, str]:
    config = {}
    try:
        dotenv_spec = find_spec('dotenv')
        if dotenv_spec is not None:
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE)
        else:
            print("Warning: python-dotenv library not found. Unable to load .env file.")
            print("To use .env file, please install python-dotenv: pip install python-dotenv")
            return config
        
        oauth_token = os.getenv('SLACK_OAUTH_TOKEN')
        default_channel = os.getenv('SLACK_DEFAULT_CHANNEL')

        if oauth_token:
            config['oauth_token'] = oauth_token
        if default_channel:
            config['default_channel'] = default_channel

        missing = []
        if 'oauth_token' not in config:
            missing.append('SLACK_OAUTH_TOKEN')
        if 'default_channel' not in config:
            missing.append('SLACK_DEFAULT_CHANNEL')

        if missing:
            print(f"Warning: The following variables are missing in the '{ENV_FILE}' file: {', '.join(missing)}")
        
        return config
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        return config

def load_slack_config() -> Dict[str, str]:
    config = {}
    
    # First, try to load from .env file
    if os.path.exists(ENV_FILE):
        config = load_env_vars()
    
    # If any config is missing, try to load from JSON file
    if len(config) < 2:
        missing = set(['oauth_token', 'default_channel']) - set(config.keys())
        if os.path.exists(ENV_FILE):
            print(f"Attempting to load missing configuration ({', '.join(missing)}) from '{CONFIG_FILE}'.")
        
        try:
            with open(CONFIG_FILE) as f:
                json_config = json.load(f)
                for key in missing:
                    if key in json_config:
                        config[key] = json_config[key]
        except FileNotFoundError:
            if os.path.exists(ENV_FILE):
                print(f"Warning: '{CONFIG_FILE}' not found.")
            else:
                print(f"Warning: Neither '{ENV_FILE}' nor '{CONFIG_FILE}' found.")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in configuration file '{CONFIG_FILE}'.")
        except Exception as e:
            print(f"Unexpected error while loading config from JSON: {e}")
    
    # Final check for missing configuration
    missing = set(['oauth_token', 'default_channel']) - set(config.keys())
    if missing:
        print(f"Warning: The following configuration is still missing: {', '.join(missing)}")
    
    return config

def initialize_slack_client() -> Tuple[Optional[WebClient], Optional[str]]:
    if not slack_sdk_imported:
        return None, None

    try:
        config = load_slack_config()
        slack_token = config.get('oauth_token')
        default_channel = config.get('default_channel')
        
        if not slack_token:
            print("Warning: Missing 'oauth_token' in configuration. Slack functionality will be disabled.")
            return None, None
        
        try:
            client = WebClient(token=slack_token)
            # Connection Test
            client.auth_test()
            return client, default_channel  # default_channel can be None
        except SlackApiError as e:
            print(f"Error initializing Slack client: {e.response['error']}")
            return None, None
    except Exception as e:
        print(f"Unexpected error initializing Slack client: {e}")
        return None, None
    
client, DEFAULT_CHANNEL = initialize_slack_client()

def send_slack(text: str = "", file: Optional[str] = None, channel: Optional[str] = None) -> None:
    if not slack_sdk_imported:
        print("Slack functionality is disabled due to missing slack_sdk library.")
        return

    if client is None:
        print("Slack functionality is disabled due to missing configuration.")
        return

    if channel is None and DEFAULT_CHANNEL is None:
        print("Error: No channel specified. Please provide a channel or set a default channel in the configuration.")
        return

    used_channel = channel or DEFAULT_CHANNEL

    try:
        if file is None:
            response = client.chat_postMessage(channel=used_channel, text=text)
        else:
            if not os.path.exists(file):
                print(f"Warning: Local file not found: {file}")
                print(f"Current working directory: {os.getcwd()}")
                return
            
            with open(file, "rb") as file_content:
                response = client.files_upload_v2(
                    channel=used_channel,
                    file=file_content,
                    filename=os.path.basename(file),
                    title=os.path.basename(file),
                    initial_comment=text
                )
        
        # print(f"Message sent successfully to channel: {used_channel}")
        print(f"Message sent successfully")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
    except Exception as e:
        print(f"Unexpected error while sending message: {e}")

# Usage example
if __name__ == "__main__":
    send_slack("Hello, Slack!")
    # send_slack("Here's an image", "path/to/image.png")
    # send_slack(file="path/to/image.png")
    # send_slack("Hello, specific channel!", channel="C1234567890")
    # send_slack(file="path/to/image.png", channel="C1234567890")

    # # Error handling and traceback sending example (for use in main.py)
    # import traceback
    # import sys
    # from utils import send_slack

    # def main():
    #     try:
    #         # Your main code here...
    #         send_slack("Process completed successfully!")
    #     except Exception as e:
    #         error_message = f"An error occurred:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
    #         print(error_message)
    #         send_slack(error_message)
    #         sys.exit(1)
    # main()