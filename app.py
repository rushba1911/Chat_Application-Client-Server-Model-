from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
from datetime import datetime
import os

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create the uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy, Bcrypt, LoginManager, and SocketIO
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
socketio = SocketIO(app)

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Message model to store chat messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(150), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set to current time

    def __repr__(self):
        return f"Message({self.id}, '{self.sender}', '{self.content}', '{self.timestamp}')"

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("chat"))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("chat"))
        else:
            flash("Login failed. Check your username and password.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! You can log in now.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/chat")
@login_required
def chat():
    # Retrieve the last 20 messages from the database
    messages = Message.query.order_by(Message.timestamp.desc()).limit(20).all()
    # Reverse to show oldest messages at the top
    messages = messages[::-1]
    return render_template("chat.html", username=current_user.username, messages=messages)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Return file name in JSON for the frontend
        return {"file": filename}
    return {"error": "No file uploaded"}, 400


@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Store connected users
connected_users = {}

# SocketIO event to handle user connection
@socketio.on('connect')
def handle_connect():
    connected_users[current_user.username] = request.sid
    emit('user_list', list(connected_users.keys()), broadcast=True)  # Send the list of users to all clients

# SocketIO event to handle user disconnection
@socketio.on('disconnect')
def handle_disconnect():
    if current_user.username in connected_users:
        del connected_users[current_user.username]
    emit('user_list', list(connected_users.keys()), broadcast=True)  # Send updated user list

# SocketIO event to handle incoming messages
@socketio.on('message')
def handle_message(data):
    sender = current_user.username
    message = data.get('message')
    file = data.get('file')

    # Save message to the database
    if message:
        new_message = Message(sender=sender, content=message)
        db.session.add(new_message)
        db.session.commit()  # Commit to save the message to the database
        emit('message', {'sender': sender, 'message': message}, broadcast=True)

    elif file:
        new_message = Message(sender=sender, content=f"File: {file}")
        db.session.add(new_message)
        db.session.commit()  # Commit to save the file message to the database
        emit('message', {'sender': sender, 'file': file}, broadcast=True)


@socketio.on('join')
def join_private_room(data):
    recipient = data['recipient']
    room = recipient
    join_room(room)
    print(f"{current_user.username} joined private room {room}")

@socketio.on('leave')
def leave_private_room(data):
    recipient = data['recipient']
    room = recipient
    leave_room(room)
    print(f"{current_user.username} left private room {room}")

# SocketIO typing handler
@socketio.on('typing')
def handle_typing(data):
    sender = current_user.username  # Use the authenticated user's username
    emit('typing', {'sender': sender}, broadcast=True)

# Run the Flask application with SocketIO in a separate thread
def run_flask():
    socketio.run(app, host='0.0.0.0', port=5000)

# Create the database and tables on app startup
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates both User and Message tables
    threading.Thread(target=run_flask).start()
