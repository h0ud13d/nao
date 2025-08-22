# -*- coding: future_fstrings -*-
# nao_zmq.py
import zmq
import threading
import json
import time

class NAOChatSystem:
    def __init__(self, is_robot=True, server_ip="localhost", push_port=5555, sub_port=5556):
        self.context = zmq.Context()
        
        if is_robot:
            # Robot sends messages on PUSH socket
            self.sender = self.context.socket(zmq.PUSH)
            self.sender.connect("tcp://{}:{}".format(server_ip, push_port))
            
            # Robot receives responses on SUB socket
            self.receiver = self.context.socket(zmq.SUB)
            self.receiver.connect("tcp://{}:{}".format(server_ip, sub_port))
            # Fixed: Use unicode string for subscription
            self.receiver.setsockopt(zmq.SUBSCRIBE, u"".encode('utf-8'))
            
            # Start listening thread for responses
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
        else:
            # Server binds to PULL socket to receive messages
            self.receiver = self.context.socket(zmq.PULL)
            self.receiver.bind("tcp://*:{}".format(push_port))
            
            # Server binds to PUB socket to send responses
            self.sender = self.context.socket(zmq.PUB)
            self.sender.bind("tcp://*:{}".format(sub_port))
    
    def send_message(self, message):
        """Send a message"""
        try:
            self.sender.send_json({
                'text': message,
                'timestamp': time.time()
            })
            return True
        except Exception as e:
            print("Error sending message: {}".format(e))
            return False
    
    def _receive_messages(self):
        """Continuously receive messages (for robot)"""
        while self.running:
            try:
                message = self.receiver.recv_json()
                if 'text' in message:
                    # Call the registered callback if it exists
                    if hasattr(self, 'on_message_received'):
                        self.on_message_received(message['text'])
            except Exception as e:
                if self.running:
                    print("Error receiving message: {}".format(e))
    
    def register_callback(self, callback):
        """Register a callback for received messages"""
        self.on_message_received = callback
    
    def close(self):
        """Clean up the communication system"""
        self.running = False
        if hasattr(self, 'sender'):
            self.sender.close()
        if hasattr(self, 'receiver'):
            self.receiver.close()
        self.context.term()

def run_server():
    chat_system = NAOChatSystem(is_robot=False)
    print("Server started. Waiting for messages...")
    
    try:
        while True:
            try:
                # Receive message from robot
                message = chat_system.receiver.recv_json()
                print("Received from robot: {}".format(message['text']))
                
                # Process the message (you can add your custom logic here)
                response = "Server received: {}".format(message['text'])
                
                # Send response back to robot
                chat_system.send_message(response)
                print("Sent response: {}".format(response))
                
            except Exception as e:
                print("Error processing message: {}".format(e))
                
    except KeyboardInterrupt:
        print("Server shutting down...")
        chat_system.close()

if __name__ == "__main__":
    run_server()
