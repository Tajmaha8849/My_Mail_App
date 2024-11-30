from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
import smtplib

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yyhhsgj764wyvtuucybius4yw7iucbysgiw'

# PostgreSQL Database configuration
DATABASE_URI = "postgresql://mail_app_hwcn_user:V69J8HaTl4wb6Uh9BlqWzASy7Q3gnlpS@dpg-ct5gp93qf0us7386tq3g-a.oregon-postgres.render.com/mail_app_hwcn"

# Function to establish database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URI)
    return conn

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # Check if the email already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Email already exists!', 'danger')
            conn.close()
            return redirect(url_for('register'))

        # Insert new user into PostgreSQL
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        conn.commit()
        conn.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

from werkzeug.security import check_password_hash

from werkzeug.security import check_password_hash
from flask import session, redirect, url_for, flash, render_template

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"Received email: {email}")  # Debug print
        print(f"Received password: {password}")  # Debug print

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            print(f"User fetched: {user}")  # Debug print
            if check_password_hash(user[3], password):  # Check hash from user[3]
                session['user_id'] = user[0]  # Assuming user[0] is user_id
                session['username'] = user[1]  # Assuming user[1] is username
                print("Login successful, redirecting to dashboard...")  # Debug print
                flash('Login successful!', 'success')
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password.', 'danger')
        else:
            flash('No user found with this email address.', 'danger')

        conn.close()

    return render_template('login.html')






@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    
    # Check if email exists in session, else default to an empty string
    email = session.get('email', 'Email not found')

    # Fetch messages from the database for this user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM messages WHERE user_id = %s", (user_id,))
    messages = cursor.fetchall()

    # Extract message text from the list of tuples
    message_list = [message[0] for message in messages]

    conn.close()

    return render_template('dashboard.html', username=username, email=email, messages=message_list)





@app.route('/send_mail', methods=['POST'])
def send_mail():
    if 'user_id' not in session:
        flash('Please log in to send an email.', 'warning')
        return redirect(url_for('login'))

    # Email details from form
    from_address = request.form['from_address']
    app_password = request.form['app_password']
    to_address = request.form['to_address']
    subject = request.form['subject']
    body = request.form['body']

    # Set up SMTP connection
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    message = MIMEText(body)
    message['From'] = from_address
    message['To'] = to_address
    message['Subject'] = subject

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_address, app_password)
            server.sendmail(from_address, to_address, message.as_string())

        # Save email to PostgreSQL
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sent_emails (user_id, to_address, subject, body) VALUES (%s, %s, %s, %s)", 
                       (user_id, to_address, subject, body))
        conn.commit()
        conn.close()
        flash('Email sent successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send email: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()  # Clears session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to submit the contact form.', 'warning')
            return redirect(url_for('login'))

        # Get form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Save the contact form details to PostgreSQL
        try:
            user_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contact_forms (user_id, name, email, message) VALUES (%s, %s, %s, %s)", 
                           (user_id, name, email, message))
            conn.commit()
            conn.close()
            flash('Your message has been submitted successfully!', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'Error submitting your message: {str(e)}', 'danger')

    return render_template('contact.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
