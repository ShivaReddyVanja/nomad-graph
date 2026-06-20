import asyncio
from typing import Dict, Optional, Any

class SessionQueueManager:
    """
    Manages async log queues for active sessions.
    Allows capturing prints/logs from different agent nodes and routing them
    to the correct SSE client streaming connection based on thread_id.
    """
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}

    def register(self, thread_id: str) -> asyncio.Queue:
        """Registers a new queue for a thread_id."""
        queue = asyncio.Queue()
        self.queues[thread_id] = queue
        return queue

    def unregister(self, thread_id: str):
        """Unregisters/deletes the queue for a thread_id."""
        if thread_id in self.queues:
            del self.queues[thread_id]

    def get_queue(self, thread_id: str) -> Optional[asyncio.Queue]:
        """Gets the queue associated with the thread_id."""
        return self.queues.get(thread_id)

    def log(self, thread_id: str, message: str):
        """Prints the message to the console and pushes it to the thread's queue."""
        print(message, flush=True)
        queue = self.get_queue(thread_id)
        if queue:
            try:
                loop = asyncio.get_running_loop()
                # Use call_soon_threadsafe to allow pushing logs from synchronous worker threads safely
                loop.call_soon_threadsafe(queue.put_nowait, message)
            except RuntimeError:
                # If there's no active event loop (e.g. running in simple sync script)
                pass

# Global logger instance
session_logger = SessionQueueManager()

def log_agent(config: Optional[Any], message: str):
    """
    Helper function to be called from inside LangGraph nodes.
    Extracts the thread_id from the LangGraph config object and logs the message.
    """
    thread_id = "default"
    if isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id", "default")
    elif hasattr(config, "configurable"):
        thread_id = config.configurable.get("thread_id", "default")
    session_logger.log(thread_id, message)
