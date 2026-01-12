"""
Simple MessageTracker for BotCompressor 2.0
"""

class MessageTracker:
    """Simple message tracker to prevent duplicate processing"""
    
    def __init__(self):
        self.processed_messages = set()
        
    def is_processed(self, message_id: int) -> bool:
        """Check if message was already processed"""
        return message_id in self.processed_messages
        
    def mark_as_processed(self, message_id: int):
        """Mark message as processed"""
        self.processed_messages.add(message_id)
        
    def clear_old_messages(self, max_messages: int = 10000):
        """Clear old messages to prevent memory issues"""
        if len(self.processed_messages) > max_messages:
            # Keep only the most recent messages
            self.processed_messages = set(list(self.processed_messages)[-max_messages:])