from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

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
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    surname = request.form.get('surname')
    gender = request.form.get('gender')
    email = request.form.get('email')

    # Store data in MongoDB
    user_data = {
        'name': name,
        'surname': surname,
        'gender': gender,
        'email': email
    }

    users_collection.insert_one(user_data)

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user_data = users_collection.find_one({'email': email})
        if user_data:
            user = User()
            user.id = str(user_data['_id'])
            login_user(user)
            return redirect(url_for('select_preferences', gender=user_data['gender']))
        else:
            return "User not found. Please register first."

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Import necessary modules

@app.route('/select_preferences/<gender>', methods=['GET', 'POST'])
@login_required
def select_preferences(gender):
    if request.method == 'POST':
        selected_user_id = request.form.get('selected_user')
        current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
        current_preferences_count = len(current_user_data.get('preferences', []))

        if selected_user_id and current_preferences_count < 10:
            # Increment the index for the new preference
            new_index = current_preferences_count + 1

            # Add the selected user ID to the preferences list with the new index
            users_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$push': {'preferences': {'user_id': selected_user_id, 'index': new_index}}}
            )

    # Show users with the opposite gender
    opposite_gender = 'male' if gender == 'female' else 'female'
    users = users_collection.find({'gender': opposite_gender})

    return render_template('user_list.html', users=users, current_gender=gender)



# Import necessary modules

# Import necessary modules

# Import necessary modules

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
                    perfect_matches.append({
                        'user_id': str(current_user_data['_id']),
                        'user_id2': potential_match_id,
                        'name': current_user_data['name'],
                        'surname': current_user_data['surname'],
                        'matched_name': potential_match['name'],
                        'matched_surname': potential_match['surname']
                    })

    return render_template('matching.html', perfect_matches=perfect_matches)




if __name__ == '__main__':
    app.run(debug=True)
