# py2slack/auth.py

import os
import json
import traceback
from typing import Dict, Optional, Tuple, Any
from importlib.util import find_spec

# Import Slack SDK
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    slack_sdk_imported = True
except ImportError:
    print("Warning: slack_sdk library not found. Slack functionality will be disabled.")
    slack_sdk_imported = False
    WebClient = Any
    SlackApiError = Any

# Define paths for configuration files
ENV_FILE = '.env'  # Requires python-dotenv library if using .env
CONFIG_FILE = 'slack_config.json'  # JSON configuration file

def load_from_dotenv_file() -> Dict[str, str]:
    """Load configuration from a .env file."""
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
    """Load Slack configuration from environment variables, .env file, or JSON file."""
    config = {}

    # Step 1: Load from environment variables
    oauth_token = os.getenv('SLACK_OAUTH_TOKEN')
    default_channel = os.getenv('SLACK_DEFAULT_CHANNEL')
    if oauth_token:
        config['oauth_token'] = oauth_token
    if default_channel:
        config['default_channel'] = default_channel

    # Step 2: Load from .env file if any configuration is missing
    missing = {'oauth_token', 'default_channel'} - config.keys()
    if missing or os.path.exists(ENV_FILE):
        env_config = load_from_dotenv_file()
        for key in missing:
            if key in env_config:
                config[key] = env_config[key]

    # Step 3: Load from JSON file if still missing configuration
    missing = {'oauth_token', 'default_channel'} - config.keys()
    if missing or os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                json_config = json.load(f)
                for key in missing:
                    if key in json_config:
                        config[key] = json_config[key]
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in configuration file '{CONFIG_FILE}'.")
        except Exception as e:
            print(f"Unexpected error while loading config from JSON: {e}")

    # Final check for any missing configuration values
    missing = {'oauth_token', 'default_channel'} - config.keys()
    if missing:
        print(f"Warning: The following configuration is still missing: {', '.join(missing)}")
        if not os.path.exists(ENV_FILE) and not os.path.exists(CONFIG_FILE):
            print(f"Warning: Both '{ENV_FILE}' and '{CONFIG_FILE}' are missing.")
        elif not os.path.exists(ENV_FILE):
            print(f"Warning: '{ENV_FILE}' is missing.")
        elif not os.path.exists(CONFIG_FILE):
            print(f"Warning: '{CONFIG_FILE}' is missing.")
        else:
            print(f"Warning: Both '{ENV_FILE}' and '{CONFIG_FILE}' are present, but still missing configuration.")

    return config

def initialize_slack_client() -> Tuple[Optional[WebClient], Optional[str]]:
    """Initialize the Slack client using the loaded configuration."""
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
            # Test the connection
            client.auth_test()
            return client, default_channel  # default_channel can be None
        except Exception as e:
            print(f"Error initializing Slack client: {e}")
            return None, None
    except Exception as e:
        print(f"Unexpected error initializing Slack client: {e}")
        return None, None

# Initialize the Slack client as constants
CLIENT, DEFAULT_CHANNEL = initialize_slack_client()
