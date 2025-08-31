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
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter."
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    
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

    # Groups table (main travel group)
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

    # Destinations table (places that can be visited)
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

    # TravelItinerary table (links groups to multiple destinations in sequence)
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

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_travel_itinerary_group ON TravelItinerary(group_id, visit_order);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tourist_spots_destination ON TouristSpots(destination_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_messages_group_timestamp ON GroupMessages(group_id, timestamp);")

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

def create_group_with_itinerary(owner_id, group_name, group_type, destination_ids, **kwargs):
    """Creates a new group with a travel itinerary (chain of destinations)."""
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if user exists and can create group
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

def view_group_itinerary(group_id):
    """Display the travel itinerary for a group."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get group info
        cursor.execute("SELECT group_name, group_description FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return
            
        print(f"\n--- Travel Itinerary for '{group_data['group_name']}' ---")
        if group_data['group_description']:
            print(f"Description: {group_data['group_description']}")
        
        # Get itinerary
        cursor.execute("""
            SELECT ti.visit_order, d.destination_name, d.state_province, d.country,
                   ti.duration_days, ti.planned_arrival_date, ti.planned_departure_date,
                   ti.estimated_cost, ti.accommodation_type, ti.transport_to_next, ti.notes
            FROM TravelItinerary ti
            JOIN Destinations d ON ti.destination_id = d.destination_id
            WHERE ti.group_id = ?
            ORDER BY ti.visit_order
        """, (group_id,))
        
        itinerary = cursor.fetchall()
        
        if not itinerary:
            print("No itinerary found for this group.")
            return
            
        print(f"\nTravel Chain ({len(itinerary)} destinations):")
        print("=" * 60)
        
        for stop in itinerary:
            print(f"Stop {stop['visit_order']}: {stop['destination_name']}")
            print(f"   Location: {stop['state_province']}, {stop['country']}")
            print(f"   Duration: {stop['duration_days']} day(s)")
            if stop['planned_arrival_date']:
                print(f"   Arrival: {stop['planned_arrival_date']}")
            if stop['planned_departure_date']:
                print(f"   Departure: {stop['planned_departure_date']}")
            if stop['estimated_cost']:
                print(f"   Estimated Cost: {stop['estimated_cost']}")
            if stop['accommodation_type']:
                print(f"   Accommodation: {stop['accommodation_type']}")
            if stop['transport_to_next']:
                print(f"   Transport to Next: {stop['transport_to_next']}")
            if stop['notes']:
                print(f"   Notes: {stop['notes']}")
            
            if stop['visit_order'] < len(itinerary):
                print("   ↓")
            print("-" * 40)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not retrieve itinerary. {e}")
    finally:
        conn.close()

def add_destination_to_itinerary(group_id, destination_id, owner_id, **kwargs):
    """Add a new destination to existing group's itinerary."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify group ownership
        cursor.execute("SELECT owner_id FROM Groups WHERE group_id = ?", (group_id,))
        group_data = cursor.fetchone()
        if not group_data:
            print(f"ERROR: Group with ID '{group_id}' does not exist.")
            return False
            
        if group_data['owner_id'] != owner_id:
            print("ERROR: Only group owner can modify the itinerary.")
            return False
            
        # Check if destination exists
        cursor.execute("SELECT destination_name FROM Destinations WHERE destination_id = ?", (destination_id,))
        dest_data = cursor.fetchone()
        if not dest_data:
            print(f"ERROR: Destination with ID '{destination_id}' does not exist.")
            return False
            
        # Check if destination is already in itinerary
        cursor.execute("SELECT * FROM TravelItinerary WHERE group_id = ? AND destination_id = ?", 
                      (group_id, destination_id))
        if cursor.fetchone():
            print("ERROR: This destination is already in the itinerary.")
            return False
            
        # Get next order number
        cursor.execute("SELECT COALESCE(MAX(visit_order), 0) + 1 FROM TravelItinerary WHERE group_id = ?", (group_id,))
        next_order = cursor.fetchone()[0]
        
        # Add to itinerary
        itinerary_id = generate_id()
        conn.execute(
            """INSERT INTO TravelItinerary (itinerary_id, group_id, destination_id, visit_order,
               duration_days, estimated_cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (itinerary_id, group_id, destination_id, next_order,
             kwargs.get('duration_days', 2), kwargs.get('estimated_cost'),
             kwargs.get('notes', f"Added destination {next_order}"))
        )
        
        conn.commit()
        print(f"SUCCESS: '{dest_data['destination_name']}' added to itinerary as stop {next_order}.")
        return True
    except sqlite3.Error as e:
        print(f"ERROR: Could not add destination to itinerary. {e}")
        return False
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

def search_groups_by_destination(destination_name=None):
    """Search for groups traveling to a specific destination."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if destination_name:
            cursor.execute("""
                SELECT DISTINCT g.group_id, g.group_name, g.group_type, g.member_count, g.max_members,
                       COUNT(ti.destination_id) as destination_count,
                       u.username as owner_name
                FROM Groups g
                JOIN TravelItinerary ti ON g.group_id = ti.group_id
                JOIN Destinations d ON ti.destination_id = d.destination_id
                JOIN Users u ON g.owner_id = u.userid
                WHERE d.destination_name LIKE ?
                GROUP BY g.group_id
                ORDER BY g.created_at DESC
            """, (f"%{destination_name}%",))
        else:
            cursor.execute("""
                SELECT g.group_id, g.group_name, g.group_type, g.member_count, g.max_members,
                       COUNT(ti.destination_id) as destination_count,
                       u.username as owner_name
                FROM Groups g
                LEFT JOIN TravelItinerary ti ON g.group_id = ti.group_id
                JOIN Users u ON g.owner_id = u.userid
                GROUP BY g.group_id
                ORDER BY g.created_at DESC
            """)
            
        groups = cursor.fetchall()
        
        if not groups:
            print("No groups found.")
            return
            
        search_text = f" for '{destination_name}'" if destination_name else ""
        print(f"\n--- Groups{search_text} ---")
        
        for group in groups:
            print(f"Group: {group['group_name']} (ID: {group['group_id']})")
            print(f"Type: {group['group_type']}")
            print(f"Owner: {group['owner_name']}")
            print(f"Members: {group['member_count']}/{group['max_members']}")
            print(f"Destinations in Itinerary: {group['destination_count']}")
            print("-" * 50)
            
    except sqlite3.Error as e:
        print(f"ERROR: Could not search groups. {e}")
    finally:
        conn.close()

def main():
    """Main function to run the interactive command-line interface."""
    setup_database()
    
    while True:
        print("\n--- Travel Together DB Manager ---")
        print("1. Add User")
        print("2. Add Destination")
        print("3. Create Group with Travel Chain")
        print("4. View Group Itinerary")
        print("5. Add Destination to Itinerary")
        print("6. View All Destinations")
        print("7. Search Groups by Destination")
        print("8. Exit")
        
        choice = input("Enter your choice (1-8): ").strip()
        
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
            add_user(username, password, email)
            
        elif choice == '2':
            print("\n--- Add Destination ---")
            destination_name = input("Enter destination name: ").strip()
            state_province = input("Enter state/province: ").strip()
            country = input("Enter country: ").strip()
            description = input("Enter description (optional): ").strip() or None
            
            add_destination(destination_name, state_province, country, description=description)
            
        elif choice == '3':
            print("\n--- Create Group with Travel Chain ---")
            owner_id = input("Enter your userid: ").strip()
            group_name = input("Enter group name: ").strip()
            group_type = input("Enter group type (Public/Private): ").strip().capitalize()
            
            # Get destinations for the travel chain
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
            total_days = input("Enter total trip duration in days (optional): ").strip()
            total_days = int(total_days) if total_days.isdigit() else None
            
            create_group_with_itinerary(
                owner_id, group_name, group_type, destination_ids,
                group_description=group_description, total_duration_days=total_days
            )
            
        elif choice == '4':
            group_id = input("Enter group ID to view itinerary: ").strip()
            view_group_itinerary(group_id)
            
        elif choice == '5':
            print("\n--- Add Destination to Existing Itinerary ---")
            owner_id = input("Enter your userid: ").strip()
            group_id = input("Enter your group ID: ").strip()
            destination_id = input("Enter destination ID to add: ").strip()
            duration = input("Enter duration in days (default 2): ").strip()
            duration = int(duration) if duration.isdigit() else 2
            notes = input("Enter notes (optional): ").strip() or None
            
            add_destination_to_itinerary(group_id, destination_id, owner_id, 
                                       duration_days=duration, notes=notes)
            
        elif choice == '6':
            view_destinations()
            
        elif choice == '7':
            destination_name = input("Enter destination name to search (or press Enter for all groups): ").strip()
            search_groups_by_destination(destination_name if destination_name else None)
            
        elif choice == '8':
            print("Exiting... Have a great day!")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1-8.")

if __name__ == "__main__":
    main()
