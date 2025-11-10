from abc import abstractmethod
import math

# Interface to prevent importing Node2D (circular import)
class MessageNode():
    @property
    @abstractmethod
    def id(self) -> int:
        """
        Node id.
        """
        ...

    @property
    @abstractmethod
    def pos(self) -> tuple:
        """
        Node position.
        """
        ...

class Messages:
    # (destination_id, message) -> (sending_time, sender)
    _messages: dict[tuple[int, bytes], tuple[float, MessageNode | None]] = dict()
    _broadcasts: set[bytes] = set()
    _sent_count: int = 0
    _received_count: int = 0
    _total_delay: float = 0
    _total_speed: float = 0

    @staticmethod
    def register_message(node: MessageNode | None, dest: int, data: bytes, time: float) -> None:
        # Make sure the sending node is valid
        if not node:
            print("Invalid sending node")
            return
        
        # Broadcast messages are ignored, because they can have more than one receiver
        if dest < 0:
            Messages._broadcasts.add(data)
            print("Broadcast message ignored in statistics")
            return
        
        # Store the message for later verification
        Messages._messages[(dest, data)] = (time, node)
        Messages._sent_count += 1
    
    @staticmethod
    def verify_message(node: MessageNode | None, data: bytes, time: float) -> tuple[float, float]:
        # Statistics are not implemented for broadcasts
        if data in Messages._broadcasts:
            return (0, 0)

        # Mark as received
        Messages._received_count += 1

        # Make sure the receving node is valid
        if not node:
            print("Invalid receving node")
            return (0, 0)

        # Try to find the sender and time the message was posted
        (start_time, sender) = Messages._messages.pop((node.id, data), (-1, None))
        if sender == None:
            # Either received message was not posted, or the exact same message was posted twice
            print("Cannot determine message origin")
            return (0, 0)
        
        # Calculate end to end distance
        dist: float = math.dist(sender.pos, node.pos)
        
        # Calculate end to end message delay
        delay: float = time - start_time
        Messages._total_delay += delay

        # Calculate end to end message speed
        Messages._total_speed += dist / delay

        return (delay, dist)
    
    @staticmethod
    def get_success_rate() -> float:
        if Messages._sent_count == 0:
            return 0
        return 100 * Messages._received_count / Messages._sent_count
    
    @staticmethod
    def get_avg_delay() -> float:
        if Messages._received_count == 0:
            return 0
        return Messages._total_delay / Messages._received_count
    
    @staticmethod
    def get_avg_speed() -> float:
        if Messages._received_count == 0:
            return 0
        return Messages._total_speed / Messages._received_count