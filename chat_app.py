import tkinter as tk
from tkinter import scrolledtext
import socket
import threading

# Client GUI Class
class ChatClientGUI:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((host, port))
        except ConnectionRefusedError:
            print("Connection to the server failed. Is the server running?")
            exit()

        # GUI Setup
        self.window = tk.Tk()
        self.window.title("Chat Application")

        self.chat_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state='disabled')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(self.window)
        self.message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.window, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)

        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message.strip():
            self.client.send(message.encode())
            self.message_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, f"{message}\n")
                self.chat_area.config(state='disabled')
                self.chat_area.yview(tk.END)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def on_close(self):
        self.client.close()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


# Server Class
class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = []
        print(f"Server started on {host}:{port}")

    def broadcast(self, message, client_socket):
        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(message)
                except Exception as e:
                    print(f"Error broadcasting to a client: {e}")
                    self.clients.remove(client)

    def handle_client(self, client_socket, client_address):
        print(f"New connection from {client_address}")
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                self.broadcast(message, client_socket)
            except Exception as e:
                print(f"Error handling client {client_address}: {e}")
                break

        print(f"Connection closed from {client_address}")
        self.clients.remove(client_socket)
        client_socket.close()

    def run(self):
        print("Server is running...")
        while True:
            client_socket, client_address = self.server.accept()
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True).start()


# Client Class (console-based for testing)
class ChatClientConsole:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        print(f"Connected to chat server at {host}:{port}")

    def send_messages(self):
        while True:
            message = input("You: ")
            self.client.send(message.encode())

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                print(f"\r{message}\nYou: ", end="")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def run(self):
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_messages()


# Main to Run Server or Client
if __name__ == "__main__":
    choice = input("Do you want to start the server or client? (server/client): ").strip().lower()

    if choice == "server":
        ChatServer().run()
    elif choice == "client":
        chat_choice = input("Do you want to run the GUI client or console client? (gui/console): ").strip().lower()
        if chat_choice == "gui":
            client_gui = ChatClientGUI()
            client_gui.run()
        elif chat_choice == "console":
            ChatClientConsole().run()
        else:
            print("Invalid choice. Please enter 'gui' or 'console'.")
    else:
        print("Invalid choice. Please enter 'server' or 'client'.")
