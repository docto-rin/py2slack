# py2slack/notify.py

import os
import sys
import traceback
from typing import Optional
from .auth import CLIENT, DEFAULT_CHANNEL, slack_sdk_imported, SlackApiError

def send_slack(text: str = "", file: Optional[str] = None, channel: Optional[str] = None) -> None:
    """
    Send a message or file to Slack.
    
    Parameters:
        text (str): The text message to send.
        file (Optional[str]): Path to the file to upload.
        channel (Optional[str]): Slack channel ID to send the message to.
    """
    if not slack_sdk_imported:
        print("Slack functionality is disabled due to missing slack_sdk library.")
        return

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

def slack_notify(func):
    """
    Decorator that sends a Slack notification upon completion or error of the decorated function.
    """
    def wrapper(*args, **kwargs):
        script_name = os.path.basename(sys.argv[0])
        try:
            result = func(*args, **kwargs)
            send_slack(f"[{script_name}] Process completed successfully!")
            return result
        except Exception as e:
            error_message = (
                f"[{script_name}] An error occurred:\n{str(e)}\n\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            print(error_message)
            send_slack(error_message)
            raise e
    return wrapper
