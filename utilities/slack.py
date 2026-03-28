import requests
import json


class SlackNotifier:
    """
    Slack integration for CryptoRobot.

    Supports:
    - Outbound trade/balance notifications via Incoming Webhook
    - Remote command reading via Slack Web API (bot token + channel_id required)

    Remote commands (post in the configured Slack channel):
      !pause   - prevents new positions from being opened on next run
      !resume  - re-enables opening new positions
      !status  - bot will reply with current balance/positions summary
    """

    def __init__(self, webhook_url, bot_token=None, channel_id=None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.channel_id = channel_id

    # ------------------------------------------------------------------
    # Outbound notifications
    # ------------------------------------------------------------------

    def send_message(self, text):
        if not self.webhook_url:
            return False
        response = requests.post(
            self.webhook_url,
            json={"text": text},
            timeout=10,
        )
        return response.status_code == 200

    def send_open_long(self, pair, quantity, price, usd_value):
        text = (
            f":chart_with_upwards_trend: *OPEN LONG* | {pair} | "
            f"{quantity} @ {price}$ (~{round(usd_value, 2)}$)"
        )
        return self.send_message(text)

    def send_close_long(self, pair, quantity, price, usd_value):
        text = (
            f":white_check_mark: *CLOSE LONG* | {pair} | "
            f"{quantity} @ {price}$ (~{round(usd_value, 2)}$)"
        )
        return self.send_message(text)

    def send_open_short(self, pair, quantity, price, usd_value):
        text = (
            f":chart_with_downwards_trend: *OPEN SHORT* | {pair} | "
            f"{quantity} @ {price}$ (~{round(usd_value, 2)}$)"
        )
        return self.send_message(text)

    def send_close_short(self, pair, quantity, price, usd_value):
        text = (
            f":x: *CLOSE SHORT* | {pair} | "
            f"{quantity} @ {price}$ (~{round(usd_value, 2)}$)"
        )
        return self.send_message(text)

    def send_balance_update(self, usd_balance, long_expo=None, short_expo=None, var=None):
        text = f":bank: *Balance* | {round(usd_balance, 2)}$"
        if long_expo is not None and short_expo is not None:
            text += f" | LONG: {round(long_expo * 100, 2)}% | SHORT: {round(short_expo * 100, 2)}%"
        if var is not None:
            text += f" | VaR: -{round(var, 2)}%"
        return self.send_message(text)

    def send_error(self, error_msg):
        text = f":warning: *Error* | {error_msg}"
        return self.send_message(text)

    # ------------------------------------------------------------------
    # Remote control (requires bot_token + channel_id)
    # ------------------------------------------------------------------

    def _get_recent_messages(self, limit=20):
        """Fetch recent messages from the configured Slack channel."""
        if not self.bot_token or not self.channel_id:
            return []
        response = requests.get(
            "https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {self.bot_token}"},
            params={"channel": self.channel_id, "limit": limit},
            timeout=10,
        )
        if response.status_code != 200:
            return []
        data = response.json()
        if not data.get("ok"):
            return []
        return data.get("messages", [])

    def get_remote_commands(self):
        """
        Return a list of remote commands found in recent messages.
        Commands start with '!' (e.g. '!pause', '!resume', '!status').
        Each entry is a list of tokens, e.g. ['pause'] or ['status'].
        Messages are returned newest-first from Slack.
        """
        commands = []
        for msg in self._get_recent_messages():
            text = msg.get("text", "").strip()
            if text.startswith("!"):
                tokens = text[1:].lower().split()
                if tokens:
                    commands.append(tokens)
        return commands

    def is_paused(self):
        """
        Check whether the bot is currently paused based on the most recent
        !pause / !resume command in the channel.
        Returns True if the latest relevant command is !pause.
        """
        for cmd in self.get_remote_commands():  # newest first
            if cmd[0] == "pause":
                return True
            if cmd[0] == "resume":
                return False
        return False

    def post_reply(self, text):
        """Send a reply message to the channel (uses webhook)."""
        return self.send_message(text)
