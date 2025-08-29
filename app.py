from flask import Flask, render_template, request, session, redirect, flash
import database  # your database.py

app = Flask(__name__)
app.secret_key = "my_secret_123"

# --- Setup DB on startup ---
database.setup_database()

@app.route('/')
@app.route('/home')
def home():
    username = session.get("username")
    return render_template('home.html', username=username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/groups', methods=["GET", "POST"])
def groups():
    # Ensure user is logged in
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to manage groups.")
        return redirect("/auth")

    # Get user info
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Get user ID
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()
    user_id = user['userid']

    # cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
    # user = cursor.fetchone()
    # conn.close()

    # Handle group creation
    if request.method == "POST":
        group_name = request.form.get("group_name")
        group_type = request.form.get("group_type")
        group_description = request.form.get("group_description")

        if not group_name or not group_type:
            flash("⚠️ Group name and type are required.")
        else:
            gid = database.add_group(group_name, group_type, user['userid'], group_description)
            if gid:
                flash(f"✅ Group '{group_name}' created successfully!")
            else:
                flash("❌ Could not create group.")

        return redirect("/groups")

    # Fetch all groups
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.group_id, g.group_name, g.group_type, g.group_description,
               u.username AS owner_name, g.member_count,CASE WHEN gm.user_id=?THEN 1 ELSE 0 END AS is_member
        FROM Groups g 
        JOIN Users u ON g.owner_id = u.userid
        LEFT JOIN GroupMembers gm ON g.group_id = gm.group_id AND gm.user_id = ?
    """, (user_id, user_id))
    groups = cursor.fetchall()
    conn.close()

    return render_template('groups.html', groups=groups, user=user)

@app.route('/groups/join/<group_id>')
def join_group(group_id):
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to join a group.")
        return redirect("/auth")

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if database.join_group(user['userid'], group_id):
        flash("✅ Successfully joined the group!")
        return redirect(f"/groups/chat/{group_id}")
    else:
        flash("❌ Could not join the group.")
        return redirect("/groups")


@app.route('/groups/delete/<group_id>')
def delete_group(group_id):
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to delete a group.")
        return redirect("/auth")

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()

    # Check if user is the owner
    cursor.execute("SELECT owner_id FROM Groups WHERE group_id=?", (group_id,))
    group = cursor.fetchone()

    if not group or group['owner_id'] != user['userid']:
        flash("❌ You are not authorized to delete this group.")
        conn.close()
        return redirect("/groups")

    # Delete group
    database.delete_group(group_id)
    flash("✅ Group deleted successfully!")
    
    conn.close()
    return redirect("/groups")

# Route for INCOMING MESSAGES (receives data from JavaScript)
@app.route('/api/messages/send/<group_id>', methods=['POST'])
def send_message_api(group_id):
    username = session.get("username")
    if not username:
        return {"status": "error", "message": "Not logged in"}, 401

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "message": "User not found"}, 404

    data = request.json
    message = data.get('message')
    if not message:
        return {"status": "error", "message": "Message is empty"}, 400

    # Save the message to the database
    database.add_group_message(group_id, user['userid'], message)

    # Return a success response with data for the new message bubble
    from datetime import datetime
    return {
        "status": "success",
        "message": {
            "sender_name": username,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }


# Route for LOADING THE CHAT PAGE (only handles GET requests now)
@app.route('/groups/chat/<group_id>', methods=['GET'])
def group_chat(group_id):
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to access group chat.")
        return redirect("/auth")

    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Get user info
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()

    # Check if user is a member of this group
    cursor.execute("SELECT 1 FROM GroupMembers WHERE group_id = ? AND user_id = ?", (group_id, user['userid']))
    if not cursor.fetchone():
        flash("⚠️ You are not a member of this group.")
        conn.close()
        return redirect("/groups")

    # Fetch group info
    cursor.execute("SELECT group_name FROM Groups WHERE group_id=?", (group_id,))
    group = cursor.fetchone()

    # Fetch all messages
    cursor.execute("""
    SELECT m.message, m.timestamp, u.username AS sender_name
    FROM GroupMessages m JOIN Users u ON m.sender_id = u.userid
    WHERE m.group_id = ? ORDER BY m.timestamp ASC
""", (group_id,))

    # Fetch the special 'Row' objects
    db_rows = cursor.fetchall()
    conn.close()

    # CONVERT the 'Row' objects into a list of standard dictionaries
    messages = [dict(row) for row in db_rows]

    return render_template(
        "group_chat.html",
        group_id=group_id,
        group_name=group['group_name'],
        messages=messages,
        username=username
    )


@app.route('/groups/leave')
def leave_group():
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to leave a group.")
        return redirect("/auth")

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM Users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if database.leave_group(user['userid']):
        flash("✅ You left your current group.")
    else:
        flash("❌ Could not leave the group.")
    return redirect("/groups")

@app.route('/travel')
def travel():
    return render_template('travel.html')

@app.route('/user')
def user():
    username = session.get("username")
    if not username:
        flash("⚠️ You must be logged in to view your dashboard.")
        return redirect("/auth")

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
    user_data = cursor.fetchone()

    group_data = None
    members = []
    if user_data and user_data['current_group_id']:
        group_data = database.get_user_group(user_data['userid'])
        if group_data:
            members = database.get_group_members(group_data['group_id'])

    conn.close()
    return render_template("user.html", user=user_data, group=group_data, members=members)

@app.route("/auth", methods=["GET", "POST"])
def auth():
    show_register = False  # default: show login form

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        if action == "register":
            show_register = True  # if user clicked register, stay on that form
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
                flash("⚠️ Registration failed. Username/email exists or password too weak.", "error")
                return render_template("auth.html", show_register=True)

            session["username"] = username
            flash("✅ Registration successful! Welcome.", "success")
            return redirect('/home')

        elif action == "login":
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("❌ Invalid username or password.", "error")
                return render_template("auth.html", show_register=False)

            session["username"] = username
            flash("✅ Login successful!", "success")
            return redirect('/home')

    return render_template("auth.html", show_register=show_register)

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("👋 You have been logged out.")
    return redirect('/home')

if __name__ == '__main__':
    app.run(debug=True)