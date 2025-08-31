# sample_data_generator.py - Travel Together Sample Data Generator
import sqlite3
import uuid
import re
from datetime import datetime, timedelta
import random

def generate_id():
    """Generates a unique ID using UUID4."""
    return uuid.uuid4().hex

def validate_password(password):
    """Validates password strength."""
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

    print("Database tables created successfully.")
    conn.commit()
    conn.close()

def insert_sample_data():
    """Inserts comprehensive sample data into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Sample Users Data
        users_data = [
            ('alice_wanderer', 'Pass@123', 'alice.wanderer@email.com', '9876543210', 'Female', 'Single', 'Adventure seeker from Mumbai'),
            ('bob_explorer', 'Travel@456', 'bob.explorer@email.com', '9876543211', 'Male', 'Married', 'Nature lover and photographer'),
            ('carol_backpacker', 'Journey@789', 'carol.backpack@email.com', '9876543212', 'Female', 'Single', 'Solo traveler and blogger'),
            ('david_trekker', 'Mountain@321', 'david.trekker@email.com', '9876543213', 'Male', 'Single', 'Mountain enthusiast from Delhi'),
            ('eva_foodie', 'Taste@654', 'eva.foodie@email.com', '9876543214', 'Female', 'Married', 'Food blogger and culture explorer'),
            ('frank_pilot', 'Flying@987', 'frank.pilot@email.com', '9876543215', 'Male', 'Divorced', 'Pilot who loves exotic destinations'),
            ('grace_artist', 'Color@147', 'grace.artist@email.com', '9876543216', 'Female', 'Single', 'Artist seeking inspiration worldwide'),
            ('henry_historian', 'History@258', 'henry.historian@email.com', '9876543217', 'Male', 'Married', 'History professor and heritage lover'),
            ('irene_yogini', 'Zen@369', 'irene.yogini@email.com', '9876543218', 'Female', 'Single', 'Yoga instructor and spiritual traveler'),
            ('jack_swimmer', 'Ocean@741', 'jack.swimmer@email.com', '9876543219', 'Male', 'Single', 'Marine biologist and beach lover'),
            ('kate_runner', 'Marathon@852', 'kate.runner@email.com', '9876543220', 'Female', 'Married', 'Marathon runner exploring cities'),
            ('liam_chef', 'Spice@963', 'liam.chef@email.com', '9876543221', 'Male', 'Single', 'Chef discovering global cuisines'),
            ('mia_dancer', 'Rhythm@159', 'mia.dancer@email.com', '9876543222', 'Female', 'Single', 'Dancer exploring cultural festivals'),
            ('noah_writer', 'Story@753', 'noah.writer@email.com', '9876543223', 'Male', 'Married', 'Travel writer and storyteller'),
            ('olivia_surfer', 'Wave@486', 'olivia.surfer@email.com', '9876543224', 'Female', 'Single', 'Professional surfer and beach guide')
        ]

        user_ids = []
        for username, password, email, phone, gender, marital_status, bio in users_data:
            user_id = generate_id()
            user_ids.append(user_id)
            cursor.execute(
                """INSERT INTO Users (userid, username, password, email, phone_no, gender, 
                   marital_status, bio, current_group_id, is_group_owner) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, password, email, phone, gender, marital_status, bio, None, False)
            )

        # Sample Destinations Data
        destinations_data = [
            ('Goa', 'Goa', 'India', 'Beautiful beaches and Portuguese heritage', 'November to February', 'Easy', '$30-50', 'Beach activities, Water sports, Heritage tours', 15.2993, 74.1240),
            ('Kerala Backwaters', 'Kerala', 'India', 'Serene backwaters and houseboat experiences', 'October to March', 'Easy', '$25-40', 'Houseboat cruises, Ayurveda, Spice plantations', 9.9312, 76.2673),
            ('Rajasthan Golden Triangle', 'Rajasthan', 'India', 'Royal palaces and desert landscapes', 'October to March', 'Moderate', '$20-35', 'Palace tours, Camel safari, Cultural shows', 26.9124, 75.7873),
            ('Himachal Pradesh', 'Himachal Pradesh', 'India', 'Snow-capped mountains and hill stations', 'April to October', 'Moderate', '$15-30', 'Trekking, Adventure sports, Mountain views', 31.1048, 77.1734),
            ('Uttarakhand Hills', 'Uttarakhand', 'India', 'Spiritual destinations and natural beauty', 'March to June, September to November', 'Moderate', '$20-35', 'Pilgrimage, Trekking, Yoga retreats', 30.0668, 79.0193),
            ('Ladakh', 'Ladakh', 'India', 'High altitude desert and Buddhist monasteries', 'June to September', 'Hard', '$25-40', 'High altitude trekking, Monasteries, Photography', 34.1526, 77.5771),
            ('Andaman Islands', 'Andaman and Nicobar', 'India', 'Pristine beaches and coral reefs', 'November to April', 'Easy', '$40-60', 'Scuba diving, Snorkeling, Beach relaxation', 11.7401, 92.6586),
            ('Tamil Nadu Temples', 'Tamil Nadu', 'India', 'Ancient temples and rich culture', 'November to March', 'Easy', '$15-25', 'Temple visits, Classical music, Traditional cuisine', 11.1271, 78.6569),
            ('Karnataka Heritage', 'Karnataka', 'India', 'Historical sites and coffee plantations', 'October to March', 'Moderate', '$20-30', 'Heritage tours, Coffee plantation visits, Wildlife', 15.3173, 75.7139),
            ('Maharashtra Caves', 'Maharashtra', 'India', 'Ancient rock-cut caves and wine tours', 'October to March', 'Easy', '$25-35', 'Cave exploration, Wine tasting, Hill stations', 19.7515, 75.7139),
            ('Northeast India', 'Assam', 'India', 'Unexplored beauty and tribal culture', 'October to April', 'Moderate', '$20-30', 'Tea gardens, Wildlife, Tribal culture', 26.2006, 92.9376),
            ('Gujarat Culture', 'Gujarat', 'India', 'Colorful festivals and handicrafts', 'November to February', 'Easy', '$15-25', 'Cultural festivals, Handicrafts, Salt desert', 23.0225, 72.5714),
            ('Odisha Heritage', 'Odisha', 'India', 'Ancient temples and tribal art', 'October to March', 'Easy', '$15-20', 'Temple architecture, Tribal tours, Handloom', 20.9517, 85.0985),
            ('West Bengal Culture', 'West Bengal', 'India', 'Literary heritage and Durga Puja', 'October to March', 'Easy', '$12-20', 'Cultural heritage, Tea gardens, River cruises', 22.9868, 87.8550),
            ('Sikkim Himalayas', 'Sikkim', 'India', 'Buddhist monasteries and mountain views', 'March to June, September to November', 'Moderate', '$20-30', 'Monastery visits, Trekking, Mountain railways', 27.5330, 88.5122)
        ]

        destination_ids = []
        for dest_name, state, country, description, best_time, difficulty, budget, activities, lat, lng in destinations_data:
            dest_id = generate_id()
            destination_ids.append(dest_id)
            cursor.execute(
                """INSERT INTO Destinations (destination_id, destination_name, state_province, 
                   country, description, best_time_to_visit, difficulty_level, estimated_budget_per_day, 
                   popular_activities, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (dest_id, dest_name, state, country, description, best_time, difficulty, budget, activities, lat, lng)
            )

        # Sample Tourist Spots Data
        tourist_spots_data = [
            # Goa spots
            (destination_ids[0], 'Baga Beach', 'Beach', 'Popular beach with water sports', 'Free', '24 hours', 4.2),
            (destination_ids[0], 'Basilica of Bom Jesus', 'Religious', 'UNESCO World Heritage Site', 'Free', '9 AM - 6:30 PM', 4.5),
            (destination_ids[0], 'Dudhsagar Falls', 'Natural', 'Spectacular four-tiered waterfall', '$5', '6 AM - 5 PM', 4.7),
            # Kerala spots
            (destination_ids[1], 'Alleppey Backwaters', 'Natural', 'Venice of the East', '$20-100', '24 hours', 4.6),
            (destination_ids[1], 'Munnar Tea Gardens', 'Natural', 'Rolling hills covered with tea', '$2', '8 AM - 5 PM', 4.4),
            # Rajasthan spots
            (destination_ids[2], 'Amber Fort', 'Historical', 'Magnificent fort palace', '$3', '8 AM - 5:30 PM', 4.5),
            (destination_ids[2], 'City Palace Jaipur', 'Cultural', 'Royal residence and museum', '$5', '9:30 AM - 5 PM', 4.3),
            # Himachal spots
            (destination_ids[3], 'Rohtang Pass', 'Mountain', 'High mountain pass with snow', 'Free', '6 AM - 6 PM', 4.1),
            (destination_ids[3], 'Solang Valley', 'Adventure', 'Adventure sports destination', '$10-30', '9 AM - 5 PM', 4.3),
            # Uttarakhand spots
            (destination_ids[4], 'Kedarnath Temple', 'Religious', 'Sacred Hindu pilgrimage site', 'Free', '4 AM - 9 PM', 4.8)
        ]

        spot_ids = []
        for dest_id, spot_name, spot_type, description, fee, hours, rating in tourist_spots_data:
            spot_id = generate_id()
            spot_ids.append(spot_id)
            cursor.execute(
                """INSERT INTO TouristSpots (spot_id, destination_id, spot_name, spot_type,
                   description, entry_fee, opening_hours, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (spot_id, dest_id, spot_name, spot_type, description, fee, hours, rating)
            )

        # Sample Groups Data
        groups_data = [
            ('Goa Beach Paradise', 'Experience the best beaches of Goa', 'Public', 7, '$200-300', '2024-12-15', '2024-12-22', 'Planning'),
            ('Kerala Houseboat Adventure', 'Cruise through serene backwaters', 'Private', 5, '$250-350', '2024-11-20', '2024-11-27', 'Planning'),
            ('Rajasthan Royal Heritage', 'Explore palaces and forts', 'Public', 10, '$300-400', '2024-12-01', '2024-12-11', 'Planning'),
            ('Himachal Trekking Expedition', 'Mountain trekking and adventure', 'Private', 6, '$180-250', '2025-05-01', '2025-05-07', 'Planning'),
            ('Spiritual Uttarakhand Journey', 'Pilgrimage and yoga retreat', 'Public', 8, '$150-200', '2025-03-10', '2025-03-18', 'Planning'),
            ('Ladakh High Altitude Adventure', 'Extreme altitude experience', 'Private', 4, '$400-500', '2025-07-15', '2025-07-25', 'Planning'),
            ('Andaman Diving Paradise', 'Scuba diving and water sports', 'Public', 6, '$350-450', '2024-12-10', '2024-12-17', 'Planning'),
            ('Tamil Nadu Temple Trail', 'Ancient temples exploration', 'Public', 12, '$120-180', '2024-11-15', '2024-11-27', 'Planning'),
            ('Karnataka Coffee Culture', 'Coffee plantations and heritage', 'Private', 5, '$160-220', '2024-12-05', '2024-12-10', 'Planning'),
            ('Maharashtra Wine & Caves', 'Wine tasting and cave exploration', 'Public', 8, '$200-280', '2025-01-20', '2025-01-27', 'Planning')
        ]

        group_ids = []
        for i, (group_name, description, group_type, duration, cost, start_date, end_date, status) in enumerate(groups_data):
            group_id = generate_id()
            group_ids.append(group_id)
            owner_id = random.choice(user_ids)
            max_members = random.randint(15, 30)
            
            cursor.execute(
                """INSERT INTO Groups (group_id, group_name, group_description, group_type, 
                   owner_id, member_count, max_members, total_duration_days, estimated_total_cost,
                   travel_start_date, travel_end_date, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (group_id, group_name, description, group_type, owner_id, 1, max_members,
                 duration, cost, start_date, end_date, status)
            )

        # Create Travel Itineraries (Link groups to destinations)
        for i, group_id in enumerate(group_ids):
            # Each group visits 1-3 destinations
            num_destinations = random.randint(1, min(3, len(destination_ids)))
            selected_destinations = random.sample(destination_ids, num_destinations)
            
            for order, dest_id in enumerate(selected_destinations, 1):
                itinerary_id = generate_id()
                duration_days = random.randint(2, 4)
                cursor.execute(
                    """INSERT INTO TravelItinerary (itinerary_id, group_id, destination_id, visit_order,
                       duration_days, notes) VALUES (?, ?, ?, ?, ?, ?)""",
                    (itinerary_id, group_id, dest_id, order, duration_days, f"Stop {order} in travel chain")
                )

        # Add group owners to GroupMembers
        cursor.execute("SELECT group_id, owner_id FROM Groups")
        group_owner_pairs = cursor.fetchall()
        
        for group_id, owner_id in group_owner_pairs:
            cursor.execute("SELECT username FROM Users WHERE userid = ?", (owner_id,))
            owner_username = cursor.fetchone()[0]
            
            member_id = generate_id()
            cursor.execute(
                """INSERT INTO GroupMembers (member_id, group_id, user_id, username, role) 
                   VALUES (?, ?, ?, ?, 'Owner')""",
                (member_id, group_id, owner_id, owner_username)
            )
            
            # Update user's group ownership status
            cursor.execute("UPDATE Users SET current_group_id = ?, is_group_owner = TRUE WHERE userid = ?", 
                          (group_id, owner_id))

        # Add some regular members to groups
        for group_id in group_ids[:5]:  # Add members to first 5 groups
            num_members = random.randint(2, 5)
            available_users = [uid for uid in user_ids if uid not in [row[1] for row in group_owner_pairs]]
            selected_members = random.sample(available_users, min(num_members, len(available_users)))
            
            for user_id in selected_members:
                cursor.execute("SELECT username FROM Users WHERE userid = ?", (user_id,))
                username = cursor.fetchone()[0]
                
                member_id = generate_id()
                cursor.execute(
                    """INSERT INTO GroupMembers (member_id, group_id, user_id, username) 
                       VALUES (?, ?, ?, ?)""",
                    (member_id, group_id, user_id, username)
                )
                
                # Update user's current group
                cursor.execute("UPDATE Users SET current_group_id = ? WHERE userid = ?", (group_id, user_id))
                
                # Update group member count
                cursor.execute("UPDATE Groups SET member_count = member_count + 1 WHERE group_id = ?", (group_id,))

        # Sample Messages
        sample_messages = [
            "Hey everyone! Excited for our upcoming trip!",
            "Has anyone booked their flights yet?",
            "I found a great local restaurant we should try",
            "What's the weather forecast looking like?",
            "Don't forget to pack sunscreen!",
            "Looking forward to meeting you all",
            "Should we create a packing checklist?",
            "I've researched some amazing photo spots",
            "Anyone interested in trying local adventure sports?",
            "Let's plan our daily itinerary together"
        ]

        # Add sample messages to groups
        for group_id in group_ids[:3]:  # Add messages to first 3 groups
            cursor.execute("SELECT user_id, username FROM GroupMembers WHERE group_id = ?", (group_id,))
            group_members = cursor.fetchall()
            
            for _ in range(random.randint(3, 8)):
                member = random.choice(group_members)
                message = random.choice(sample_messages)
                
                cursor.execute(
                    "INSERT INTO GroupMessages (group_id, sender_id, sender_username, message) VALUES (?, ?, ?, ?)",
                    (group_id, member[0], member[1], message)
                )

        conn.commit()
        print(f"Successfully inserted sample data:")
        print(f"   - {len(users_data)} Users")
        print(f"   - {len(destinations_data)} Destinations")
        print(f"   - {len(tourist_spots_data)} Tourist Spots")
        print(f"   - {len(groups_data)} Groups with Travel Itineraries")
        print(f"   - Multiple Group Members and Messages")
        print(f"   - Total entries: ~{len(users_data) + len(destinations_data) + len(tourist_spots_data) + len(groups_data) + 50}")

    except sqlite3.Error as e:
        print(f"Error inserting sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

def display_sample_statistics():
    """Display statistics about the inserted sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\nDATABASE STATISTICS:")
        print("=" * 40)
        
        # Users count
        cursor.execute("SELECT COUNT(*) FROM Users")
        users_count = cursor.fetchone()[0]
        print(f"👥 Total Users: {users_count}")
        
        # Groups count by type
        cursor.execute("SELECT group_type, COUNT(*) FROM Groups GROUP BY group_type")
        groups_by_type = cursor.fetchall()
        for group_type, count in groups_by_type:
            print(f"{group_type} Groups: {count}")
        
        # Destinations count
        cursor.execute("SELECT COUNT(*) FROM Destinations")
        destinations_count = cursor.fetchone()[0]
        print(f"Total Destinations: {destinations_count}")
        
        # Tourist spots count
        cursor.execute("SELECT COUNT(*) FROM TouristSpots")
        spots_count = cursor.fetchone()[0]
        print(f"Total Tourist Spots: {spots_count}")
        
        # Messages count
        cursor.execute("SELECT COUNT(*) FROM GroupMessages")
        messages_count = cursor.fetchone()[0]
        print(f"Total Messages: {messages_count}")
        
        # Active group members
        cursor.execute("SELECT COUNT(*) FROM GroupMembers WHERE join_status = 'Approved'")
        active_members = cursor.fetchone()[0]
        print(f"Active Group Members: {active_members}")
        
        print("=" * 40)
        print("Sample data generation completed successfully!")
        print("You can now run your main application to test with this data.")
        
    except sqlite3.Error as e:
        print(f"Error retrieving statistics: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Travel Together - Sample Data Generator")
    print("=" * 50)
    
    # Setup database tables
    setup_database()
    
    # Insert comprehensive sample data
    insert_sample_data()
    
    # Display statistics
    display_sample_statistics()
