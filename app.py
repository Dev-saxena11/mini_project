from flask import Flask, render_template, request, session, redirect, flash, jsonify
import database
from datetime import datetime

app = Flask(__name__)
app.secret_key = "my_secret_123"

# --- DB Initialization on Startup ---
def initialize_database():
    """Sets up DB and populates with sample data if it's empty."""
    database.setup_database()
    conn = database.get_db_connection()
    try:
        user_count = conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
        if user_count == 0:
            print("Database is empty. Populating with sample data...")
            database.insert_sample_data()
            print("Sample data has been inserted.")
        else:
            print("Database already contains data. Skipping sample data insertion.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
    finally:
        conn.close()

# --- HELPER FUNCTION TO VALIDATE USER SESSION ---
def validate_user_session():
    """Checks if the username in the session exists in the database."""
    username = session.get("username")
    if not username:
        return None, None # No user in session

    conn = database.get_db_connection()
    user = conn.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()
    
    if not user:
        # User in session does not exist in DB, clear session
        session.pop("username", None)
        flash("Your session was invalid. Please log in again.", "warning")
        conn.close()
        return None, None
        
    return conn, user

# --- Main Routes ---

@app.route('/')
@app.route('/home')
def home():
    username = session.get("username")
    return render_template('home.html', username=username)

# --- Auth Routes ---

@app.route("/auth", methods=["GET", "POST"])
def auth():
    # ... (No changes in this route) ...
    show_register = False
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")

        if action == "register":
            show_register = True
            email = request.form.get("email")
            phone_no = request.form.get("phone_no") or None
            gender = request.form.get("gender") or None
            marital_status = request.form.get("marital_status") or None
            bio = request.form.get("bio") or None

            user_id = database.add_user(
                username, password, email,
                phone_no=phone_no, gender=gender,
                marital_status=marital_status, bio=bio
            )
            if not user_id:
                flash("⚠️ Registration failed. Username/email may exist or password is too weak.", "error")
            else:
                session["username"] = username
                flash("✅ Registration successful! Welcome.", "success")
                return redirect('/home')

        elif action == "login":
            conn = database.get_db_connection()
            user = conn.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, password)).fetchone()
            conn.close()
            if not user:
                flash("❌ Invalid username or password.", "error")
            else:
                session["username"] = username
                flash("✅ Login successful!", "success")
                return redirect('/home')

    return render_template("auth.html", show_register=show_register)

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("👋 You have been logged out.")
    return redirect('/home')

# --- User Dashboard ---

@app.route('/user')
def user():
    conn, user_data = validate_user_session()
    if not user_data:
        return redirect("/auth")
    
    group_data = None
    members = []
    if user_data['current_group_id']:
        group_data = database.get_user_group(user_data['userid'])
        if group_data:
            members = database.get_group_members(group_data['group_id'])
    
    conn.close()
    return render_template("user.html", user=user_data, group=group_data, members=members)

# --- Group Routes ---

@app.route('/groups', methods=["GET", "POST"])
def groups():
    conn, user = validate_user_session()
    if not user:
        return redirect("/auth")
    
    if request.method == "POST":
        group_name = request.form.get("group_name")
        group_type = request.form.get("group_type")
        destination_id = request.form.get("destination_id")
        group_description = request.form.get("group_description")

        if not all([group_name, group_type, destination_id]):
            flash("⚠️ Group name, type, and destination are required.")
        else:
            gid = database.add_group(group_name, group_type, user['userid'], destination_id, group_description)
            if gid:
                flash(f"✅ Group '{group_name}' created successfully!")
            else:
                flash("❌ Could not create group. You may already be in one.")
        conn.close()
        return redirect("/groups")

    destinations = database.get_all_destinations()
    
    groups_list = conn.execute("""
        SELECT g.*, u.username as owner_name, d.destination_name,
               CASE WHEN gm.user_id IS NOT NULL THEN 1 ELSE 0 END as is_member
        FROM Groups g
        JOIN Users u ON g.owner_id = u.userid
        LEFT JOIN Destinations d ON g.destination_id = d.destination_id
        LEFT JOIN GroupMembers gm ON g.group_id = gm.group_id AND gm.user_id = ?
    """, (user['userid'],)).fetchall()
    
    conn.close()
    return render_template('groups.html', groups=groups_list, user=user, destinations=destinations)

# Other routes are omitted for brevity but should also use validate_user_session()
# The rest of your app.py file can remain the same...

# --- Example of updating another route ---
@app.route('/groups/join/<group_id>')
def join_group(group_id):
    conn, user = validate_user_session()
    if not user:
        return redirect("/auth")
    conn.close() # Connection is no longer needed here

    if database.join_group(user['userid'], group_id):
        flash("✅ Successfully joined the group!")
    else:
        flash("❌ Could not join group. It may be full or you're already in one.")
    return redirect("/groups")

# --- Full app.py continues below ---
@app.route('/about')
def about():
    username = session.get("username")
    return render_template('about.html', username=username)

@app.route('/travel')
def travel():
    username = session.get("username")
    return render_template('travel.html', username=username)

@app.route('/groups/leave')
def leave_group():
    conn, user = validate_user_session()
    if not user: return redirect("/auth")
    conn.close()

    if database.leave_group(user['userid']):
        flash("✅ You have left your current group.")
    else:
        flash("❌ Could not leave group. Owners must delete their group.")
    return redirect("/groups")

@app.route('/groups/delete/<group_id>')
def delete_group(group_id):
    conn, user = validate_user_session()
    if not user: return redirect("/auth")

    group = conn.execute("SELECT owner_id FROM Groups WHERE group_id=?", (group_id,)).fetchone()
    
    if not group or group['owner_id'] != user['userid']:
        flash("❌ You are not authorized to delete this group.")
    else:
        database.delete_group(group_id)
        flash("✅ Group deleted successfully!")
    
    conn.close()
    return redirect("/groups")

@app.route('/groups/chat/<group_id>', methods=['GET'])
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
    username = user['username']

    return render_template(
        "group_chat.html",
        group_id=group_id,
        group_name=group['group_name'],
        messages=messages,
        username=username
    )

@app.route('/api/messages/send/<group_id>', methods=['POST'])
def send_message_api(group_id):
    conn, user = validate_user_session()
    if not user:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    conn.close()
    
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({"status": "error", "message": "Message is empty"}), 400

    if not database.add_group_message(group_id, user['userid'], message):
      return jsonify({"status": "error", "message": "Could not save message."}), 500
    
    return jsonify({
        "status": "success",
        "message": {
            "sender_name": user['username'],
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    })


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)