from datetime import datetime
from random import randint
import sqlite3
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
import mysql.connector  
from flask_cors import CORS 
import hashlib
import re
from werkzeug.security import check_password_hash, generate_password_hash


import os
from datetime import datetime
from random import randint
import sqlite3
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
import mysql.connector  
from flask_cors import CORS 
import hashlib
import re
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Read Flask secret key from env
CORS(app)

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        print("Database connection successful")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None  

# Your Flask routes and other logic here...


# --- Validation Functions ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_mobile(mobile):
    return mobile.isdigit() and len(mobile) in [10, 12]

def check_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'user_db'")
    exists = cursor.fetchone()
    cursor.close()
    conn.close()
    return exists is not None

# --- Signup Route ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    print(f"Received data: {data}")  # Log the received data for debugging
    username = data.get('name')
    email = data.get('email')
    mobile = data.get('mobile')
    usertype = data.get('usertype')
    password = data.get('password')

    if not username or not email or not mobile or not password or not usertype:
        return jsonify({"message": "All fields are required!"}), 400
    if not is_valid_email(email):
        return jsonify({"message": "Invalid email format!"}), 400
    if not is_valid_mobile(mobile):
        return jsonify({"message": "Invalid mobile number!"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if not check_table_exists():
            return jsonify({"message": "Database table 'user_db' does not exist!"}), 500

        cursor.execute(
            "INSERT INTO user_db (username, email, mobile, usertype, password) VALUES (%s, %s, %s, %s, %s)",
            (username, email, mobile, usertype, hashed_password)
        )
        conn.commit()
        return jsonify({"message": "Registration successful!"})
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Email already exists!"}), 400
    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()
import logging

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usertype = data.get('usertype')
    email = data.get('email')
    password = data.get('password')

    if not email or not password or not usertype:
        return jsonify({"message": "Email, password, and usertype are required!"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Invalid email format!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if usertype == "receiver":
            usertype = "recipient"  # Match 'receiver' with 'recipient' in the database

        cursor.execute("SELECT * FROM user_db WHERE email = %s AND usertype = %s", (email, usertype))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"message": "User not found or user type mismatch!"}), 404

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if user['password'] != hashed_password:
            return jsonify({"message": "Incorrect password!"}), 401

        session['user_email'] = email

        return jsonify({
            "message": "Login successful!",
            "usertype": user['usertype'],
            "username": user['username']
        }), 200

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"message": f"Database error: {err}"}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"message": "An unexpected error occurred!"}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/get_profile', methods=['GET'])
def get_profile():
    if 'user_email' not in session:
        return jsonify({"message": "Not logged in!"}), 401

    email = session['user_email']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, email, mobile, usertype FROM user_db WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(user), 200

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_email' not in session:
        return jsonify({"message": "Not logged in!"}), 401

    data = request.json
    email = session['user_email']
    new_username = data.get('username')
    new_mobile = data.get('mobile')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_db SET username=%s, mobile=%s WHERE email=%s", (new_username, new_mobile, email))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Profile updated!"}), 200

@app.route('/send_verification', methods=['POST'])
def send_verification():
    if 'user_email' not in session:
        return jsonify({"message": "Not logged in!"}), 401

    email = session['user_email']
    code = randint(1000, 9999)
    session['code'] = str(code)

    msg = MIMEText(f"Your code: {code}")
    msg['Subject'] = 'Verification Code'
    msg['From'] = 'your_email@example.com'
    msg['To'] = email

    try:
        server = smtplib.SMTP('smtp.example.com', 587)
        server.starttls()
        server.login('share2careofficial35@gmail.com', 'drdi gbgz qqow mxbzy')
        server.sendmail(msg['From'], [email], msg.as_string())
        server.quit()
        return jsonify({"message": "Code sent"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_email' not in session:
        return jsonify({"message": "Not logged in!"}), 401

    data = request.json
    email = session['user_email']
    code = data.get('code')
    new_pw = data.get('newPassword')

    if session.get('code') != code:
        return jsonify({"message": "Invalid code!"}), 400

    hashed_pw = hashlib.sha256(new_pw.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_db SET password=%s WHERE email=%s", (hashed_pw, email))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Password updated!"}), 200

# ✅ API Route to Submit Food Requests
@app.route('/submit_food_request', methods=['POST'])
def submit_food_request():
    data = request.json  # Get JSON data from frontend

    # Extract form data
    full_name = data.get("fullName")
    email = data.get("email") 
    food_name = data.get('foodName')
    food_type = data.get('foodType')
    quantity = data.get('quantity')
    expiry = data.get('expiry')
    location = data.get('location')

    # Validate required fields
    if not food_name or not quantity or not expiry or not location:
        return jsonify({"success": False, "message": "All fields are required!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ Insert data into food_requests table
        query = "INSERT INTO food_requests (full_name, email,food_name, food_type, quantity, expiry,  location) VALUES (%s, %s,%s, %s, %s, %s, %s)"
        cursor.execute(query, (full_name, email,food_name, food_type, quantity, expiry, location))
        conn.commit()

        return jsonify({"success": True, "message": "Food request submitted successfully!"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/donate-cloth', methods=['POST'])
def donate_cloth():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    cloth_type = data.get('cloth_type')
    quantity = data.get('quantity')
    condition_status = data.get('condition_status')
    location = data.get('location')

    # Check for required fields
    if not full_name or not email:
        return jsonify({"success": False, "message": "Donor name and email are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cloth (full_name, email, cloth_type, quantity, condition_status, location, submitted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, cloth_type, quantity, condition_status, location, datetime.now()))
        conn.commit()
        return jsonify({"success": True, "message": "Cloth donation submitted successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()


from flask import request, jsonify
from datetime import datetime

@app.route("/submit_blood_request", methods=["POST"])
def submit_blood_request():
    data = request.get_json()

    full_name = data.get("fullName")
    email = data.get("email")  # ✅ New field
    blood_type = data.get("bloodType")
    quantity = data.get("quantity")
    hospital = data.get("hospital")
    needed_by = data.get("neededBy")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ Updated INSERT query to include 'email'
        query = """
            INSERT INTO blood_requests 
            (full_name, email, blood_type, quantity, hospital, needed_by, requested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            full_name,
            email,
            blood_type,
            quantity,
            hospital,
            needed_by,
            datetime.now()
        )
        cursor.execute(query, values)
        conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "message": str(e)})

    finally:
        if 'cursor' in locals():
          cursor.close()
        if 'conn' in locals():
           conn.close()



@app.route('/submit_book_donation', methods=['POST'])
def submit_book_donation():
    data = request.get_json()

    try:
        full_name = data.get('full_name')
        email = data.get('email')
        title = data['title']
        author = data.get('author', '')
        condition_status = data['condition']
        age_group = data.get('age_group', '')
        location = data['location']

        connection = get_db_connection()

        with connection.cursor() as cursor:
            query = """
                INSERT INTO book (full_name, email, title, author, condition, age_group, location, donated_on)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                full_name,
                email,
                title,
                author,
                condition_status,
                age_group,
                location,
                datetime.now()
            ))
            connection.commit()

        connection.close()
        return jsonify({"success": True})

    except Exception as e:
        print("Server Error:", str(e))
        return jsonify({"success": False, "message": "Database error: " + str(e)}), 500


@app.route('/donate-book', methods=['POST'])
def donate_book():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    title = data.get('title')
    author = data.get('author', '')
    condition = data.get('condition')
    age_group = data.get('age_group', '')
    location = data.get('location')

    if not title or not location:
        return jsonify({"success": False, "message": "Book title and location are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO book (full_name, email, title, author, `condition`, age_group, location, donated_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, title, author, condition, age_group, location, datetime.now()))

        conn.commit()  # Ensure the commit is executed
        print("Data inserted successfully")
        return jsonify({"success": True, "message": "Book donation submitted successfully!"})
    except mysql.connector.Error as err:
        print("Database error:", err)
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/donate-stationery', methods=['POST'])
def donate_stationery():
    data = request.json
    full_name = data.get('full_name')      # Get donor name as 'fullName'
    email = data.get('email')              # Get donor email as 'email'
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    condition = data.get('condition')
    age_group = data.get('age_group')
    location = data.get('location')

    # Check if full_name and email are present
    if not full_name or not email:
        return jsonify({"success": False, "message": "Donor name and email are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stationery (full_name, email, item_name, quantity, `condition`, age_group, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, item_name, quantity, condition, age_group, location))
        conn.commit()
        return jsonify({"success": True, "message": "Stationery donation submitted successfully!"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

#reciever form get request
@app.route('/get-requests', methods=['POST'])
def get_requests():
    data = request.get_json()
    category = data.get('category')

    print(f"Category received: {category}")  # ✅ Debug print

    table_map = {
        'food': 'food_requests',
        'clothes': 'cloth',
        'blood': 'blood_requests',
        'stationery': 'stationery',
        'books': 'book'
    }

    table = table_map.get(category)
    if not table:
        return jsonify({'error': 'Invalid category'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table}")
        results = cursor.fetchall()
        print("Fetched rows:", results)  # ✅ Debug print
        return jsonify(results)
    except Exception as e:
        print("DB Error:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
#RF-request for donation part1

@app.route('/get-donation-requests', methods=['POST'])
def get_donation_requests():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM donation_request")
    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(requests)


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/submit-request', methods=['POST'])
def submit_request():
    data = request.json

    # Extract data from the request
    item = data.get('item')
    donor_name = data.get('donorName')
    donor_email = data.get('donorEmail')
    category = data.get('category')
    receiver_name = data.get('receiverName')
    receiver_contact = data.get('receiverContact')
    receiver_address = data.get('receiverAddress')
    reason = data.get('reason')

    # Check for missing fields
    if not all([item, donor_name, donor_email, category, receiver_name, receiver_contact, receiver_address, reason]):
        return jsonify({"message": "All fields are required!"}), 400

    # Initialize database connection and cursor
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into donation_request table
        cursor.execute("""
            INSERT INTO donation_request 
            (item, donor_name, donor_email, category, receiver_name, receiver_contact, receiver_address, reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (item, donor_name, donor_email, category, receiver_name, receiver_contact, receiver_address, reason))
        conn.commit()

        # Send email to donor
        try:
            send_email_to_donor(donor_email, donor_name, receiver_name, receiver_contact, item)
        except Exception as email_error:
            print(f"Error sending email: {email_error}")
            # Continue processing, but don't fail the whole request
            # Return success for the form submission
            return jsonify({"message": "Donation request submitted, but error sending email!"}), 200

        # Delete from the correct category table
        table_mapping = {
            'food': 'food_requests',
            'book': 'book',
            'blood': 'blood_requests',
            'stationery': 'stationery',
            'cloth': 'cloth'
        }

        category_table = table_mapping.get(category.lower())

        if not category_table:
            return jsonify({"message": "Invalid category!"}), 400  # Handle invalid category

        try:
            delete_query = f"DELETE FROM {category_table} WHERE email = %s"
            cursor.execute(delete_query, (donor_email,))
            conn.commit()
        except Exception as delete_error:
            print(f"Error deleting from {category_table}: {delete_error}")
            return jsonify({"message": f"Error deleting from {category_table}!"}), 500

        return jsonify({"message": "Donation request submitted, email sent, and entry deleted!"}), 200

    except Exception as e:
        print(f"Error saving request: {e}")
        return jsonify({"message": "Error submitting donation request."}), 500

        success_message = """
        <div style="background-color: green; color: white; padding: 20px; text-align: center;">
            Donation request submitted, email sent, and entry deleted!
        </div>
        """

        return success_message, 200

    except Exception as e:
        print(f"Error saving request: {e}")
        return jsonify({"message": "Error submitting donation request."}), 500

    finally:
        # Ensure connection and cursor are properly closed
        if cursor:
            cursor.close()
        if conn:
            conn.close()


import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

def send_email_to_donor(donor_email, donor_name, receiver_name, receiver_contact, item):
    try:
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_EMAIL_PASSWORD')

        subject = "Donation Request Details"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <p>Hello <strong>{donor_name}</strong>,</p>

            <p>Someone has shown interest in receiving the item you offered:</p>
            <p style="font-size: 16px;"><strong>🧾 Item:</strong> <span style="color: #2b7a78;"><b>{item}</b></span></p>
            <p><strong>👤 Receiver:</strong> <span style="color: #17252a;">{receiver_name}</span></p>
            <p><strong>📱 Receiver Contact:</strong> <span style="color: #17252a;">{receiver_contact}</span></p>

            <p>The receiver will contact you for further details.<br>
            Kindly get in touch if you wish to proceed with the donation.</p>

            <p style="margin-top: 20px;">Thank you for your generosity,<br>
            <p><b>Regards</b></p>
            <strong style="color: #3aafa9;">Share2Care Team</strong></p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = donor_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, donor_email, msg.as_string())
        server.quit()

        print("Email sent to donor!")

    except Exception as e:
        print("Failed to send email:", e)


if __name__ == '__main__':
    app.run(debug=True)
