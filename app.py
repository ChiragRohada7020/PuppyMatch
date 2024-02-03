from flask import Flask, render_template, request, redirect, url_for, session,flash,jsonify
from flask_mail import Mail, Message
import random
import os
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from waitress import serve
from flask import render_template_string



app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['UPLOAD_FOLDER'] = 'static/uploads'


# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'info.puppymatch@gmail.com'  # Enter your Gmail email address
app.config['MAIL_PASSWORD'] = 'icbi xxir gtmj lset'  # Enter your Gmail password

mail = Mail(app)

# Connect to MongoDB
client = MongoClient('mongodb+srv://ChiragRohada:s54icYoW4045LhAW@atlascluster.t7vxr4g.mongodb.net/test')
db = client['crush']
users_collection = db['users']

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        user = User()
        user.id = str(user_data['_id'])
        return user

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})

    return render_template('profile.html', current_user_data=current_user_data)


@app.route('/work')
def work():
    return render_template("work.html")

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method=="POST":
        name = request.form.get('name')
        gender = request.form.get('gender')
        email = request.form.get('email')
        password = request.form.get('password')
        InstaId = request.form.get('InstaId')
        profile_picture = request.files['profile_picture']

        existing_user = users_collection.find_one({'email': email})
        if not email.endswith("@somaiya.edu"):
            flash("Invalid email domain. Please use a somaiya email address.", 'error')
            return redirect(url_for('register'))  # Replace with the actual route for registration

        if existing_user:
            return "User with this email already exists. Please login or use a different email."


    # Generate a random 6-digit OTP
        otp = ''.join(str(random.randint(0, 9)) for _ in range(6))
        if profile_picture.filename != '':
    # Generate a unique filename for the uploaded file
            _, file_extension = os.path.splitext(profile_picture.filename)
            unique_filename = f"{email}_profile_picture{file_extension}"

    # Save the file to your desired directory
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

    # Store the unique filename in the user_data dictionary
            profile_picture = unique_filename

    # Store registration details in the session for OTP verification later
        session['registration_details'] = {
        'name': name,
        'gender': gender,
        'email': email,
        'password': password,
        "InstaId"  :InstaId ,# Store plaintext password (will be hashed during OTP verification)
        "profile_picture":profile_picture
        }

    # Store the OTP in the session for verification later
        session['otp'] = otp
        html_content = render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Puppy Match OTP</title>
            <!-- Your CSS styles go here -->
        </head>
        <body>
            <div class="container">
                <h2>Puppy Match OTP</h2>
                <p>Your OTP for Puppy Match verification:</p>
                <div class="otp-container">
                    <span class="otp">{{ otp }}</span>
                </div>
                <p class="note">Please use this OTP to complete your registration.</p>
            </div>
        </body>
        </html>
    """, otp=otp)


    # Send the OTP to the user's email
        msg = Message('OTP Verification', sender='your_email@gmail.com', recipients=[email])
        msg.body = f'Your OTP for registration is: {otp}'
        msg.html = html_content
        mail.send(msg)
    
    else:
        return render_template('login.html')


    # Render a page to enter and verify the OTP
    return render_template('verify_otp.html', email=email)

@app.route('/verify_registration_otp/<email>', methods=['POST'])
def verify_registration_otp(email):
    entered_otp = request.form.get('otp')

    # Retrieve the stored registration details from the session
    registration_details = session.get('registration_details')
    stored_otp = session.get('otp')
    

    if stored_otp and entered_otp == stored_otp and registration_details:
        # OTP is correct, proceed with user registration
        hashed_password = generate_password_hash(registration_details['password'], method='pbkdf2:sha256', salt_length=8)

        user_data = {
            'name': registration_details['name'],
            'gender': registration_details['gender'],
            'email': email,
            'password': hashed_password,
            'InstaId':registration_details['InstaId'],
            "profile_picture":registration_details['profile_picture']
        }
        


        # Store data in MongoDB


        users_collection.insert_one(user_data)

        # Clear the session after successful registration
        session.pop('registration_details', None)
        session.pop('otp', None)

        return redirect(url_for('login'))
    else:
        return "Invalid OTP. Please try again."

# ... (remaining code, including select_preferences and matching routes)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_data = users_collection.find_one({'email': email})
        if user_data and check_password_hash(user_data['password'], password):
            user = User()
            user.id = str(user_data['_id'])
            login_user(user)
            return redirect(url_for('select_preferences'))
        else:
            return "Invalid email or password. Please try again."

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Import necessary modules

@app.route('/select_preferences', methods=['GET', 'POST'])
@login_required
def select_preferences():
    if request.method == 'POST':
        
        selected_user_id = request.form.get('selected_user')
        current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
        gender = current_user_data["gender"]
        current_preferences = current_user_data.get('preferences', [])

        # Check if the selected user is already in the preferences list
        if selected_user_id in [pref['user_id'] for pref in current_preferences]:
            print('You have already selected this user as a preference.')
        elif len(current_preferences) < 10:
            # Increment the index for the new preference
            new_index = len(current_preferences) + 1

            # Add the selected user ID to the preferences list with the new index
            users_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$push': {'preferences': {'user_id': selected_user_id, 'index': new_index}}}
            )
        else:
            print('You have reached the maximum number of preferences (10).')

    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    gender = current_user_data["gender"]

    # Show users with the opposite gender
    opposite_gender = 'male' if gender == 'female' else 'female'
    users = users_collection.find({'gender': opposite_gender})

    return render_template('user_list.html', users=users, current_gender=gender)


@app.route('/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Get the current user's data from the database
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})

    # Retrieve the preferences list for the current user
    preferences = current_user_data.get('preferences', [])

    # Remove the specified user_id from the preferences list
    updated_preferences = [preference for preference in preferences if str(preference.get('user_id')) != user_id]

    # Update the user's preferences in the database
    users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'preferences': updated_preferences}}
    )

    # Redirect back to the select_preferences route after deletion
    return redirect(url_for('user_preferences'))

@app.route('/user_preferences')
@login_required
def user_preferences():
    # Get the current user's data from the database
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})

    # Retrieve the preferences list for the current user
    preferences = current_user_data.get('preferences', [])
    print(preferences)
    
    # print(preferences)
    user_details_list = []
    for preference in preferences:
        # Extract the user_id from the preference dictionary
        user_id = preference.get('user_id')

        # Ensure the user_id is of type ObjectId or convert it
        user_id = ObjectId(user_id)

        # Fetch user details from the database based on the user ID
        user_details = users_collection.find_one({'_id': user_id})

        # Append user details to the list
        user_details_list.append(user_details)

    return render_template('user_preferences.html', preferences=user_details_list)



# Import necessary modules

# Import necessary modules

# Import necessary modules

@app.route('/search_users')
@login_required
def search_users():
    query = request.args.get('query', '').lower()
    print(query)
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})


    # Fetch users from the database based on the search query
    users = users_collection.find({
        'gender': {'$ne': current_user_data.get('gender')},  # Exclude users of the same gender
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'InstaId': {'$regex': query, '$options': 'i'}},
            {'email': {'$regex': query, '$options': 'i'}}
        ]
    })
    
    # Convert MongoDB objects to a list of dictionaries
    users_data = [
        {'_id': str(user['_id']), 'name': user['name'], 'email': user['email'],'InstaId':user['InstaId'],
         'profile_picture': user['profile_picture']}
        for user in users
    ]

    print(users_data)

    return jsonify(users_data)




@app.route('/matching', methods=['GET'])
@login_required
def matching():
    # Get all users
    all_users = users_collection.find()

    # List to store perfect matches
    perfect_matches = []

    # Iterate through all users
    for current_user_data in all_users:
        current_user_preferences = current_user_data.get('preferences', [])

        # Determine the opposite gender
        opposite_gender = 'male' if current_user_data['gender'] == 'female' else 'female'

        # Find potential matches of opposite gender
        potential_matches = users_collection.find({
            'gender': "female",
            'preferences.user_id': str(current_user_data['_id'])
        })

        # Iterate through potential matches
        for potential_match in potential_matches:
            potential_match_id = str(potential_match['_id'])

            # Check if the current user is present in the match's preferences
            if any(potential_match_id == str(pref['user_id']) for pref in current_user_preferences):
                # Check if the match also has the current user in their preferences
                if any(str(current_user_data['_id']) == str(pref['user_id']) for pref in potential_match.get('preferences', [])):
                    sum_of_indices = sum(pref['index'] for pref in current_user_preferences if pref['user_id'] == potential_match_id)

                    perfect_matches.append({
                        'user_id': str(current_user_data['_id']),
                        'user_id2': potential_match_id,
                        'name': current_user_data['name'],
                        'surname': current_user_data['surname'],
                        'matched_name': potential_match['name'],
                        'matched_surname': potential_match['surname'],
                        'sum_of_indices': sum_of_indices

                    })
        perfect_matches = sorted(perfect_matches, key=lambda x: x['sum_of_indices'], reverse=True)
            # Create a set to keep track of users
        unique_users = set()

    # List to store final unique matches
        unique_matches = []



        for match in perfect_matches:
            if match['user_id'] not in unique_users and match['user_id2'] not in unique_users:
            # If both users are not in the set, add the match to the final list
                unique_matches.append(match)

            # Add both users to the set
                unique_users.add(match['user_id'])
                unique_users.add(match['user_id2'])
        
        unmatched_users = [
        {'user_id': str(user['_id']), 'name': user['name'], 'surname': user['surname']}
        for user in all_users
        if str(user['_id']) not in unique_users
    ]
        print(unmatched_users)



    return render_template('matching.html', perfect_matches=unique_matches)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
