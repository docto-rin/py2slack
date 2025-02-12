# py2slack/notify.py

import os
import sys
import time
import traceback
from functools import wraps
from typing import Optional, Callable, TypeVar
from slack_sdk.errors import SlackApiError
from .auth import CLIENT, DEFAULT_CHANNEL

F = TypeVar("F", bound=Callable[..., object])

def send_slack(text: str = "", file: Optional[str] = None, channel: Optional[str] = None) -> None:
    """
    Send a message or file to Slack.

    Parameters:
        text (str): The text message to send.
        file (Optional[str]): Path to the file to upload.
        channel (Optional[str]): Slack channel ID to send the message to.
    """
    if CLIENT is None:
        print("Slack functionality is disabled due to missing configuration.")
        return

    if channel is None and DEFAULT_CHANNEL is None:
        print("Error: No channel specified. Please provide a channel or set a default channel in the configuration.")
        return

    used_channel = channel or DEFAULT_CHANNEL

    try:
        if file is None:
            response = CLIENT.chat_postMessage(channel=used_channel, text=text)
        else:
            if not os.path.exists(file):
                print(f"Warning: Local file not found: {file}")
                print(f"Current working directory: {os.getcwd()}")
                return
            
            with open(file, "rb") as file_content:
                response = CLIENT.files_upload_v2(
                    channel=used_channel,
                    file=file_content,
                    filename=os.path.basename(file),
                    title=os.path.basename(file),
                    initial_comment=text
                )
        print("Message sent successfully")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
    except Exception as e:
        print(f"Unexpected error while sending message: {e}")

def format_duration(elapsed: float) -> str:
    """
    Format a duration (in seconds) into a human-readable string.
    
    Parameters:
        elapsed (float): Elapsed time in seconds.
    
    Returns:
        str: A formatted duration string.
    """
    days = int(elapsed // 86400)
    elapsed %= 86400
    hours = int(elapsed // 3600)
    elapsed %= 3600
    minutes = int(elapsed // 60)
    seconds = elapsed % 60

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds:.2f} second{'s' if seconds != 1 else ''}")
    
    return ', '.join(parts)

def slack_notify(func: F) -> F:
    """
    Decorator that sends a Slack notification upon completion or error of the decorated function.
    The notification includes the original function name and a human-friendly formatted execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        script_name = os.path.basename(sys.argv[0]) if sys.argv else "unknown"
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            duration_str = format_duration(elapsed)
            send_slack(f"[{script_name}] Function '{func.__name__}' completed successfully in {duration_str}!")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            duration_str = format_duration(elapsed)
            error_message = (
                f"[{script_name}] Function '{func.__name__}' encountered an error after {duration_str}:\n{str(e)}\n\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            print(error_message)
            send_slack(error_message)
            raise
    return wrapper
