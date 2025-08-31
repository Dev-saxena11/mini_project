import sqlite3
import uuid
import re
from datetime import datetime
import random

# --- UTILITY FUNCTIONS ---

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

# --- DATABASE SETUP ---

def setup_database():
    """Creates all database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        userid TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone_no TEXT UNIQUE,
        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
        marital_status TEXT CHECK(marital_status IN ('Single', 'Married', 'Divorced', 'Widowed')),
        bio TEXT,
        current_group_id TEXT,
        is_group_owner BOOLEAN DEFAULT FALSE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_group_id) REFERENCES Groups (group_id) ON DELETE SET NULL
    );
    """)

    # Destinations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Destinations (
        destination_id TEXT PRIMARY KEY,
        destination_name TEXT UNIQUE NOT NULL,
        country TEXT NOT NULL
    );
    """)

    # Groups table - NOW WITH DESTINATION LINK
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Groups (
        group_id TEXT PRIMARY KEY,
        group_name TEXT NOT NULL,
        group_description TEXT,
        group_type TEXT NOT NULL CHECK(group_type IN ('Public', 'Private')),
        owner_id TEXT NOT NULL,
        destination_id TEXT,
        member_count INTEGER DEFAULT 1,
        max_members INTEGER DEFAULT 50,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES Users (userid) ON DELETE CASCADE,
        FOREIGN KEY (destination_id) REFERENCES Destinations (destination_id) ON DELETE SET NULL
    );
    """)

    # GroupMembers table
    cursor.execute("""
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
    """)

    # GroupMessages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GroupMessages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES Groups (group_id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES Users (userid) ON DELETE CASCADE
    );
    """)
    
    print("Database tables checked/created.")
    conn.commit()
    conn.close()

# --- USER MANAGEMENT ---

def add_user(username, password, email, **kwargs):
    is_valid, message = validate_password(password)
    if not is_valid: return None
    if not validate_email(email): return None

    user_id = generate_id()
    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO Users (userid, username, password, email, phone_no, gender, marital_status, bio) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, password, email, kwargs.get('phone_no'), 
             kwargs.get('gender'), kwargs.get('marital_status'), kwargs.get('bio'))
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

# --- DESTINATION MANAGEMENT ---

def get_all_destinations():
    """Fetches all destinations to populate a dropdown."""
    conn = get_db_connection()
    destinations = conn.execute("SELECT * FROM Destinations ORDER BY destination_name ASC").fetchall()
    conn.close()
    return destinations

def find_or_create_destination(name):
    """
    Finds a destination by name. If it doesn't exist, creates it.
    Returns the destination_id.
    """
    if not name or not name.strip():
        return None
        
    clean_name = name.strip().title()
    conn = get_db_connection()
    
    try:
        # Check if destination exists
        cursor = conn.cursor()
        cursor.execute("SELECT destination_id FROM Destinations WHERE destination_name = ?", (clean_name,))
        result = cursor.fetchone()
        
        if result:
            return result['destination_id']
        else:
            # Create it if it doesn't exist
            new_id = generate_id()
            # For simplicity, we'll add a placeholder country for now
            cursor.execute(
                "INSERT INTO Destinations (destination_id, destination_name, country) VALUES (?, ?, ?)",
                (new_id, clean_name, "Unknown")
            )
            conn.commit()
            return new_id
    except sqlite3.Error as e:
        print(f"Database error in find_or_create_destination: {e}")
        return None
    finally:
        conn.close()


# --- GROUP MANAGEMENT ---

def add_group(group_name, group_type, owner_id, destination_id, group_description=None):
    """Creates a new group, making the creator the owner."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, current_group_id FROM Users WHERE userid = ?", (owner_id,))
        user = cursor.fetchone()

        if not user or user['current_group_id']:
            return None

        group_id = generate_id()
        owner_username = user['username']

        # Create the group
        cursor.execute(
            "INSERT INTO Groups (group_id, group_name, group_type, owner_id, destination_id, group_description) VALUES (?, ?, ?, ?, ?, ?)",
            (group_id, group_name, group_type, owner_id, destination_id, group_description)
        )
        # Add owner to members table
        cursor.execute(
            "INSERT INTO GroupMembers (member_id, group_id, user_id, username, role) VALUES (?, ?, ?, ?, ?)",
            (generate_id(), group_id, owner_id, owner_username, 'Owner')
        )
        # Update user's status
        cursor.execute(
            "UPDATE Users SET current_group_id = ?, is_group_owner = TRUE WHERE userid = ?",
            (group_id, owner_id)
        )
        conn.commit()
        return group_id
    except sqlite3.Error:
        return None
    finally:
        conn.close()

def join_group(user_id, group_id):
    """Allows a user to join a public group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, current_group_id FROM Users WHERE userid = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or user['current_group_id']: return False

        cursor.execute("SELECT member_count, max_members FROM Groups WHERE group_id = ?", (group_id,))
        group = cursor.fetchone()
        if not group or group['member_count'] >= group['max_members']: return False

        cursor.execute(
            "INSERT INTO GroupMembers (member_id, group_id, user_id, username) VALUES (?, ?, ?, ?)",
            (generate_id(), group_id, user_id, user['username'])
        )
        cursor.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", (group_id, user_id))
        cursor.execute("UPDATE Groups SET member_count = member_count + 1 WHERE group_id = ?", (group_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def leave_group(user_id):
    """Removes a user from their current group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT current_group_id, is_group_owner FROM Users WHERE userid = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not user['current_group_id'] or user['is_group_owner']:
            return False

        group_id = user['current_group_id']
        cursor.execute("DELETE FROM GroupMembers WHERE user_id = ? AND group_id = ?", (user_id, group_id))
        cursor.execute("UPDATE Users SET current_group_id = NULL WHERE userid = ?", (user_id,))
        cursor.execute("UPDATE Groups SET member_count = member_count - 1 WHERE group_id = ?", (group_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def delete_group(group_id):
    """Deletes a group and all associated data."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET current_group_id = NULL, is_group_owner = FALSE WHERE current_group_id = ?", (group_id,))
        cursor.execute("DELETE FROM Groups WHERE group_id = ?", (group_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_user_group(user_id):
    """Fetches the full details of a user's current group."""
    conn = get_db_connection()
    group = conn.execute("""
        SELECT g.*, d.destination_name FROM Groups g 
        LEFT JOIN Destinations d ON g.destination_id = d.destination_id
        JOIN Users u ON g.group_id = u.current_group_id 
        WHERE u.userid = ?
    """, (user_id,)).fetchone()
    conn.close()
    return group

def get_group_members(group_id):
    """Fetches details of all members in a given group."""
    conn = get_db_connection()
    members = conn.execute("""
        SELECT u.username, u.email, u.phone_no, gm.role, gm.joined_at
        FROM GroupMembers gm
        JOIN Users u ON gm.user_id = u.userid
        WHERE gm.group_id = ?
        ORDER BY gm.role, gm.joined_at
    """, (group_id,)).fetchall()
    conn.close()
    return members

# --- MESSAGING ---

def add_group_message(group_id, sender_id, message):
    """Adds a message to a group's chat."""
    conn = get_db_connection()
    try:
        is_member = conn.execute(
            "SELECT 1 FROM GroupMembers WHERE group_id = ? AND user_id = ?",
            (group_id, sender_id)
        ).fetchone()
        
        if not is_member: return False

        conn.execute(
            "INSERT INTO GroupMessages (group_id, sender_id, message) VALUES (?, ?, ?)",
            (group_id, sender_id, message)
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()