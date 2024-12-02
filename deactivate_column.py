import sqlite3

def add_deactivated_column():
    conn = sqlite3.connect('endpoints.db')  # Path to your database file
    c = conn.cursor()
    try:
        # Add the deactivated column to the table
        c.execute('ALTER TABLE endpoints ADD COLUMN deactivated INTEGER DEFAULT 0;')
        print("Column 'deactivated' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'deactivated' already exists.")
        else:
            print(f"Error adding column: {e}")
    finally:
        conn.commit()
        conn.close()

# Run the function
add_deactivated_column()
