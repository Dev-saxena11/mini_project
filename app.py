# --- IMPORTS ---
from flask import Flask, render_template, request, session, redirect, flash, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
import database
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# --- APP & SOCKETIO INITIALIZATION ---
app = Flask(__name__)
app.secret_key = "a_much_more_secure_secret_key_123!"
socketio = SocketIO(app)

# --- DATABASE INITIALIZATION ---
def initialize_database():
    """Sets up DB tables if they don't exist."""
    database.setup_database()
    print("Database tables initialized.")

# --- HELPER FUNCTION ---
def validate_user_session():
    """
    Checks if the userid in the session exists in the database.
    Returns the database connection and user data if valid.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None, None  # No user in session

    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM Users WHERE userid = ?", (user_id,)).fetchone()
    
    if not user:
        session.clear()
        flash("Your session was invalid. Please log in again.", "warning")
        conn.close()
        return None, None
        
    return conn, user

# --- MAIN ROUTES ---
@app.route('/')
@app.route('/home')
def home():
    username = session.get("username")
    return render_template('home.html', username=username)

@app.route('/about')
def about():
    username = session.get("username")
    return render_template('about.html', username=username)

@app.route('/travel')
def travel():
    username = session.get("username")
    return render_template('travel.html', username=username)

# --- AUTH ROUTES ---
@app.route("/auth", methods=["GET", "POST"])
def auth():
    show_register = False
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")

        if action == "register":
            show_register = True
            email = request.form.get("email")
            
            # --- FIX: Validate the plain-text password here, BEFORE hashing ---
            is_valid, message = database.validate_password(password)
            if not is_valid:
                flash(f"⚠️ {message}", "error")
                return render_template("auth.html", show_register=True)

            # Hash the password after it has been validated
            hashed_password = generate_password_hash(password)

            user_id = database.add_user(
                username, hashed_password, email,
                phone_no=request.form.get("phone_no") or None,
                gender=request.form.get("gender") or None,
                bio=request.form.get("bio") or None
            )
            if user_id:
                session["user_id"] = user_id
                session["username"] = username
                flash("✅ Registration successful! Welcome.", "success")
                return redirect('/home')
            else:
                flash("⚠️ Registration failed. Username or email may already be in use.", "error")

        elif action == "login":
            conn = database.get_db_connection()
            user = conn.execute("SELECT * FROM Users WHERE username = ?", (username,)).fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session["user_id"] = user['userid']
                session["username"] = user['username']
                flash("✅ Login successful!", "success")
                return redirect('/home')
            else:
                flash("❌ Invalid username or password.", "error")

    return render_template("auth.html", show_register=show_register)

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect('/auth')

# --- USER DASHBOARD ---
@app.route('/user')
def user():
    conn, user_data = validate_user_session()
    if not user_data:
        return redirect("/auth")
    
    current_group = database.get_user_groups(user_data['userid'])
    group = current_group[0] if current_group else None
    
    members = []
    if group:
        members = database.get_group_members(group['group_id'])

    conn.close()
    return render_template("user.html", user=user_data, group=group, members=members)



# --- GROUP ROUTES ---
@app.route('/groups', methods=["GET", "POST"])
def groups():
    conn, user = validate_user_session()
    if not user:
        return redirect("/auth")
    
    if request.method == "POST":
        group_name = request.form.get("group_name")
        group_type = request.form.get("group_type")
        destination_name = request.form.get("destination_name")
        group_description = request.form.get("group_description")

        if not all([group_name, group_type, destination_name]):
            flash("⚠️ Group name, type, and destination are required.")
        else:
            destination_id = database.find_or_create_destination(destination_name)
            if destination_id:
                gid = database.add_group(group_name, group_type, user['userid'], destination_id, group_description)
                if gid:
                    flash(f"✅ Group '{group_name}' created successfully!")
                else:
                    flash("❌ An error occurred while creating the group.")
            else:
                flash("❌ Invalid destination name provided.")
        conn.close()
        return redirect("/groups")

    destinations = database.get_all_destinations()
    groups_list = conn.execute("""
        SELECT g.*, u.username as owner_name, d.destination_name,
               (SELECT 1 FROM GroupMembers gm WHERE gm.group_id = g.group_id AND gm.user_id = ?) as is_member
        FROM Groups g
        JOIN Users u ON g.owner_id = u.userid
        LEFT JOIN Destinations d ON g.destination_id = d.destination_id
    """, (user['userid'],)).fetchall()
    
    conn.close()
    return render_template('groups.html', groups=groups_list, user=user, destinations=destinations)

@app.route('/groups/join/<group_id>')
def join_group_route(group_id):
    conn, user = validate_user_session()
    if not user: return redirect("/auth")
    conn.close() 

    if database.join_group(user['userid'], group_id):
        flash("✅ Successfully joined the group!")
    else:
        flash("❌ Could not join group. It may be full or you're already in it.")
    return redirect("/groups")

@app.route('/groups/leave/<group_id>')
def leave_group_route(group_id):
    conn, user = validate_user_session()
    if not user: return redirect("/auth")
    conn.close()

    if database.leave_group(user['userid'], group_id):
        flash("✅ You have left the group.")
    else:
        flash("❌ Could not leave group. Owners must delete their group instead.")
    return redirect("/groups")

@app.route('/groups/delete/<group_id>')
def delete_group_route(group_id):
    conn, user = validate_user_session()
    if not user: return redirect("/auth")
    
    if database.delete_group(group_id, user['userid']):
        flash("✅ Group deleted successfully!")
    else:
        flash("❌ You are not authorized to delete this group.")
    
    conn.close()
    return redirect("/groups")

# --- GROUP CHAT ROUTES ---
@app.route('/groups/chat/<group_id>')
def group_chat(group_id):
    conn, user = validate_user_session()
    if not user: return redirect("/auth")

    is_member = conn.execute("SELECT 1 FROM GroupMembers WHERE group_id=? AND user_id=?", (group_id, user['userid'])).fetchone()
    if not is_member:
        flash("⚠️ You are not a member of this group.")
        conn.close()
        return redirect("/groups")

    group = conn.execute("SELECT group_name FROM Groups WHERE group_id=?", (group_id,)).fetchone()
    db_rows = conn.execute("""
        SELECT m.message, m.timestamp, u.username AS sender_name
        FROM GroupMessages m JOIN Users u ON m.sender_id = u.userid
        WHERE m.group_id = ? ORDER BY m.timestamp ASC
    """, (group_id,)).fetchall()
    conn.close()

    messages = [dict(row) for row in db_rows]
    return render_template(
        "group_chat.html",
        group_id=group_id,
        group_name=group['group_name'],
        messages=messages,
        username=user['username']
    )

# --- API ROUTES ---
@app.route('/api/messages/send/<group_id>', methods=['POST'])
def send_message_api(group_id):
    conn, user = validate_user_session()
    if not user:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    data = request.json
    message_text = data.get('message')
    if not message_text:
        conn.close()
        return jsonify({"status": "error", "message": "Message is empty"}), 400

    if not database.add_group_message(group_id, user['userid'], message_text):
        conn.close()
        return jsonify({"status": "error", "message": "Could not save message."}), 500
    
    message_payload = {
        "sender_name": user['username'],
        "message": message_text,
        "timestamp": datetime.now().isoformat()
    }
    
    socketio.emit('new_message', message_payload, to=group_id)
    
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    data = request.json
    user_message = data.get('message', '').lower()
    
    bot_response = "I'm not sure how to help with that. Try asking about our features or for a travel recommendation!"
    
    recommend_keywords = ['recommend', 'popular', 'destination', 'suggest', 'where to go']
    if any(keyword in user_message for keyword in recommend_keywords):
        popular_destinations = database.get_popular_destinations()
        if popular_destinations:
            dest_list = ", ".join(popular_destinations)
            bot_response = f"✈️ Our most popular destinations are: {dest_list}. You can create a group for one of them!"
        else:
            bot_response = "We don't have any popular destinations yet, but you can be the first to start a trend!"
            
    return jsonify({"response": bot_response})

# --- WEBSOCKET EVENT HANDLERS ---
@socketio.on('join_room')
def handle_join_room(data):
    group_id = data['group_id']
    join_room(group_id)
    print(f"Client joined room: {group_id}")

@socketio.on('leave_room')
def handle_leave_room(data):
    group_id = data['group_id']
    leave_room(group_id)
    print(f"Client left room: {group_id}")

# In app.py, replace your current run_server function with this one:

def run_server():
    """Initialize DB and start the SocketIO server."""
    initialize_database()
    print("Starting Flask + SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000)  # <-- use 0.0.0.0
