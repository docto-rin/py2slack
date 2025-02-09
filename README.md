# py2slack

**py2slack** provides utility functions to send notifications to Slack using the [slack_sdk](https://pypi.org/project/slack-sdk/) library.

## Installation

Install the package via pip:

```bash
pip install py2slack
```

## Configuration

Before using the package, you must provide your Slack credentials and default channel information. To do so, prepare **one** of the following configuration files in your project root (and add them to your `.gitignore` to protect sensitive data):

### Option 1: Using a `.env` file

Create a file named `.env` with the following contents:

```dotenv
SLACK_OAUTH_TOKEN=<Your OAuth token>
SLACK_DEFAULT_CHANNEL=<Slack default channel ID (not the name)>
```

*Note: The `.env` file requires the [python-dotenv](https://pypi.org/project/python-dotenv/) library. Install it via `pip install python-dotenv` if you choose this option.*

### Option 2: Using a `slack_config.json` file

Alternatively, create a file named `slack_config.json` with the following JSON content:

```json
{
    "oauth_token": "<Your OAuth token>",
    "default_channel": "<Slack default channel ID (not the name)>"
}
```

## OAuth Token Setup

To use py2slack, you need to create a Slack App Bot and obtain an OAuth token. Refer to [this guide](https://qiita.com/kobayashi_ryo/items/a194e620b49edad27364) for instructions.  
Your Bot must have at least the following token scopes:
- **chat:write** – to send messages as your bot.
- **files:write** – to upload, edit, and delete files as your bot.
- **groups:read** – to view basic information about private channels your bot is added to.

After creating your Bot, make sure to invite it to the Slack channel where you want to send notifications.

## Usage

After installing the package and preparing your configuration file, you can send messages as follows:

```python
from py2slack import send_slack

# Send a simple text notification
send_slack("Hello, Slack!")
```

You can also pass a file or specify a channel by using the additional parameters of the `send_slack` function. Refer to the function’s documentation for further details.

## Requirements

- **slack_sdk**: Install with `pip install slack_sdk`
- **python-dotenv**: Required only if you are using a `.env` file for configuration (`pip install python-dotenv`)

## Notes

- **Configuration**: Prepare **either** the `.env` file or the `slack_config.json` file—not both.
- **Security**: Ensure that your configuration files (i.e., `.env` and `slack_config.json`) are added to your `.gitignore` to avoid committing sensitive data.
- **Module Import**: The package’s `__init__.py` is set up to allow you to import the `send_slack` function directly:
  - If `__init__.py` contains `from .slack_utils import send_slack`, you can use:
    ```python
    from py2slack import send_slack
    ```
  - This design leverages Python’s module system for cleaner imports.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.