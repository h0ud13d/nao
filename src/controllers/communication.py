# -*- coding: future_fstrings -*-
# controllers/communication.py
import zmq
import threading
import json
import time
from config import ZMQ_SERVER_IP, ZMQ_PUSH_PORT, ZMQ_SUB_PORT

class NAOChatSystem:
    """ZMQ-based communication system for NAO robot."""
    
    def __init__(self, is_robot=True, server_ip=ZMQ_SERVER_IP, push_port=ZMQ_PUSH_PORT, sub_port=ZMQ_SUB_PORT):
        """Initialize the chat system.
        
        Args:
            is_robot: Boolean, True if this is running on the robot, False for server
            server_ip: IP address of the chat server
            push_port: Port for sending messages
            sub_port: Port for receiving messages
        """
        self.context = zmq.Context()
        self.on_message_received = None
        
        if is_robot:
            # Robot sends messages on PUSH socket
            self.sender = self.context.socket(zmq.PUSH)
            self.sender.connect(f"tcp://{server_ip}:{push_port}")
            
            # Robot receives responses on SUB socket
            self.receiver = self.context.socket(zmq.SUB)
            self.receiver.connect(f"tcp://{server_ip}:{sub_port}")
            # Subscribe to all messages
            self.receiver.setsockopt(zmq.SUBSCRIBE, u"".encode('utf-8'))
            
            # Start listening thread for responses
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
        else:
            # Server binds to PULL socket to receive messages
            self.receiver = self.context.socket(zmq.PULL)
            self.receiver.bind(f"tcp://*:{push_port}")
            
            # Server binds to PUB socket to send responses
            self.sender = self.context.socket(zmq.PUB)
            self.sender.bind(f"tcp://*:{sub_port}")
    
    def send_message(self, message):
        """Send a message.
        
        Args:
            message: String message to send
            
        Returns:
            Boolean indicating success
        """
        try:
            self.sender.send_json({
                'text': message,
                'timestamp': time.time()
            })
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def _receive_messages(self):
        """Continuously receive messages (for robot)."""
        while self.running:
            try:
                message = self.receiver.recv_json()
                if 'text' in message:
                    # Call the registered callback if it exists
                    if self.on_message_received:
                        self.on_message_received(message['text'])
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
    
    def register_callback(self, callback):
        """Register a callback for received messages.
        
        Args:
            callback: Function that takes a single string parameter
        """
        self.on_message_received = callback
    
    def close(self):
        """Clean up the communication system."""
        self.running = False
        if hasattr(self, 'sender'):
            self.sender.close()
        if hasattr(self, 'receiver'):
            self.receiver.close()
        self.context.term()


def run_server():
    """Run the chat server."""
    chat_system = NAOChatSystem(is_robot=False)
    print("Chat server started. Waiting for messages...")
    
    try:
        while True:
            try:
                # Receive message from robot
                message = chat_system.receiver.recv_json()
                print(f"Received from robot: {message['text']}")
                
                # Process the message (you can add your custom logic here)
                response = f"Server received: {message['text']}"
                
                # Send response back to robot
                chat_system.send_message(response)
                print(f"Sent response: {response}")
                
            except Exception as e:
                print(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        print("Server shutting down...")
        chat_system.close()

if __name__ == "__main__":
    run_server()