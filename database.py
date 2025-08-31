import sqlite3
import uuid
import re

def generate_id():
    """Generates a unique ID using UUID4."""
    return uuid.uuid4().hex

def validate_password(password):
    """
    Validates password strength.
    Requirements: At least 6 characters, contains numbers, alphabets, and special characters.
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter."
    
    # Check for at least one number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character."
    
    return True, "Password is strong."

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

    # Users table with current_group_id column
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
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_group_id) REFERENCES Groups (group_id) ON DELETE SET NULL
    );
    """
    cursor.execute(create_users_table_query)

    # Groups table with member_count and member_list
    create_groups_table_query = """
    CREATE TABLE IF NOT EXISTS Groups (
        group_id TEXT PRIMARY KEY,
        group_name TEXT NOT NULL,
        group_description TEXT,
        group_type TEXT NOT NULL CHECK(group_type IN ('Public', 'Private')),
        owner_id TEXT NOT NULL,
        member_count INTEGER DEFAULT 1,
        member_list TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES Users (userid) ON DELETE CASCADE
    );
    """
    cursor.execute(create_groups_table_query)

    # GroupMembers table for detailed membership tracking
    create_group_members_table_query = """
    CREATE TABLE IF NOT EXISTS GroupMembers (
        member_id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'Member' CHECK(role IN ('Owner', 'Admin', 'Member')),
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users (userid) ON DELETE CASCADE,
        UNIQUE(group_id, user_id)
    );
    """
    cursor.execute(create_group_members_table_query)

    # GroupMessages table for storing group chats
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

    print("Database and tables are ready.")
    conn.commit()
    conn.close()

def add_user(username, password, email, **kwargs):
    """Adds a new user to the Users table with a generated ID."""
    # Validate password strength
    is_valid, message = validate_password(password)
    if not is_valid:
        print(f"ERROR: {message}")
        return None

    user_id = generate_id()
    conn = get_db_connection()
    
    try:
        conn.execute(
            """INSERT INTO Users (userid, username, password, email, phone_no, gender, 
               marital_status, profile_picture, bio, current_group_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, password, email, kwargs.get('phone_no'), 
             kwargs.get('gender'), kwargs.get('marital_status'), 
             kwargs.get('profile_picture'), kwargs.get('bio'), None)
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

def delete_user(user_id):
    """Deletes a user from the Users table by their ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # First, remove user from any groups they're in
        cursor.execute("SELECT current_group_id FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data and user_data['current_group_id']:
            leave_group(user_id)
        
        # Delete the user (messages will be deleted due to CASCADE)
        cursor.execute("DELETE FROM Users WHERE userid = ?", (user_id,))
        if cursor.rowcount == 0:
            print(f"ERROR: No user found with ID '{user_id}'.")
        else:
            conn.commit()
            print(f"SUCCESS: User with ID '{user_id}' deleted.")
    except sqlite3.Error as e:
        print(f"ERROR: Could not delete user. {e}")
    finally:
        conn.close()

def add_group(group_name, group_type, owner_id, group_description=None):
    """Adds a new group to the Groups table with a generated ID."""
    if group_type not in ['Public', 'Private']:
        print("ERROR: Group type must be 'Public' or 'Private'.")
        return None

    group_id = generate_id()
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if owner exists and get username
        cursor.execute("SELECT userid, username FROM Users WHERE userid = ?", (owner_id,))
        owner_data = cursor.fetchone()
        if not owner_data:
            print(f"ERROR: Owner with ID '{owner_id}' does not exist.")
            return None

        owner_username = owner_data['username']
        
        # Create the group
        conn.execute(
            """INSERT INTO Groups (group_id, group_name, group_description, group_type, 
               owner_id, member_count, member_list) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (group_id, group_name, group_description, group_type, owner_id, 1, owner_username)
        )
        
        # Add owner to GroupMembers
        member_id = generate_id()
        conn.execute(
            """INSERT INTO GroupMembers (member_id, group_id, user_id, username, role) 
               VALUES (?, ?, ?, ?, 'Owner')""",
            (member_id, group_id, owner_id, owner_username)
        )
        
        # Update owner's current_group_id
        conn.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", (group_id, owner_id))
        
        conn.commit()
        print(f"SUCCESS: Group '{group_name}' added with ID: {group_id}")
        print(f"Owner '{owner_username}' automatically joined the group.")
        return group_id
    except sqlite3.Error as e:
        print(f"ERROR: Could not add group. {e}")
        return None
    finally:
        conn.close()

def delete_group(group_id):
    """Deletes a group from the Groups table by its ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Update all users in this group to have no current group
        cursor.execute("UPDATE Users SET current_group_id = NULL WHERE current_group_id = ?", (group_id,))
        
        # Delete the group (GroupMembers and GroupMessages will be deleted due to CASCADE)
        cursor.execute("DELETE FROM Groups WHERE group_id = ?", (group_id,))
        if cursor.rowcount == 0:
            print(f"ERROR: No group found with ID '{group_id}'.")
        else:
            conn.commit()
            print(f"SUCCESS: Group with ID '{group_id}' deleted along with all messages.")
    except sqlite3.Error as e:
        print(f"ERROR: Could not delete group. {e}")
    finally:
        conn.close()

def join_group(user_id, group_id):
    """Adds a user to a group and updates all related tables."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT userid, username, current_group_id FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            print(f"ERROR: User with ID '{user_id}' does not exist.")
            return False
            
        username = user_data['username']
        current_group = user_data['current_group_id']
        
        # Check if group exists
        cursor.execute("SELECT group_id, group_name, member_count, member_list FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return False
            
        # Check if user is already in this group
        if current_group == group_id:
            print("ERROR: User is already a member of this group.")
            return False
        
        # If user is in another group, leave it first
        if current_group:
            leave_group(user_id)
            
        # Add user to GroupMembers
        member_id = generate_id()
        conn.execute(
            "INSERT INTO GroupMembers (member_id, group_id, user_id, username) VALUES (?, ?, ?, ?)",
            (member_id, group_id, user_id, username)
        )
        
        # Update user's current_group_id
        conn.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", (group_id, user_id))
        
        # Update group's member_count and member_list
        new_count = group_data['member_count'] + 1
        current_members = group_data['member_list'] or ""
        new_member_list = f"{current_members}, {username}" if current_members else username
        
        conn.execute(
            "UPDATE Groups SET member_count = ?, member_list = ? WHERE group_id = ?",
            (new_count, new_member_list, group_id)
        )
        
        conn.commit()
        print(f"SUCCESS: User '{username}' joined group '{group_data['group_name']}'.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not join group. {e}")
        return False
    finally:
        conn.close()

def leave_group(user_id):
    """Removes a user from their current group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get user and current group info
        cursor.execute("SELECT username, current_group_id FROM Users WHERE userid = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data or not user_data['current_group_id']:
            print("ERROR: User is not in any group.")
            return False
            
        username = user_data['username']
        group_id = user_data['current_group_id']
        
        # Get group info
        cursor.execute("SELECT group_name, member_count, member_list FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        
        # Remove from GroupMembers
        cursor.execute("DELETE FROM GroupMembers WHERE group_id = ? AND user_id = ?", (group_id, user_id))
        
        # Update user's current_group_id to NULL
        conn.execute("UPDATE Users SET current_group_id = NULL WHERE userid = ?", (user_id,))
        
        # Update group's member_count and member_list
        new_count = group_data['member_count'] - 1
        current_members = group_data['member_list'] or ""
        member_list = [member.strip() for member in current_members.split(',') if member.strip()]
        if username in member_list:
            member_list.remove(username)
        new_member_list = ', '.join(member_list)
        
        conn.execute(
            "UPDATE Groups SET member_count = ?, member_list = ? WHERE group_id = ?",
            (new_count, new_member_list, group_id)
        )
        
        conn.commit()
        print(f"SUCCESS: User '{username}' left group '{group_data['group_name']}'.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not leave group. {e}")
        return False
    finally:
        conn.close()

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
        cursor.execute("SELECT * FROM GroupMembers WHERE group_id = ? AND user_id = ?", (group_id, sender_id))
        if not cursor.fetchone():
            print("ERROR: You must be a member of the group to send messages.")
            return False
            
        # Insert the message
        conn.execute(
            "INSERT INTO GroupMessages (group_id, sender_id, sender_username, message) VALUES (?, ?, ?, ?)",
            (group_id, sender_id, sender_username, message)
        )
        
        conn.commit()
        print(f"SUCCESS: Message sent to group.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not send message. {e}")
        return False
    finally:
        conn.close()

def get_group_messages(group_id, limit=50):
    """Retrieves recent messages from a group chat."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, sender_username, message, timestamp
            FROM GroupMessages 
            WHERE group_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (group_id, limit))
        
        messages = cursor.fetchall()
        return list(reversed(messages))  # Return in chronological order
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve messages. {e}")
        return []
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
        
        messages = get_group_messages(group_id, 20)  # Last 20 messages
        
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

def view_groups():
    """Displays all groups with their member information."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.group_id, g.group_name, g.group_type, g.group_description, 
                   u.username as owner_name, g.member_count, g.member_list, g.created_at
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
            print(f"Member Count: {group['member_count']}")
            print(f"Members: {group['member_list'] or 'No members'}")
            print(f"Created: {group['created_at']}")
            print("-" * 60)
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve groups. {e}")
    finally:
        conn.close()

def get_group_members(group_id):
    """Returns all members of a specific group (for frontend API)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gm.user_id, gm.username, gm.role, gm.joined_at,
                   u.email, u.phone_no
            FROM GroupMembers gm
            JOIN Users u ON gm.user_id = u.userid
            WHERE gm.group_id = ?
            ORDER BY gm.role DESC, gm.joined_at ASC
        """, (group_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"ERROR: Could not get group members. {e}")
        return []
    finally:
        conn.close()

def get_user_group(user_id):
    """Returns the current group of a user (for frontend API)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.group_id, g.group_name, g.group_type, g.group_description,
                   g.member_count, g.member_list
            FROM Users u
            JOIN Groups g ON u.current_group_id = g.group_id
            WHERE u.userid = ?
        """, (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"ERROR: Could not get user group. {e}")
        return None
    finally:
        conn.close()

def main():
    """Main function to run the interactive command-line interface."""
    setup_database()
    
    while True:
        print("\n--- Travel Together DB Manager ---")
        print("1. Add User")
        print("2. Delete User")
        print("3. View Users")
        print("4. Add Group")
        print("5. Delete Group")
        print("6. View Groups")
        print("7. Join Group")
        print("8. Leave Group")
        print("9. Send Message")
        print("10. View Group Chat")
        print("11. Exit")
        
        choice = input("Enter your choice (1-11): ").strip()
        
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
            marital_status = input("Enter marital status (Single/Married/Divorced/Widowed, optional): ").strip() or None
            bio = input("Enter bio (optional): ").strip() or None
            
            add_user(username, password, email, phone_no=phone_no, gender=gender, 
                    marital_status=marital_status, bio=bio)
                    
        elif choice == '2':
            user_id = input("Enter the userid to delete: ").strip()
            delete_user(user_id)
            
        elif choice == '3':
            view_users()
            
        elif choice == '4':
            print("\n--- Add New Group ---")
            group_name = input("Enter group name: ").strip()
            group_type = input("Enter group type (Public/Private): ").strip().capitalize()
            owner_id = input("Enter the owner's userid: ").strip()
            group_description = input("Enter group description (optional): ").strip() or None
            add_group(group_name, group_type, owner_id, group_description)
            
        elif choice == '5':
            group_id = input("Enter the group_id to delete: ").strip()
            delete_group(group_id)
            
        elif choice == '6':
            view_groups()
            
        elif choice == '7':
            print("\n--- Join Group ---")
            user_id = input("Enter your userid: ").strip()
            group_id = input("Enter the group_id to join: ").strip()
            join_group(user_id, group_id)
            
        elif choice == '8':
            print("\n--- Leave Group ---")
            user_id = input("Enter your userid: ").strip()
            leave_group(user_id)
            
        elif choice == '9':
            print("\n--- Send Message ---")
            sender_id = input("Enter your userid: ").strip()
            group_id = input("Enter the group_id: ").strip()
            message = input("Enter your message: ").strip()
            send_message(sender_id, group_id, message)
            
        elif choice == '10':
            print("\n--- View Group Chat ---")
            group_id = input("Enter the group_id: ").strip()
            view_group_chat(group_id)
            
        elif choice == '11':
            print("Exiting... Have a great day!")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1-11.")

if __name__ == "__main__":
    main()
