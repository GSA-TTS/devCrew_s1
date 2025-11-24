"""
Slack Integration Module.

Provides comprehensive Slack integration using the slack-sdk library with
support for Block Kit formatting, file uploads, threading, reactions, and
rich message composition. Designed for production use with proper error
handling, rate limiting, and mock-friendly architecture.

Key Features:
    - Block Kit message composition with helper methods
    - File upload and sharing capabilities
    - Thread management and replies
    - Reaction handling (emoji reactions)
    - User and channel mentions
    - Permalink generation
    - Rate limit handling and retries
    - Comprehensive error handling

Example:
    >>> slack = SlackIntegration(token=os.getenv("SLACK_BOT_TOKEN"))
    >>> blocks = [
    ...     slack.create_header_block("System Alert"),
    ...     slack.create_section_block("Service is experiencing issues"),
    ... ]
    >>> response = slack.send_block_kit_message("#alerts", blocks)
    >>> print(response["ts"])  # Message timestamp

Author: devCrew_s1
Version: 1.0.0
"""

import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure module logger
logger = logging.getLogger(__name__)


class SlackMessageType(str, Enum):
    """Slack message types."""

    PLAIN = "plain"
    MARKDOWN = "mrkdwn"
    BLOCK_KIT = "block_kit"


class SlackBlockType(str, Enum):
    """Slack Block Kit block types."""

    HEADER = "header"
    SECTION = "section"
    DIVIDER = "divider"
    CONTEXT = "context"
    ACTIONS = "actions"
    IMAGE = "image"


class SlackTextType(str, Enum):
    """Slack text formatting types."""

    PLAIN = "plain_text"
    MARKDOWN = "mrkdwn"


class SlackBlock(BaseModel):
    """
    Pydantic model for Slack Block Kit blocks.

    Represents a single block in Slack's Block Kit framework with
    type validation and helper methods for block composition.

    Attributes:
        type: Block type (header, section, divider, etc.)
        text: Text content (for header/section blocks)
        text_type: Text formatting type (plain_text or mrkdwn)
        fields: List of text fields (for section blocks)
        accessory: Accessory element (button, image, etc.)
        elements: List of interactive elements (for actions blocks)
        block_id: Unique identifier for the block
        image_url: URL for image blocks
        alt_text: Alt text for images
    """

    type: SlackBlockType
    text: Optional[str] = None
    text_type: SlackTextType = SlackTextType.PLAIN
    fields: Optional[List[Dict[str, Any]]] = None
    accessory: Optional[Dict[str, Any]] = None
    elements: Optional[List[Dict[str, Any]]] = None
    block_id: Optional[str] = None
    image_url: Optional[str] = None
    alt_text: Optional[str] = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v: Any) -> SlackBlockType:
        """Validate and convert block type."""
        if isinstance(v, str):
            return SlackBlockType(v)
        return v

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to Slack API compatible dictionary.

        Returns:
            Dictionary representation suitable for Slack API
        """
        block: Dict[str, Any] = {"type": self.type.value}

        if self.block_id:
            block["block_id"] = self.block_id

        if self.type == SlackBlockType.HEADER:
            if self.text:
                block["text"] = {
                    "type": "plain_text",
                    "text": self.text,
                    "emoji": True,
                }

        elif self.type == SlackBlockType.SECTION:
            if self.text:
                block["text"] = {
                    "type": self.text_type.value,
                    "text": self.text,
                }
            if self.fields:
                block["fields"] = self.fields
            if self.accessory:
                block["accessory"] = self.accessory

        elif self.type == SlackBlockType.DIVIDER:
            pass  # Divider blocks have no additional fields

        elif self.type == SlackBlockType.CONTEXT:
            if self.elements:
                block["elements"] = self.elements

        elif self.type == SlackBlockType.ACTIONS:
            if self.elements:
                block["elements"] = self.elements

        elif self.type == SlackBlockType.IMAGE:
            if self.image_url and self.alt_text:
                block["image_url"] = self.image_url
                block["alt_text"] = self.alt_text
                if self.text:
                    block["title"] = {
                        "type": "plain_text",
                        "text": self.text,
                        "emoji": True,
                    }

        return block


class SlackMessage(BaseModel):
    """
    Pydantic model for Slack messages.

    Comprehensive message model supporting plain text, markdown, and
    Block Kit formatted messages with threading and metadata.

    Attributes:
        channel: Target channel (ID or name with #)
        text: Plain text message content (fallback for blocks)
        blocks: List of Block Kit blocks
        thread_ts: Parent message timestamp for threading
        username: Bot username override
        icon_emoji: Emoji icon override (e.g., :robot_face:)
        icon_url: URL for custom icon
        attachments: Legacy attachments (for backwards compatibility)
        unfurl_links: Whether to unfurl links
        unfurl_media: Whether to unfurl media
        metadata: Message metadata for event tracking
    """

    channel: str = Field(..., description="Target channel ID or name")
    text: Optional[str] = Field(None, description="Message text (fallback for blocks)")
    blocks: Optional[List[SlackBlock]] = Field(None, description="Block Kit blocks")
    thread_ts: Optional[str] = Field(None, description="Thread parent timestamp")
    username: Optional[str] = Field(None, description="Bot username override")
    icon_emoji: Optional[str] = Field(None, description="Emoji icon")
    icon_url: Optional[str] = Field(None, description="Custom icon URL")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        None, description="Legacy attachments"
    )
    unfurl_links: bool = Field(True, description="Unfurl links")
    unfurl_media: bool = Field(True, description="Unfurl media")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Validate channel format."""
        if not v:
            raise ValueError("Channel cannot be empty")
        return v

    def to_api_params(self) -> Dict[str, Any]:
        """
        Convert message to Slack API parameters.

        Returns:
            Dictionary of parameters for Slack API calls
        """
        params: Dict[str, Any] = {"channel": self.channel}

        if self.text:
            params["text"] = self.text

        if self.blocks:
            params["blocks"] = [block.to_dict() for block in self.blocks]

        if self.thread_ts:
            params["thread_ts"] = self.thread_ts

        if self.username:
            params["username"] = self.username

        if self.icon_emoji:
            params["icon_emoji"] = self.icon_emoji

        if self.icon_url:
            params["icon_url"] = self.icon_url

        if self.attachments:
            params["attachments"] = self.attachments

        params["unfurl_links"] = self.unfurl_links
        params["unfurl_media"] = self.unfurl_media

        if self.metadata:
            params["metadata"] = self.metadata

        return params


class SlackIntegration:
    """
    Main Slack integration client.

    Provides a comprehensive interface to Slack's API with support for
    message posting, Block Kit formatting, file uploads, threading,
    reactions, and more. Handles rate limiting, retries, and errors.

    Attributes:
        client: Slack WebClient instance
        token: Slack OAuth bot token
        default_channel: Default channel for messages
        retry_count: Number of retries for failed requests
        retry_delay: Initial delay between retries (seconds)

    Example:
        >>> slack = SlackIntegration(token=os.getenv("SLACK_BOT_TOKEN"))
        >>> response = slack.post_message("#general", "Hello, World!")
        >>> print(response["ok"])  # True
    """

    def __init__(
        self,
        token: Optional[str] = None,
        default_channel: Optional[str] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Slack integration.

        Args:
            token: Slack OAuth bot token (defaults to SLACK_BOT_TOKEN env var)
            default_channel: Default channel for messages
            retry_count: Number of retries for failed requests
            retry_delay: Initial delay between retries in seconds

        Raises:
            ValueError: If no token is provided or found in environment
        """
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError(
                "Slack token required. Provide token parameter or set "
                "SLACK_BOT_TOKEN environment variable."
            )

        self.client = WebClient(token=self.token)
        self.default_channel = default_channel
        self.retry_count = retry_count
        self.retry_delay = retry_delay

        logger.info("SlackIntegration initialized successfully")

    def _handle_rate_limit(self, error: SlackApiError) -> None:
        """
        Handle rate limit errors with exponential backoff.

        Args:
            error: SlackApiError containing rate limit information

        Raises:
            SlackApiError: If retry_after header is not present
        """
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            wait_time = int(retry_after)
            logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry.")
            time.sleep(wait_time)
        else:
            raise error

    def _execute_with_retry(
        self, func: Any, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute Slack API call with retry logic.

        Args:
            func: Slack API method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Response dictionary from Slack API

        Raises:
            SlackApiError: If all retries fail
        """
        last_error = None
        delay = self.retry_delay

        for attempt in range(self.retry_count):
            try:
                response = func(*args, **kwargs)
                return response.data
            except SlackApiError as e:
                last_error = e
                if e.response["error"] == "rate_limited":
                    self._handle_rate_limit(e)
                    continue

                logger.error(
                    f"Slack API error (attempt {attempt + 1}/"
                    f"{self.retry_count}): {e.response['error']}"
                )

                if attempt < self.retry_count - 1:
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

        raise last_error  # type: ignore

    def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Post a message to a Slack channel.

        Args:
            channel: Channel ID or name (with #)
            text: Message text (used as fallback if blocks provided)
            blocks: Optional Block Kit blocks
            thread_ts: Optional parent message timestamp for threading
            **kwargs: Additional parameters for chat.postMessage

        Returns:
            Response dictionary with 'ok', 'channel', 'ts', etc.

        Example:
            >>> response = slack.post_message(
            ...     "#general",
            ...     "Hello, World!",
            ...     thread_ts="1234567890.123456"
            ... )
        """
        params: Dict[str, Any] = {
            "channel": channel,
            "text": text,
        }

        if blocks:
            params["blocks"] = blocks

        if thread_ts:
            params["thread_ts"] = thread_ts

        params.update(kwargs)

        logger.info(f"Posting message to channel: {channel}")
        return self._execute_with_retry(self.client.chat_postMessage, **params)

    def send_block_kit_message(
        self,
        channel: str,
        blocks: List[Dict[str, Any]],
        text: Optional[str] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Send a Block Kit formatted message.

        Args:
            channel: Channel ID or name
            blocks: List of Block Kit block dictionaries
            text: Fallback text for notifications
            thread_ts: Optional thread parent timestamp
            **kwargs: Additional parameters

        Returns:
            Response dictionary from Slack API

        Example:
            >>> blocks = [
            ...     slack.create_header_block("Alert"),
            ...     slack.create_section_block("System error detected"),
            ... ]
            >>> response = slack.send_block_kit_message("#alerts", blocks)
        """
        fallback = text or "New message (open in Slack to view)"
        return self.post_message(
            channel=channel,
            text=fallback,
            blocks=blocks,
            thread_ts=thread_ts,
            **kwargs,
        )

    def upload_file(
        self,
        channel: str,
        file_path: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to a Slack channel.

        Args:
            channel: Channel ID or name
            file_path: Path to file to upload
            title: File title in Slack
            initial_comment: Optional comment to post with file
            thread_ts: Optional thread parent timestamp

        Returns:
            Response dictionary from Slack API

        Raises:
            FileNotFoundError: If file does not exist
            SlackApiError: If upload fails

        Example:
            >>> response = slack.upload_file(
            ...     "#general",
            ...     "/tmp/report.pdf",
            ...     title="Monthly Report",
            ...     initial_comment="Here's the report!"
            ... )
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        params = {
            "channels": channel,
            "file": str(path),
        }

        if title:
            params["title"] = title
        else:
            params["title"] = path.name

        if initial_comment:
            params["initial_comment"] = initial_comment

        if thread_ts:
            params["thread_ts"] = thread_ts

        logger.info(f"Uploading file to channel: {channel}")
        return self._execute_with_retry(self.client.files_upload, **params)

    def create_thread(
        self, channel: str, parent_ts: str, text: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a threaded reply to a message.

        Args:
            channel: Channel ID or name
            parent_ts: Parent message timestamp
            text: Reply text
            **kwargs: Additional parameters

        Returns:
            Response dictionary from Slack API

        Example:
            >>> original = slack.post_message("#general", "Thread starter")
            >>> reply = slack.create_thread(
            ...     "#general",
            ...     original["ts"],
            ...     "This is a reply"
            ... )
        """
        return self.post_message(
            channel=channel, text=text, thread_ts=parent_ts, **kwargs
        )

    def add_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """
        Add an emoji reaction to a message.

        Args:
            channel: Channel ID or name
            timestamp: Message timestamp
            emoji: Emoji name (without colons, e.g., 'thumbsup')

        Returns:
            True if reaction was added successfully

        Example:
            >>> msg = slack.post_message("#general", "Great work!")
            >>> slack.add_reaction("#general", msg["ts"], "tada")
        """
        # Remove colons if present
        emoji = emoji.strip(":")

        try:
            self._execute_with_retry(
                self.client.reactions_add,
                channel=channel,
                timestamp=timestamp,
                name=emoji,
            )
            logger.info(f"Added reaction '{emoji}' to message {timestamp}")
            return True
        except SlackApiError as e:
            if e.response["error"] == "already_reacted":
                logger.info(f"Reaction '{emoji}' already exists")
                return True
            logger.error(f"Failed to add reaction: {e.response['error']}")
            return False

    def remove_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """
        Remove an emoji reaction from a message.

        Args:
            channel: Channel ID or name
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            True if reaction was removed successfully
        """
        emoji = emoji.strip(":")

        try:
            self._execute_with_retry(
                self.client.reactions_remove,
                channel=channel,
                timestamp=timestamp,
                name=emoji,
            )
            logger.info(f"Removed reaction '{emoji}' from {timestamp}")
            return True
        except SlackApiError as e:
            logger.error(f"Failed to remove reaction: {e.response['error']}")
            return False

    def update_message(
        self,
        channel: str,
        timestamp: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Update an existing message.

        Args:
            channel: Channel ID or name
            timestamp: Message timestamp to update
            text: Updated text
            blocks: Updated Block Kit blocks
            **kwargs: Additional parameters

        Returns:
            Response dictionary from Slack API

        Example:
            >>> msg = slack.post_message("#general", "Original text")
            >>> slack.update_message(
            ...     "#general",
            ...     msg["ts"],
            ...     text="Updated text"
            ... )
        """
        params: Dict[str, Any] = {
            "channel": channel,
            "ts": timestamp,
        }

        if text:
            params["text"] = text

        if blocks:
            params["blocks"] = blocks

        params.update(kwargs)

        logger.info(f"Updating message {timestamp} in channel: {channel}")
        return self._execute_with_retry(self.client.chat_update, **params)

    def delete_message(self, channel: str, timestamp: str) -> Dict[str, Any]:
        """
        Delete a message.

        Args:
            channel: Channel ID or name
            timestamp: Message timestamp to delete

        Returns:
            Response dictionary from Slack API

        Example:
            >>> msg = slack.post_message("#general", "Oops!")
            >>> slack.delete_message("#general", msg["ts"])
        """
        logger.info(f"Deleting message {timestamp} from channel: {channel}")
        return self._execute_with_retry(
            self.client.chat_delete, channel=channel, ts=timestamp
        )

    def get_permalink(self, channel: str, timestamp: str) -> str:
        """
        Get a permanent link to a message.

        Args:
            channel: Channel ID or name
            timestamp: Message timestamp

        Returns:
            Permanent URL to the message

        Example:
            >>> msg = slack.post_message("#general", "Important!")
            >>> url = slack.get_permalink("#general", msg["ts"])
            >>> print(url)
        """
        response = self._execute_with_retry(
            self.client.chat_getPermalink,
            channel=channel,
            message_ts=timestamp,
        )
        return response.get("permalink", "")

    @staticmethod
    def mention_user(user_id: str) -> str:
        """
        Format a user mention.

        Args:
            user_id: Slack user ID (e.g., U1234567890)

        Returns:
            Formatted mention string (e.g., <@U1234567890>)

        Example:
            >>> mention = slack.mention_user("U1234567890")
            >>> slack.post_message("#general", f"{mention} please review")
        """
        return f"<@{user_id}>"

    @staticmethod
    def mention_channel() -> str:
        """
        Format a @channel mention.

        Returns:
            Formatted @channel mention string

        Example:
            >>> msg = f"{slack.mention_channel()} System is down!"
            >>> slack.post_message("#alerts", msg)
        """
        return "<!channel>"

    @staticmethod
    def mention_here() -> str:
        """
        Format a @here mention.

        Returns:
            Formatted @here mention string
        """
        return "<!here>"

    @staticmethod
    def create_header_block(
        text: str, block_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a header block.

        Args:
            text: Header text (plain text, max 150 chars)
            block_id: Optional unique block identifier

        Returns:
            Header block dictionary

        Example:
            >>> block = slack.create_header_block("System Alert")
        """
        block: Dict[str, Any] = {
            "type": "header",
            "text": {"type": "plain_text", "text": text[:150], "emoji": True},
        }
        if block_id:
            block["block_id"] = block_id
        return block

    @staticmethod
    def create_section_block(
        text: str,
        markdown: bool = True,
        fields: Optional[List[str]] = None,
        accessory: Optional[Dict[str, Any]] = None,
        block_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a section block.

        Args:
            text: Section text
            markdown: Use markdown formatting (default True)
            fields: Optional list of field texts
            accessory: Optional accessory element (button, image, etc.)
            block_id: Optional unique block identifier

        Returns:
            Section block dictionary

        Example:
            >>> block = slack.create_section_block(
            ...     "*Error detected*: Service unavailable",
            ...     markdown=True
            ... )
        """
        text_type = "mrkdwn" if markdown else "plain_text"
        block: Dict[str, Any] = {
            "type": "section",
            "text": {"type": text_type, "text": text},
        }

        if fields:
            block["fields"] = [{"type": text_type, "text": field} for field in fields]

        if accessory:
            block["accessory"] = accessory

        if block_id:
            block["block_id"] = block_id

        return block

    @staticmethod
    def create_divider_block() -> Dict[str, Any]:
        """
        Create a divider block.

        Returns:
            Divider block dictionary

        Example:
            >>> blocks = [
            ...     slack.create_section_block("Part 1"),
            ...     slack.create_divider_block(),
            ...     slack.create_section_block("Part 2"),
            ... ]
        """
        return {"type": "divider"}

    @staticmethod
    def create_context_block(
        elements: List[str], block_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a context block.

        Args:
            elements: List of text elements
            block_id: Optional unique block identifier

        Returns:
            Context block dictionary

        Example:
            >>> block = slack.create_context_block([
            ...     "Last updated: 2024-01-15",
            ...     "Version: 1.0.0"
            ... ])
        """
        block: Dict[str, Any] = {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": element} for element in elements],
        }
        if block_id:
            block["block_id"] = block_id
        return block

    @staticmethod
    def create_actions_block(
        elements: List[Dict[str, Any]], block_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an actions block with interactive elements.

        Args:
            elements: List of interactive elements (buttons, etc.)
            block_id: Optional unique block identifier

        Returns:
            Actions block dictionary

        Example:
            >>> button = slack.create_button("approve", "Approve", "primary")
            >>> block = slack.create_actions_block([button])
        """
        block: Dict[str, Any] = {"type": "actions", "elements": elements}
        if block_id:
            block["block_id"] = block_id
        return block

    @staticmethod
    def create_button(
        action_id: str,
        text: str,
        style: Optional[str] = None,
        value: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a button element.

        Args:
            action_id: Unique action identifier
            text: Button text
            style: Button style (primary, danger)
            value: Value sent when clicked
            url: URL to open when clicked

        Returns:
            Button element dictionary

        Example:
            >>> approve = slack.create_button(
            ...     "approve_request",
            ...     "Approve",
            ...     style="primary",
            ...     value="approved"
            ... )
        """
        button: Dict[str, Any] = {
            "type": "button",
            "action_id": action_id,
            "text": {"type": "plain_text", "text": text, "emoji": True},
        }

        if style:
            button["style"] = style

        if value:
            button["value"] = value

        if url:
            button["url"] = url

        return button

    @staticmethod
    def create_image_block(
        image_url: str,
        alt_text: str,
        title: Optional[str] = None,
        block_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an image block.

        Args:
            image_url: URL of the image
            alt_text: Alternative text for the image
            title: Optional image title
            block_id: Optional unique block identifier

        Returns:
            Image block dictionary

        Example:
            >>> block = slack.create_image_block(
            ...     "https://example.com/chart.png",
            ...     "Performance chart",
            ...     title="System Performance"
            ... )
        """
        block: Dict[str, Any] = {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text,
        }

        if title:
            block["title"] = {
                "type": "plain_text",
                "text": title,
                "emoji": True,
            }

        if block_id:
            block["block_id"] = block_id

        return block

    def create_rich_message(
        self,
        channel: str,
        title: str,
        message: str,
        level: str = "info",
        fields: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create and send a rich formatted message with standard layout.

        Args:
            channel: Channel ID or name
            title: Message title
            message: Main message text
            level: Severity level (info, warning, error, success)
            fields: Optional key-value pairs for additional info
            timestamp: Optional timestamp for the message

        Returns:
            Response dictionary from Slack API

        Example:
            >>> response = slack.create_rich_message(
            ...     "#alerts",
            ...     "Deployment Complete",
            ...     "Application v1.2.3 deployed successfully",
            ...     level="success",
            ...     fields={"Version": "1.2.3", "Environment": "production"}
            ... )
        """
        # Map level to emoji
        level_emojis = {
            "info": ":information_source:",
            "warning": ":warning:",
            "error": ":x:",
            "success": ":white_check_mark:",
        }
        emoji = level_emojis.get(level.lower(), ":speech_balloon:")

        blocks = [
            self.create_header_block(f"{emoji} {title}"),
            self.create_section_block(message),
        ]

        if fields:
            field_texts = [f"*{key}*: {value}" for key, value in fields.items()]
            blocks.append(self.create_section_block("", fields=field_texts))

        blocks.append(self.create_divider_block())

        # Add timestamp context
        ts = timestamp or datetime.now()
        blocks.append(
            self.create_context_block([f"Sent at {ts.strftime('%Y-%m-%d %H:%M:%S')}"])
        )

        return self.send_block_kit_message(channel, blocks, text=title)

    def send_message_from_model(self, message: SlackMessage) -> Dict[str, Any]:
        """
        Send a message using a SlackMessage model.

        Args:
            message: SlackMessage model instance

        Returns:
            Response dictionary from Slack API

        Example:
            >>> msg = SlackMessage(
            ...     channel="#general",
            ...     text="Hello",
            ...     blocks=[slack.create_section_block("World")]
            ... )
            >>> response = slack.send_message_from_model(msg)
        """
        params = message.to_api_params()
        return self._execute_with_retry(self.client.chat_postMessage, **params)


# Convenience function for quick message sending
def send_slack_message(
    channel: str,
    text: str,
    token: Optional[str] = None,
    blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Send a quick Slack message.

    Args:
        channel: Channel ID or name
        text: Message text
        token: Slack bot token (defaults to SLACK_BOT_TOKEN env var)
        blocks: Optional Block Kit blocks

    Returns:
        Response dictionary from Slack API

    Example:
        >>> response = send_slack_message(
        ...     "#general",
        ...     "Quick message!",
        ...     token=os.getenv("SLACK_BOT_TOKEN")
        ... )
    """
    slack = SlackIntegration(token=token)
    return slack.post_message(channel=channel, text=text, blocks=blocks)
