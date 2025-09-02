import sqlite3
import uuid
import re

def generate_id():
    """Generates a unique ID using UUID4."""
    return uuid.uuid4().hex

def validate_password(password):
    """Validates password strength requirements."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."

def validate_email(email):
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[1]

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect('travel_together.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_database():
    """Creates the database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    create_users_table_query = """
    CREATE TABLE IF NOT EXISTS Users (
        userid TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone_no TEXT UNIQUE,
        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
        marital_status TEXT CHECK(marital_status IN ('Single', 'Married', 'Divorced', 'Widowed')),
        profile_picture TEXT,
        bio TEXT,
        current_group_id TEXT,
        is_group_owner BOOLEAN DEFAULT FALSE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_group_id) REFERENCES Groups (group_id) ON DELETE SET NULL
    );
    """
    cursor.execute(create_users_table_query)

    # Groups table
    create_groups_table_query = """
    CREATE TABLE IF NOT EXISTS Groups (
        group_id TEXT PRIMARY KEY,
        group_name TEXT NOT NULL,
        group_description TEXT,
        group_type TEXT NOT NULL CHECK(group_type IN ('Public', 'Private')),
        owner_id TEXT NOT NULL,
        member_count INTEGER DEFAULT 1,
        max_members INTEGER DEFAULT 50,
        total_duration_days INTEGER,
        estimated_total_cost TEXT,
        travel_start_date DATE,
        travel_end_date DATE,
        status TEXT DEFAULT 'Planning' CHECK(status IN ('Planning', 'Active', 'Completed', 'Cancelled')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES Users (userid) ON DELETE CASCADE
    );
    """
    cursor.execute(create_groups_table_query)

    # Destinations table
    create_destinations_table_query = """
    CREATE TABLE IF NOT EXISTS Destinations (
        destination_id TEXT PRIMARY KEY,
        destination_name TEXT UNIQUE NOT NULL,
        state_province TEXT,
        country TEXT NOT NULL,
        description TEXT,
        best_time_to_visit TEXT,
        difficulty_level TEXT CHECK(difficulty_level IN ('Easy', 'Moderate', 'Hard')),
        estimated_budget_per_day TEXT,
        popular_activities TEXT,
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_destinations_table_query)

    # TravelItinerary table
    create_travel_itinerary_query = """
    CREATE TABLE IF NOT EXISTS TravelItinerary (
        itinerary_id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        destination_id TEXT NOT NULL,
        visit_order INTEGER NOT NULL,
        planned_arrival_date DATE,
        planned_departure_date DATE,
        duration_days INTEGER DEFAULT 1,
        estimated_cost TEXT,
        accommodation_type TEXT,
        transport_to_next TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE,
        FOREIGN KEY (destination_id) REFERENCES Destinations (destination_id) ON DELETE CASCADE,
        UNIQUE(group_id, destination_id),
        UNIQUE(group_id, visit_order)
    );
    """
    cursor.execute(create_travel_itinerary_query)

    # TouristSpots table
    create_tourist_spots_table_query = """
    CREATE TABLE IF NOT EXISTS TouristSpots (
        spot_id TEXT PRIMARY KEY,
        destination_id TEXT NOT NULL,
        spot_name TEXT NOT NULL,
        spot_type TEXT CHECK(spot_type IN ('Historical', 'Natural', 'Adventure', 'Religious', 'Cultural', 'Beach', 'Mountain')),
        description TEXT,
        entry_fee TEXT,
        opening_hours TEXT,
        rating DECIMAL(2,1) CHECK(rating >= 0 AND rating <= 5),
        coordinates TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (destination_id) REFERENCES Destinations (destination_id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_tourist_spots_table_query)

    # GroupMembers table
    create_group_members_table_query = """
    CREATE TABLE IF NOT EXISTS GroupMembers (
        member_id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        join_status TEXT DEFAULT 'Approved' CHECK(join_status IN ('Pending', 'Approved', 'Rejected', 'Blocked')),
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'Member' CHECK(role IN ('Owner', 'Admin', 'Member')),
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users (userid) ON DELETE CASCADE,
        UNIQUE(group_id, user_id)
    );
    """
    cursor.execute(create_group_members_table_query)

    # GroupMessages table
    create_group_messages_table_query = """
    CREATE TABLE IF NOT EXISTS GroupMessages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_username TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES Users (userid) ON DELETE CASCADE
    );
    """
    cursor.execute(create_group_messages_table_query)

    # Notifications table
    create_notifications_table_query = """
    CREATE TABLE IF NOT EXISTS Notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        group_id TEXT,
        notification_type TEXT CHECK(notification_type IN ('join_request', 'member_joined', 'member_left', 'status_update', 'group_update')) DEFAULT 'group_update',
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (userid) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_notifications_table_query)

    # Performance indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_travel_itinerary_group ON TravelItinerary(group_id, visit_order);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tourist_spots_destination ON TouristSpots(destination_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_group_timestamp ON GroupMessages(group_id, timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_members_group ON GroupMembers(group_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_members_user ON GroupMembers(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON Notifications(user_id, is_read);")

    print("Database and tables are ready.")
    conn.commit()
    conn.close()

# NOTIFICATION FUNCTIONS

def add_notification(user_id, group_id, notification_type, message):
    """Adds a new notification for a user."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO Notifications (user_id, group_id, notification_type, message) VALUES (?, ?, ?, ?)",
            (user_id, group_id, notification_type, message)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not add notification. {e}")
        return False
    finally:
        conn.close()

def notify_group_members_join(user_id, group_id, joining_username):
    """Notifies existing group members when someone joins (public groups only)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group is public
        cursor.execute("SELECT group_name, group_type FROM Groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        if not group or group['group_type'] != 'Public':
            return
        
        # Get all approved members except the one who just joined
        cursor.execute("""
            SELECT user_id FROM GroupMembers 
            WHERE group_id = ? AND user_id != ? AND join_status = 'Approved'
        """, (group_id, user_id))
        
        members = cursor.fetchall()
        message = f"'{joining_username}' has joined your group '{group['group_name']}'."
        
        for member in members:
            add_notification(member['user_id'], group_id, 'member_joined', message)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not send join notifications. {e}")
    finally:
        conn.close()

def notify_group_members_leave(user_id, group_id, leaving_username):
    """Notifies existing group members when someone leaves (public groups only)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if group is public
        cursor.execute("SELECT group_name, group_type FROM Groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        if not group or group['group_type'] != 'Public':
            return
        
        # Get all approved members except the one who left
        cursor.execute("""
            SELECT user_id FROM GroupMembers 
            WHERE group_id = ? AND user_id != ? AND join_status = 'Approved'
        """, (group_id, user_id))
        
        members = cursor.fetchall()
        message = f"'{leaving_username}' has left your group '{group['group_name']}'."
        
        for member in members:
            add_notification(member['user_id'], group_id, 'member_left', message)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not send leave notifications. {e}")
    finally:
        conn.close()

def notify_owner_join_request(requesting_user_id, group_id):
    """Notifies group owner when someone requests to join a private group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get group owner and requesting user info
        cursor.execute("SELECT owner_id, group_name FROM Groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        if not group:
            return
        
        cursor.execute("SELECT username FROM Users WHERE userid = ?", (requesting_user_id,))
        user = cursor.fetchone()
        if not user:
            return
        
        message = f"'{user['username']}' has requested to join your private group '{group['group_name']}'."
        add_notification(group['owner_id'], group_id, 'join_request', message)
        
    except sqlite3.Error as e:
        print(f"ERROR: Could not send join request notification. {e}")
    finally:
        conn.close()

def notify_user_status_update(user_id, group_id, new_status):
    """Notifies user when their membership status changes."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT group_name FROM Groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        if not group:
            return
        
        if new_status == 'Approved':
            message = f"Your request to join '{group['group_name']}' has been approved!"
        elif new_status == 'Rejected':
            message = f"Your request to join '{group['group_name']}' has been rejected."
        elif new_status == 'Blocked':
            message = f"You have been blocked from group '{group['group_name']}'."
        else:
            return
        
        add_notification(user_id, group_id, 'status_update', message)
        
    except sqlite3.Error as e:
        print(f"ERROR: Could not send status update notification. {e}")
    finally:
        conn.close()

def view_notifications(user_id, unread_only=False):
    """Displays notifications for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if unread_only:
            cursor.execute("""
                SELECT n.notification_id, n.message, n.notification_type, n.is_read, n.created_at,
                       g.group_name
                FROM Notifications n
                LEFT JOIN Groups g ON n.group_id = g.group_id
                WHERE n.user_id = ? AND n.is_read = 0
                ORDER BY n.created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT n.notification_id, n.message, n.notification_type, n.is_read, n.created_at,
                       g.group_name
                FROM Notifications n
                LEFT JOIN Groups g ON n.group_id = g.group_id
                WHERE n.user_id = ?
                ORDER BY n.created_at DESC
                LIMIT 20
            """, (user_id,))
        
        notifications = cursor.fetchall()
        
        if not notifications:
            print("No notifications found.")
            return
        
        title = "Unread Notifications" if unread_only else "Recent Notifications"
        print(f"\n--- {title} ---")
        
        for notif in notifications:
            status = "UNREAD" if not notif['is_read'] else "READ"
            timestamp = notif['created_at'][:19]  # Remove microseconds
            print(f"[{status}] {timestamp}")
            print(f"Type: {notif['notification_type']}")
            print(f"Message: {notif['message']}")
            if notif['group_name']:
                print(f"Group: {notif['group_name']}")
            print(f"ID: {notif['notification_id']}")
            print("-" * 50)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve notifications. {e}")
    finally:
        conn.close()

def mark_notification_read(notification_id, user_id):
    """Marks a notification as read."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Notifications SET is_read = 1 
            WHERE notification_id = ? AND user_id = ?
        """, (notification_id, user_id))
        
        if cursor.rowcount == 0:
            print("ERROR: Notification not found or access denied.")
            return False
        
        conn.commit()
        print("SUCCESS: Notification marked as read.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not mark notification as read. {e}")
        return False
    finally:
        conn.close()

def mark_all_notifications_read(user_id):
    """Marks all notifications as read for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        
        conn.commit()
        print(f"SUCCESS: All notifications marked as read. ({cursor.rowcount} notifications updated)")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not mark notifications as read. {e}")
        return False
    finally:
        conn.close()

def get_unread_count(user_id):
    """Gets the count of unread notifications for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Notifications WHERE user_id = ? AND is_read = 0", (user_id,))
        count = cursor.fetchone()['count']
        return count
    except sqlite3.Error as e:
        print(f"ERROR: Could not get unread count. {e}")
        return 0
    finally:
        conn.close()

# USER MANAGEMENT FUNCTIONS

def add_user(username, password, email, **kwargs):
    """Adds a new user to the Users table."""
    is_valid, message = validate_password(password)
    if not is_valid:
        print(f"ERROR: {message}")
        return None

    if not validate_email(email):
        print("ERROR: Invalid email format.")
        return None

    user_id = generate_id()
    conn = get_db_connection()
    
    try:
        conn.execute(
            """INSERT INTO Users (userid, username, password, email, phone_no, gender, 
               marital_status, profile_picture, bio, current_group_id, is_group_owner) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, password, email, kwargs.get('phone_no'), 
             kwargs.get('gender'), kwargs.get('marital_status'), 
             kwargs.get('profile_picture'), kwargs.get('bio'), None, False)
        )
        conn.commit()
        print(f"SUCCESS: User '{username}' added with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            print("ERROR: Username already exists.")
        elif "email" in str(e):
            print("ERROR: Email already exists.")
        else:
            print(f"ERROR: Could not add user. {e}")
        return None
    finally:
        conn.close()

def update_user_profile(user_id, **kwargs):
    """Updates user's profile information."""
    allowed_fields = ["phone_no", "gender", "marital_status", "profile_picture", "bio"]
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if not updates:
            print("ERROR: No valid fields provided for update.")
            return False
        
        values.append(user_id)
        sql = f"UPDATE Users SET {', '.join(updates)} WHERE userid = ?"
        
        cursor.execute(sql, values)
        if cursor.rowcount == 0:
            print(f"ERROR: No user found with ID '{user_id}'.")
            return False
        
        conn.commit()
        print("SUCCESS: User profile updated.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not update user profile. {e}")
        return False
    finally:
        conn.close()

def update_password(user_id, new_password):
    """Updates user's password after validation."""
    is_valid, message = validate_password(new_password)
    if not is_valid:
        print(f"ERROR: {message}")
        return False
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET password = ? WHERE userid = ?", (new_password, user_id))
        if cursor.rowcount == 0:
            print(f"ERROR: No user found with ID '{user_id}'.")
            return False
        
        conn.commit()
        print("SUCCESS: Password updated successfully.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not update password. {e}")
        return False
    finally:
        conn.close()

def delete_user(user_id):
    """Deletes a user from the Users table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Handle group membership cleanup
        cursor.execute("SELECT current_group_id, is_group_owner FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            if user_data['current_group_id'] and not user_data['is_group_owner']:
                leave_group(user_id)
            elif user_data['is_group_owner']:
                cursor.execute("SELECT group_id FROM Groups WHERE owner_id = ?", (user_id,))
                group_data = cursor.fetchone()
                if group_data:
                    delete_group(group_data['group_id'])
        
        cursor.execute("DELETE FROM Users WHERE userid = ?", (user_id,))
        if cursor.rowcount == 0:
            print(f"ERROR: No user found with ID '{user_id}'.")
            return False
        else:
            conn.commit()
            print(f"SUCCESS: User with ID '{user_id}' deleted.")
            return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not delete user. {e}")
        return False
    finally:
        conn.close()

def view_users():
    """Displays all users with their current group information."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.userid, u.username, u.email, 
                   COALESCE(g.group_name, 'No Group') as current_group
            FROM Users u 
            LEFT JOIN Groups g ON u.current_group_id = g.group_id
        """)
        users = cursor.fetchall()
        
        if not users:
            print("No users found.")
            return
            
        print("\n--- Users List ---")
        print(f"{'ID':<32} {'Username':<15} {'Email':<25} {'Current Group':<20}")
        print("-" * 95)
        for user in users:
            print(f"{user['userid']:<32} {user['username']:<15} {user['email']:<25} {user['current_group']:<20}")
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve users. {e}")
    finally:
        conn.close()

# DESTINATION MANAGEMENT FUNCTIONS

def add_destination(destination_name, state_province, country, **kwargs):
    """Adds a new destination to the Destinations table."""
    destination_id = generate_id()
    conn = get_db_connection()
    
    try:
        conn.execute(
            """INSERT INTO Destinations (destination_id, destination_name, state_province, 
               country, description, best_time_to_visit, difficulty_level, estimated_budget_per_day, 
               popular_activities, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (destination_id, destination_name, state_province, country,
             kwargs.get('description'), kwargs.get('best_time_to_visit'),
             kwargs.get('difficulty_level'), kwargs.get('estimated_budget_per_day'),
             kwargs.get('popular_activities'), kwargs.get('latitude'), kwargs.get('longitude'))
        )
        conn.commit()
        print(f"SUCCESS: Destination '{destination_name}' added with ID: {destination_id}")
        return destination_id
    except sqlite3.IntegrityError as e:
        print(f"ERROR: Destination name already exists. {e}")
        return None
    finally:
        conn.close()

def view_destinations():
    """Display all available destinations."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Destinations ORDER BY destination_name")
        destinations = cursor.fetchall()
        
        if not destinations:
            print("No destinations found.")
            return
            
        print("\n--- Available Destinations ---")
        for dest in destinations:
            print(f"ID: {dest['destination_id']}")
            print(f"Name: {dest['destination_name']}")
            print(f"Location: {dest['state_province']}, {dest['country']}")
            print(f"Best Time: {dest['best_time_to_visit'] or 'N/A'}")
            print(f"Difficulty: {dest['difficulty_level'] or 'N/A'}")
            print(f"Budget/Day: {dest['estimated_budget_per_day'] or 'N/A'}")
            print(f"Description: {dest['description'] or 'No description'}")
            print("-" * 50)
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve destinations. {e}")
    finally:
        conn.close()

# GROUP MANAGEMENT FUNCTIONS

def create_group_with_itinerary(owner_id, group_name, group_type, destination_ids, **kwargs):
    """Creates a new group with a travel itinerary."""
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Validate user can create group
        cursor.execute("SELECT userid, username, current_group_id, is_group_owner FROM Users WHERE userid = ?", (owner_id,))
        user_data = cursor.fetchone()
        if not user_data:
            print(f"ERROR: User with ID '{owner_id}' does not exist.")
            return None
            
        if user_data['current_group_id']:
            print("ERROR: You are already a member of a group. Leave your current group first.")
            return None
            
        if user_data['is_group_owner']:
            print("ERROR: You already own a group. Delete your existing group first.")
            return None

        # Validate all destination IDs exist
        for dest_id in destination_ids:
            cursor.execute("SELECT destination_id FROM Destinations WHERE destination_id = ?", (dest_id,))
            if not cursor.fetchone():
                print(f"ERROR: Destination with ID '{dest_id}' does not exist.")
                return None
            
        group_id = generate_id()
        owner_username = user_data['username']
        
        # Create the group
        conn.execute(
            """INSERT INTO Groups (group_id, group_name, group_description, group_type, 
               owner_id, max_members, total_duration_days, estimated_total_cost, 
               travel_start_date, travel_end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (group_id, group_name, kwargs.get('group_description'), group_type,
             owner_id, kwargs.get('max_members', 50), kwargs.get('total_duration_days'),
             kwargs.get('estimated_total_cost'), kwargs.get('travel_start_date'),
             kwargs.get('travel_end_date'))
        )
        
        # Add destinations to itinerary in order
        for order, dest_id in enumerate(destination_ids, 1):
            itinerary_id = generate_id()
            conn.execute(
                """INSERT INTO TravelItinerary (itinerary_id, group_id, destination_id, visit_order,
                   duration_days, notes) VALUES (?, ?, ?, ?, ?, ?)""",
                (itinerary_id, group_id, dest_id, order, 
                 kwargs.get('duration_per_destination', 2), 
                 f"Stop {order} in the travel chain")
            )
        
        # Add owner to GroupMembers
        member_id = generate_id()
        conn.execute(
            """INSERT INTO GroupMembers (member_id, group_id, user_id, username, role) 
               VALUES (?, ?, ?, ?, 'Owner')""",
            (member_id, group_id, owner_id, owner_username)
        )
        
        # Update user's status
        conn.execute(
            "UPDATE Users SET current_group_id = ?, is_group_owner = TRUE WHERE userid = ?", 
            (group_id, owner_id)
        )
        
        conn.commit()
        print(f"SUCCESS: Group '{group_name}' created with {len(destination_ids)}-destination itinerary.")
        print(f"Group ID: {group_id}")
        return group_id
    except sqlite3.Error as e:
        print(f"ERROR: Could not create group. {e}")
        return None
    finally:
        conn.close()

def join_group(user_id, group_id):
    """User joins a group with notification system."""
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check user status
        cursor.execute("SELECT userid, username, current_group_id, is_group_owner FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            print(f"ERROR: User with ID '{user_id}' does not exist.")
            return False
            
        if user_data['current_group_id']:
            print("ERROR: You are already a member of a group. Leave your current group first.")
            return False
            
        if user_data['is_group_owner']:
            print("ERROR: You own a group. You cannot join another group.")
            return False
            
        username = user_data['username']
        
        # Check group availability
        cursor.execute("""SELECT group_id, group_name, group_type, member_count, max_members 
                         FROM Groups WHERE group_id = ?""", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return False
            
        if group_data['member_count'] >= group_data['max_members']:
            print("ERROR: Group is full.")
            return False
            
        # Set join status based on group type
        join_status = 'Pending' if group_data['group_type'] == 'Private' else 'Approved'
        
        # Add user to GroupMembers
        member_id = generate_id()
        conn.execute(
            """INSERT INTO GroupMembers (member_id, group_id, user_id, username, join_status) 
               VALUES (?, ?, ?, ?, ?)""",
            (member_id, group_id, user_id, username, join_status)
        )
        
        # Handle notifications and status updates
        if join_status == 'Approved':
            # Update user and group for public groups
            conn.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", (group_id, user_id))
            conn.execute("UPDATE Groups SET member_count = member_count + 1 WHERE group_id = ?", (group_id,))
            print(f"SUCCESS: Joined group '{group_data['group_name']}'.")
            
            # Notify existing members about new member (public groups only)
            conn.commit()  # Commit first to ensure the member is added
            notify_group_members_join(user_id, group_id, username)
        else:
            # For private groups, notify owner about join request
            print(f"SUCCESS: Join request sent to group '{group_data['group_name']}'. Waiting for approval.")
            conn.commit()  # Commit first
            notify_owner_join_request(user_id, group_id)
            
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not join group. {e}")
        return False
    finally:
        conn.close()

def leave_group(user_id):
    """Removes a user from their current group with notifications."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT username, current_group_id, is_group_owner FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data or not user_data['current_group_id']:
            print("ERROR: You are not in any group.")
            return False
            
        group_id = user_data['current_group_id']
        username = user_data['username']
        
        # Group owners must delete group instead
        if user_data['is_group_owner']:
            print("ERROR: You are the group owner. Delete the group instead of leaving.")
            return False
            
        # Get group info
        cursor.execute("SELECT group_name, member_count FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        
        # Remove from GroupMembers
        cursor.execute("DELETE FROM GroupMembers WHERE group_id = ? AND user_id = ?", (group_id, user_id))
        
        # Update user status
        cursor.execute("UPDATE Users SET current_group_id = NULL WHERE userid = ?", (user_id,))
        
        # Update group member count
        cursor.execute("UPDATE Groups SET member_count = member_count - 1 WHERE group_id = ?", (group_id,))
        
        conn.commit()
        print(f"SUCCESS: You left group '{group_data['group_name']}'.")
        
        # Notify remaining members (public groups only)
        notify_group_members_leave(user_id, group_id, username)
        
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not leave group. {e}")
        return False
    finally:
        conn.close()

def update_member_status(group_id, owner_id, member_user_id, new_status):
    """Updates member status in a group with notifications."""
    valid_statuses = ['Pending', 'Approved', 'Rejected', 'Blocked']
    
    if new_status not in valid_statuses:
        print(f"ERROR: Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return False
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify group ownership
        cursor.execute("SELECT owner_id, group_type FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return False
        
        if group_data['owner_id'] != owner_id:
            print("ERROR: Only group owner can update member status.")
            return False
        
        # Get member username for notifications
        cursor.execute("SELECT username FROM Users WHERE userid = ?", (member_user_id,))
        member_data = cursor.fetchone()
        if not member_data:
            print("ERROR: Member not found.")
            return False
        
        member_username = member_data['username']
        
        # Update member status
        cursor.execute("""UPDATE GroupMembers SET join_status = ? 
                         WHERE group_id = ? AND user_id = ?""", 
                      (new_status, group_id, member_user_id))
        
        if cursor.rowcount == 0:
            print("ERROR: Member not found in this group.")
            return False
        
        # Handle status changes
        if new_status == 'Approved':
            cursor.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", 
                          (group_id, member_user_id))
            cursor.execute("UPDATE Groups SET member_count = member_count + 1 WHERE group_id = ?", 
                          (group_id,))
            
            # Notify existing members about new approved member
            conn.commit()  # Commit first
            notify_group_members_join(member_user_id, group_id, member_username)
            
        elif new_status in ['Rejected', 'Blocked']:
            cursor.execute("SELECT current_group_id FROM Users WHERE userid = ?", (member_user_id,))
            user_data = cursor.fetchone()
            if user_data and user_data['current_group_id'] == group_id:
                cursor.execute("UPDATE Users SET current_group_id = NULL WHERE userid = ?", 
                              (member_user_id,))
                cursor.execute("UPDATE Groups SET member_count = member_count - 1 WHERE group_id = ?", 
                              (group_id,))
        
        conn.commit()
        print(f"SUCCESS: Member status updated to '{new_status}'.")
        
        # Notify the member about status change
        notify_user_status_update(member_user_id, group_id, new_status)
        
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not update member status. {e}")
        return False
    finally:
        conn.close()

def delete_group(group_id):
    """Deletes a group from the Groups table by its ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Update all users in this group
        cursor.execute("UPDATE Users SET current_group_id = NULL, is_group_owner = FALSE WHERE current_group_id = ?", (group_id,))
        
        # Delete the group (cascade deletes related records)
        cursor.execute("DELETE FROM Groups WHERE group_id = ?", (group_id,))
        if cursor.rowcount == 0:
            print(f"ERROR: No group found with ID '{group_id}'.")
            return False
        else:
            conn.commit()
            print(f"SUCCESS: Group with ID '{group_id}' deleted along with all related data.")
            return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not delete group. {e}")
        return False
    finally:
        conn.close()

def view_groups():
    """Displays all groups with their member information."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.group_id, g.group_name, g.group_type, g.group_description, 
                   u.username as owner_name, g.member_count, g.max_members, g.created_at
            FROM Groups g 
            JOIN Users u ON g.owner_id = u.userid
        """)
        groups = cursor.fetchall()
        
        if not groups:
            print("No groups found.")
            return
            
        print("\n--- Groups List ---")
        for group in groups:
            print(f"ID: {group['group_id']}")
            print(f"Name: {group['group_name']}")
            print(f"Type: {group['group_type']}")
            print(f"Owner: {group['owner_name']}")
            print(f"Description: {group['group_description'] or 'No description'}")
            print(f"Members: {group['member_count']}/{group['max_members']}")
            print(f"Created: {group['created_at']}")
            print("-" * 60)
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve groups. {e}")
    finally:
        conn.close()

def view_pending_requests(group_id, owner_id):
    """View pending join requests for a group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("SELECT owner_id FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return
        
        if group_data['owner_id'] != owner_id:
            print("ERROR: Only group owner can view pending requests.")
            return
        
        # Get pending requests
        cursor.execute("""
            SELECT gm.user_id, gm.username, gm.joined_at, u.email
            FROM GroupMembers gm
            JOIN Users u ON gm.user_id = u.userid
            WHERE gm.group_id = ? AND gm.join_status = 'Pending'
            ORDER BY gm.joined_at ASC
        """, (group_id,))
        
        requests = cursor.fetchall()
        
        if not requests:
            print("No pending requests for this group.")
            return
        
        print(f"\n--- Pending Join Requests ---")
        for req in requests:
            print(f"User: {req['username']} (ID: {req['user_id']})")
            print(f"Email: {req['email']}")
            print(f"Requested: {req['joined_at']}")
            print("-" * 40)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve pending requests. {e}")
    finally:
        conn.close()

# MESSAGING FUNCTIONS

def send_message(sender_id, group_id, message):
    """Sends a message to a group chat."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if sender exists and get username
        cursor.execute("SELECT username, current_group_id FROM Users WHERE userid = ?", (sender_id,))
        sender_data = cursor.fetchone()
        if not sender_data:
            print(f"ERROR: Sender with ID '{sender_id}' does not exist.")
            return False
            
        sender_username = sender_data['username']
        
        # Check if group exists
        cursor.execute("SELECT group_id FROM Groups WHERE group_id = ?", (group_id,))
        if not cursor.fetchone():
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return False
            
        # Check if sender is a member of the group
        cursor.execute("SELECT * FROM GroupMembers WHERE group_id = ? AND user_id = ? AND join_status = 'Approved'", 
                      (group_id, sender_id))
        if not cursor.fetchone():
            print("ERROR: You must be an approved member of the group to send messages.")
            return False
            
        # Insert the message
        conn.execute(
            "INSERT INTO GroupMessages (group_id, sender_id, sender_username, message) VALUES (?, ?, ?, ?)",
            (group_id, sender_id, sender_username, message)
        )
        
        conn.commit()
        print("SUCCESS: Message sent to group.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not send message. {e}")
        return False
    finally:
        conn.close()

def view_group_chat(group_id):
    """Displays recent messages from a group chat."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get group name
        cursor.execute("SELECT group_name FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return
            
        print(f"\n--- Chat for Group: {group_data['group_name']} ---")
        
        # Get recent messages
        cursor.execute("""
            SELECT sender_username, message, timestamp
            FROM GroupMessages 
            WHERE group_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (group_id,))
        
        messages = cursor.fetchall()
        messages = list(reversed(messages))  # Show in chronological order
        
        if not messages:
            print("No messages in this group yet.")
            return
            
        for msg in messages:
            timestamp = msg['timestamp'][:19]  # Remove microseconds
            print(f"[{timestamp}] {msg['sender_username']}: {msg['message']}")
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not view chat. {e}")
    finally:
        conn.close()

# MAIN FUNCTION

def main():
    """Main function to run the interactive command-line interface."""
    setup_database()
    
    while True:
        print("\n--- Travel Together DB Manager ---")
        print("1. Add User")
        print("2. Update User Profile") 
        print("3. Change Password")
        print("4. Delete User")
        print("5. View Users")
        print("6. Add Destination")
        print("7. View Destinations")
        print("8. Create Group with Itinerary")
        print("9. Join Group")
        print("10. Leave Group")
        print("11. Delete Group")
        print("12. View Groups")
        print("13. View Pending Requests")
        print("14. Update Member Status")
        print("15. Send Message")
        print("16. View Group Chat")
        print("17. View Notifications")
        print("18. View Unread Notifications")
        print("19. Mark Notification as Read")
        print("20. Mark All Notifications as Read")
        print("21. Exit")
        
        choice = input("Enter your choice (1-21): ").strip()
        
        if choice == '1':
            print("\n--- Add New User ---")
            username = input("Enter username: ").strip()
            
            while True:
                password = input("Enter password (min 6 chars, letters, numbers, special chars): ").strip()
                is_valid, message = validate_password(password)
                if is_valid:
                    print("Password accepted.")
                    break
                else:
                    print(f"ERROR: {message}")
                    retry = input("Try again? (y/n): ").strip().lower()
                    if retry != 'y':
                        break
            else:
                continue
            
            email = input("Enter email: ").strip()
            phone_no = input("Enter phone number (optional): ").strip() or None
            gender = input("Enter gender (Male/Female/Other, optional): ").strip() or None
            
            add_user(username, password, email, phone_no=phone_no, gender=gender)
            
        elif choice == '2':
            user_id = input("Enter your user ID: ").strip()
            print("Enter new values (leave blank to keep current):")
            phone_no = input("Phone number: ").strip() or None
            gender = input("Gender (Male/Female/Other): ").strip() or None
            marital_status = input("Marital status: ").strip() or None
            bio = input("Bio: ").strip() or None
            
            update_user_profile(user_id, phone_no=phone_no, gender=gender, 
                              marital_status=marital_status, bio=bio)
            
        elif choice == '3':
            user_id = input("Enter your user ID: ").strip()
            new_password = input("Enter new password: ").strip()
            update_password(user_id, new_password)
            
        elif choice == '4':
            user_id = input("Enter user ID to delete: ").strip()
            confirm = input("Are you sure? This will delete all user data (y/n): ").strip().lower()
            if confirm == 'y':
                delete_user(user_id)
                
        elif choice == '5':
            view_users()
            
        elif choice == '6':
            print("\n--- Add Destination ---")
            destination_name = input("Enter destination name: ").strip()
            state_province = input("Enter state/province: ").strip()
            country = input("Enter country: ").strip()
            description = input("Enter description (optional): ").strip() or None
            
            add_destination(destination_name, state_province, country, description=description)
            
        elif choice == '7':
            view_destinations()
            
        elif choice == '8':
            print("\n--- Create Group with Travel Chain ---")
            owner_id = input("Enter your userid: ").strip()
            group_name = input("Enter group name: ").strip()
            group_type = input("Enter group type (Public/Private): ").strip().capitalize()
            
            print("\nFirst, let's see available destinations:")
            view_destinations()
            
            print("\nNow enter the destinations for your travel chain:")
            destination_ids = []
            while True:
                dest_id = input(f"Enter destination ID for stop {len(destination_ids) + 1} (or 'done' to finish): ").strip()
                if dest_id.lower() == 'done':
                    break
                if dest_id:
                    destination_ids.append(dest_id)
                    
            if not destination_ids:
                print("ERROR: At least one destination is required.")
                continue
                
            group_description = input("Enter group description (optional): ").strip() or None
            
            create_group_with_itinerary(
                owner_id, group_name, group_type, destination_ids,
                group_description=group_description
            )
            
        elif choice == '9':
            user_id = input("Enter your userid: ").strip()
            group_id = input("Enter group ID to join: ").strip()
            join_group(user_id, group_id)
            
        elif choice == '10':
            user_id = input("Enter your userid: ").strip()
            leave_group(user_id)
            
        elif choice == '11':
            group_id = input("Enter group ID to delete: ").strip()
            confirm = input("Are you sure? This will delete all group data (y/n): ").strip().lower()
            if confirm == 'y':
                delete_group(group_id)
                
        elif choice == '12':
            view_groups()
            
        elif choice == '13':
            owner_id = input("Enter your user ID: ").strip()
            group_id = input("Enter your group ID: ").strip()
            view_pending_requests(group_id, owner_id)
            
        elif choice == '14':
            owner_id = input("Enter your user ID: ").strip()
            group_id = input("Enter your group ID: ").strip()
            member_user_id = input("Enter member's user ID: ").strip()
            new_status = input("Enter new status (Pending/Approved/Rejected/Blocked): ").strip()
            update_member_status(group_id, owner_id, member_user_id, new_status)
            
        elif choice == '15':
            sender_id = input("Enter your userid: ").strip()
            group_id = input("Enter the group_id: ").strip()
            message = input("Enter your message: ").strip()
            send_message(sender_id, group_id, message)
            
        elif choice == '16':
            group_id = input("Enter the group_id: ").strip()
            view_group_chat(group_id)
            
        elif choice == '17':
            user_id = input("Enter your user ID: ").strip()
            view_notifications(user_id)
            
        elif choice == '18':
            user_id = input("Enter your user ID: ").strip()
            unread_count = get_unread_count(user_id)
            print(f"You have {unread_count} unread notifications.")
            if unread_count > 0:
                view_notifications(user_id, unread_only=True)
            
        elif choice == '19':
            user_id = input("Enter your user ID: ").strip()
            notification_id = input("Enter notification ID to mark as read: ").strip()
            try:
                notification_id = int(notification_id)
                mark_notification_read(notification_id, user_id)
            except ValueError:
                print("ERROR: Invalid notification ID. Must be a number.")
                
        elif choice == '20':
            user_id = input("Enter your user ID: ").strip()
            mark_all_notifications_read(user_id)
            
        elif choice == '21':
            print("Exiting... Have a great day!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
