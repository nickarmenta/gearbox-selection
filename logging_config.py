"""
This module configures a centralized logger for the application.
It uses a custom formatter to add emojis to log messages for visual distinction.
"""
import logging
import sys

class EmojiFormatter(logging.Formatter):
    """
    A custom log formatter that adds emojis to log messages based on the log level.
    This provides a quick visual cue for the type of message being logged.
    """
    # Emojis for different log levels
    LOG_EMOJIS = {
        logging.DEBUG: "🐛",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "🔥",
        logging.CRITICAL: "💥",
        5: "😂" # Custom level for funny stuff
    }

    def format(self, record):
        """
        Formats the log record to include a timestamp and a level-specific emoji.
        If a message is passed with extra={'emoji': True}, it will be logged with a special emoji.
        """
        if record.levelno == 5:
             emoji = self.LOG_EMOJIS.get(5)
        else:
             emoji = self.LOG_EMOJIS.get(record.levelno, "🤔")

        record.msg = f"{emoji} {record.msg}"
        return super().format(record)

def setup_logger():
    """
    Sets up and returns a configured logger instance for the entire application.

    This function ensures that all modules use the same singleton logger instance,
    preventing duplicate log entries and maintaining a single, consistent log output.
    The logger is configured to output to the standard output with the custom
    EmojiFormatter.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Define a custom log level for "funny" messages
    logging.addLevelName(5, "FUNNY")

    logger = logging.getLogger("gearbox_assistant")
    if not logger.handlers:  # Avoid adding handlers multiple times on Streamlit re-runs
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Initialize and export the logger for other modules to use
logger = setup_logger() 