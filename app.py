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
import json
from flask import send_from_directory, Response, stream_with_context,send_file
from werkzeug.wsgi import FileWrapper
import shutil




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

@app.route('/add_comment', methods=['POST','GET'])
def add_comment():
    comments = db['comments']
    if request.method == "POST":
        comment_text = request.form.get('comment')
        if comment_text:
            comments.insert_one({'text': comment_text})
    return redirect(url_for('comment'))




@app.route('/download_images', methods=['GET'])
def download_images():
    # Get the path to the upload folder
    upload_folder_path = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])

    # List all files in the upload folder
    all_files = os.listdir(upload_folder_path)

    # Ensure there are files to download
    if not all_files:
        return "No files to download."

    try:
        # Create a temporary directory to store individual files
        temp_dir = os.path.join(os.getcwd(), 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)

        # Copy each file to the temporary directory with its original name
        for file in all_files:
            file_path = os.path.join(upload_folder_path, file)
            shutil.copy(file_path, os.path.join(temp_dir, file))

        # Create a zip file containing all images
        shutil.make_archive(os.path.join(os.getcwd(), 'images'), 'zip', temp_dir)

        # Send the zip file as a response
        return send_file('images.zip', as_attachment=True)

    except Exception as e:
        return f"Error creating or sending zip file: {str(e)}"

    finally:
        # Remove the temporary directory and its contents
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/comment')
def comment():
    
	comments = db['comments']
	
	all_comments = comments.find().sort('_id', -1)
	
	return render_template("comments.html",comments=all_comments)

        
        



@app.route('/profile')
@login_required
def profile():
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})

    return render_template('profile.html', current_user_data=current_user_data)


@app.route('/work')
def work():
    return render_template("work.html")


@app.route('/reorder_preferences', methods=['POST'])
@login_required
def reorder_preferences():
    if request.method == 'POST':
        # Get the reordered preference order from the client-side

        reordered_order = request.form.getlist('userOrder')
        reordered_order = json.loads(reordered_order[0])

        
        
        
        users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$unset': {'preferences': ''}}
    )
        for index, preference_id in enumerate(reordered_order):
            users_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$push': {'preferences': {'user_id': preference_id , 'index': index}}}
            )

        # Update the preferences order in the database


    # Redirect back to the select_preferences route after reordering
    return redirect(url_for('user_preferences'))

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
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="en">

<head>
	<title></title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0"><!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]--><!--[if !mso]><!-->
	<link href="https://fonts.googleapis.com/css?family=Oswald" rel="stylesheet" type="text/css"><!--<![endif]-->
	<style>
		* {
			box-sizing: border-box;
		}

		body {
			margin: 0;
			padding: 0;
		}

		a[x-apple-data-detectors] {
			color: inherit !important;
			text-decoration: inherit !important;
		}

		#MessageViewBody a {
			color: inherit;
			text-decoration: none;
		}

		p {
			line-height: inherit
		}

		.desktop_hide,
		.desktop_hide table {
			mso-hide: all;
			display: none;
			max-height: 0px;
			overflow: hidden;
		}

		.image_block img+div {
			display: none;
		}

		@media (max-width:670px) {

			.desktop_hide table.icons-inner,
			.social_block.desktop_hide .social-table {
				display: inline-block !important;
			}

			.icons-inner {
				text-align: center;
			}

			.icons-inner td {
				margin: 0 auto;
			}

			.mobile_hide {
				display: none;
			}

			.row-content {
				width: 100% !important;
			}

			.stack .column {
				width: 100%;
				display: block;
			}

			.mobile_hide {
				min-height: 0;
				max-height: 0;
				max-width: 0;
				overflow: hidden;
				font-size: 0px;
			}

			.desktop_hide,
			.desktop_hide table {
				display: table !important;
				max-height: none !important;
			}
		}
	</style>
</head>

<body style="background-color: #c3f1ff; margin: 0; padding: 0; -webkit-text-size-adjust: none; text-size-adjust: none;">
	<table class="nl-container" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #c3f1ff;">
		<tbody>
			<tr>
				<td>
					<table class="row row-1" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #c3f1ff;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-position: center top; background-repeat: no-repeat; color: #000000; background-image: url('https://d1oco4z2z1fhwp.cloudfront.net/templates/default/6081/Header_Background_01.png'); width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-top: 30px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="divider_block block-1" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<div class="alignment" align="center">
																	<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																		<tr>
																			<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 2px dashed #0F7085;"><span>&#8202;</span></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="heading_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-left:10px;padding-right:10px;text-align:center;width:100%;">
																<h1 style="margin: 0; color: #cb0c0c; direction: ltr; font-family: Oswald, Arial, Helvetica Neue, Helvetica, sans-serif; font-size: 64px; font-weight: normal; letter-spacing: 1px; line-height: 120%; text-align: center; margin-top: 0; margin-bottom: 0; mso-line-height-alt: 76.8px;">VALENTINE'S DAY</h1>
															</td>
														</tr>
													</table>
													<table class="divider_block block-3" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad">
																<div class="alignment" align="center">
																	<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																		<tr>
																			<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 2px dashed #0F7085;"><span>&#8202;</span></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<div class="spacer_block block-4" style="height:30px;line-height:30px;font-size:1px;">&#8202;</div>
													<table class="image_block block-5" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="width:100%;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div style="max-width: 650px;"><img src="https://d1oco4z2z1fhwp.cloudfront.net/templates/default/6081/Header_Overlay_01.png" style="display: block; height: auto; border: 0; width: 100%;" width="650" alt="Image Of Love Header" title="Image Of Love Header"></div>
																</div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-2" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-position: center top; background-repeat: no-repeat; color: #000000; background-color: #ffffff; background-image: url('https://d1oco4z2z1fhwp.cloudfront.net/templates/default/6081/PliegueSobre_03.png'); width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 50px; padding-left: 20px; padding-right: 20px; padding-top: 10px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="paragraph_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad" style="padding-left:10px;padding-right:10px;padding-top:10px;">
																<div style="color:#0f7085;font-family:Oswald, Arial, Helvetica Neue, Helvetica, sans-serif;font-size:20px;letter-spacing:1px;line-height:120%;text-align:center;mso-line-height-alt:24px;">
																	<p style="margin: 0; word-break: break-word;"><strong><span>UNTIL FEBRUARY 14, SHOW YOUR LOVE</span></strong></p>
																</div>
															</td>
														</tr>
													</table>
													<table class="divider_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-bottom:30px;padding-left:10px;padding-right:10px;padding-top:30px;">
																<div class="alignment" align="center">
																	<table border="0" cellpadding="0" cellspacing="0" role="presentation" width="50%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																		<tr>
																			<td class="divider_inner" style="font-size: 1px; line-height: 1px; border-top: 2px dashed #0F7085;"><span>&#8202;</span></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<table class="text_block block-3" width="100%" border="0" cellpadding="10" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; word-break: break-word;">
														<tr>
															<td class="pad">
																<div style="font-family: sans-serif">
																	<div class style="font-size: 14px; font-family: Oswald, Arial, Helvetica Neue, Helvetica, sans-serif; mso-line-height-alt: 16.8px; color: #0f7085; line-height: 1.2;">
																		<p style="margin: 0; font-size: 14px; text-align: center; mso-line-height-alt: 16.8px; letter-spacing: 1px;"><strong><span style="font-size:20px;">OTP: <span style="color:#cb0c0c;">{{otp}}</span></span></strong></p>
																	</div>
																</div>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-3" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:5px;line-height:5px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-4" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:5px;line-height:5px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-5" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:5px;line-height:5px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-6" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:5px;line-height:5px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-7" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<div class="spacer_block block-1" style="height:35px;line-height:35px;font-size:1px;">&#8202;</div>
													<table class="social_block block-2" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="padding-bottom:10px;padding-left:20px;padding-right:20px;padding-top:10px;text-align:center;">
																<div class="alignment" align="center">
																	<table class="social-table" width="52px" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block;">
																		<tr>
																			<td style="padding:0 10px 0 10px;"><a href="https://www.instagram.com/info.puppymatch" target="_blank"><img src="https://app-rsrc.getbee.io/public/resources/social-networks-icon-sets/t-outline-circle-color/instagram@2x.png" width="32" height="32" alt="Instagram" title="instagram" style="display: block; height: auto; border: 0;"></a></td>
																		</tr>
																	</table>
																</div>
															</td>
														</tr>
													</table>
													<div class="spacer_block block-3" style="height:25px;line-height:25px;font-size:1px;">&#8202;</div>
													<table class="image_block block-4" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="width:100%;">
																<div class="alignment" align="center" style="line-height:10px">
																	<div style="max-width: 650px;"><img src="https://49a3ab8ee4.imgdist.com/public/users/Integrators/BeeProAgency/1139557_1125182/puppy4.png" style="display: block; height: auto; border: 0; width: 100%;" width="650" alt="Your Logo Here" title="Your Logo Here"></div>
																</div>
															</td>
														</tr>
													</table>
													<div class="spacer_block block-5" style="height:25px;line-height:25px;font-size:1px;">&#8202;</div>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
					<table class="row row-8" align="center" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;">
						<tbody>
							<tr>
								<td>
									<table class="row-content stack" align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff; color: #000000; width: 650px; margin: 0 auto;" width="650">
										<tbody>
											<tr>
												<td class="column column-1" width="100%" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; font-weight: 400; text-align: left; padding-bottom: 5px; padding-top: 5px; vertical-align: top; border-top: 0px; border-right: 0px; border-bottom: 0px; border-left: 0px;">
													<table class="icons_block block-1" width="100%" border="0" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
														<tr>
															<td class="pad" style="vertical-align: middle; color: #1e0e4b; font-family: 'Inter', sans-serif; font-size: 15px; padding-bottom: 5px; padding-top: 5px; text-align: center;">
																<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt;">
																	<tr>
																		<td class="alignment" style="vertical-align: middle; text-align: center;"><!--[if vml]><table align="center" cellpadding="0" cellspacing="0" role="presentation" style="display:inline-block;padding-left:0px;padding-right:0px;mso-table-lspace: 0pt;mso-table-rspace: 0pt;"><![endif]-->
																			<!--[if !vml]><!-->
																			<table class="icons-inner" style="mso-table-lspace: 0pt; mso-table-rspace: 0pt; display: inline-block; margin-right: -4px; padding-left: 0px; padding-right: 0px;" cellpadding="0" cellspacing="0" role="presentation"><!--<![endif]-->
																				<tr>
																					<td style="vertical-align: middle; text-align: center; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 6px;"><a href="http://designedwithbeefree.com/" target="_blank" style="text-decoration: none;"><img class="icon" alt="Beefree Logo" src="https://d1oco4z2z1fhwp.cloudfront.net/assets/Beefree-logo.png" height="32" width="34" align="center" style="display: block; height: auto; margin: 0 auto; border: 0;"></a></td>
																					<td style="font-family: 'Inter', sans-serif; font-size: 15px; font-weight: undefined; color: #1e0e4b; vertical-align: middle; letter-spacing: undefined; text-align: center;"><a href="http://designedwithbeefree.com/" target="_blank" style="color: #1e0e4b; text-decoration: none;">Designed with Beefree</a></td>
																				</tr>
																			</table>
																		</td>
																	</tr>
																</table>
															</td>
														</tr>
													</table>
												</td>
											</tr>
										</tbody>
									</table>
								</td>
							</tr>
						</tbody>
					</table>
				</td>
			</tr>
		</tbody>
	</table><!-- End -->
</body>

</html>
    """, otp=otp)


    # Send the OTP to the user's email
        msg = Message(subject="Puppy Match", sender='your_email@gmail.com', recipients=[email])
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
