######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = b'd8fe06yc8f0d8&efa983J&pe3'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password123' #CHANGE THIS TO YOUR MYSQL psswrd
app.config['MYSQL_DATABASE_DB'] = 'photoshare_data'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users") 
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
    	return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
    	return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT psswrd FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['passwrod'] == pwd
    return user
    
'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
                <form action='login' method='POST'>
    		<input type='text' name='email' id='email' placeholder='email'></input>
    		<input type='password' name='password' id='password' placeholder='password'></input>
		<input type='submit' name='submit'></input>
		</form></br>
		<a href='/'>Home</a>
	       '''
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT psswrd FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

    #information did not match
    return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
    return render_template('improved_register.html', supress='True')  

@app.route("/register/", methods=['POST'])
def register_user():
    try:
        email=request.form.get('email')
        print (email)
        psswrd=request.form.get('password')
        fname=request.form.get('firstname')
        lname=request.form.get('lastname')
        dob=request.form.get('birthday')
        hometown=request.form.get('hometown')
        gender=request.form.get('gender')
        username=request.form.get('username')
    except:
        print ("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        if not username:
            print (cursor.execute("INSERT INTO Users (email, psswrd, fname, lname, dob, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, psswrd, fname, lname, dob, hometown, gender)))
        else:
            print (cursor.execute("INSERT INTO Users (email, psswrd, fname, lname, dob, hometown, gender, username) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, psswrd, fname, lname, dob, hometown, gender, username)))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('profile.html',name=email, message='Account Created!')
    else:
        print ("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))
    
def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
    	#this means there are greater than zero entries with that email
    	return False
    else:
    	return True
#end login code

#Useful functions
def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def getUsernameFromId(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT username  FROM Users WHERE user_id = '{0}'".format(user_id))
    return cursor.fetchone()[0]

def getUserFriends(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Friends WHERE Friends.user1_id = '{0}' OR Friends.user2_id = '{0}'".format(user_id))
    friends_list_pairs = cursor.fetchall()
    friends_list = [users[0] if users[0] != user_id else users[1] for users in friends_list_pairs]
    friends_list = [getUsernameFromId(uid) for uid in friends_list]
    return friends_list

def getUserAlbums(uid):
    #Grab user albums for displaying
    cursor = conn.cursor()
    cursor.execute("SELECT album_name, creation_date FROM Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()

def getAlbumId(album_name, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id FROM Albums WHERE Albums.user_id = '{0}' AND Albums.album_name = '{1}'".format(user_id, album_name))
    return cursor.fetchone()[0]

def getPhotoTags(pic_ids):
    tags = {pid:() for pid in pic_ids}
    cursor = conn.cursor()
    for picture in pic_ids:
        cursor.execute("SELECT tag_name FROM Tags WHERE picture_id = '{0}'".format(picture))
        tags[picture]=cursor.fetchall()
    return tags
    
#---------------------------User Profile Code (Includes creating/deleting albums, displaying profile, and uploading images)-----------------------------#
@app.route('/profile', methods = ['GET', 'POST'])
@flask_login.login_required
def protected():
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    user_albums = getUserAlbums(user_id)
    user_friends = getUserFriends(user_id)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM Users WHERE user_id = '{0}'".format(user_id))
    username = cursor.fetchone()[0]
    cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(user_id))
    all_tags = getPhotoTags([pid[0] for pid in cursor.fetchall()])
    all_tags = [all_tags[pic] for pic in all_tags]
    tagsort = set([tag for array in all_tags for tag in array])
    cursor.execute("SELECT p_pic FROM Users WHERE user_id = '{0}'".format(user_id))
    profile_pic = cursor.fetchone()[0]
    return render_template('profile.html', name=username, profile_pic = profile_pic, message="Here's your profile", albums = user_albums, friends = user_friends, tagsort = tagsort)

@app.route('/profile/changepic', methods = ['GET', 'POST'])
@flask_login.login_required
def changeProfilePic():
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    imgfile = request.files['photo']
    photo_data = base64.standard_b64encode(imgfile.read())
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET p_pic = '{0}' WHERE user_id = '{1}'".format(photo_data, user_id))
    conn.commit()
    return flask.redirect(flask.url_for('protected'))

#Shows user the pictures they've posted with the requested tag
@app.route('/profile/<string:tag_name>', methods = ['GET', 'POST'])
@flask_login.login_required
def userTags(tag_name):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT Tags.picture_id FROM Pictures, Tags WHERE Pictures.user_id = '{0}' AND Pictures.picture_id = Tags.picture_id AND Tags.tag_name = '{1}'".format(user_id, tag_name))
    matching_ids = cursor.fetchall()
    photos = []
    for photo in matching_ids:
        cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(photo[0]))
        photos.append(cursor.fetchone())
    photo_tags = getPhotoTags([pid[0] for pid in matching_ids])
    return render_template("pictures.html", album = tag_name, name=getUsernameFromId(user_id), photos = photos, tags = photo_tags, info="with tag")
    
#Renames a user's album
@app.route('/profile/newname', methods = ['GET', 'POST'])
@flask_login.login_required
def renameAlbum():
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    new_name = request.form.get("newname")
    cursor = conn.cursor()
    cursor.execute("UPDATE Albums SET album_name = '{0}' WHERE user_id = '{1}'".format(new_name, user_id))
    conn.commit()
    return flask.redirect(flask.url_for('protected'))

#Diplay pictures inside user album 
@app.route('/pictures/<string:album_name>', methods = ['GET', 'POST'])
@flask_login.login_required
def display_pictures(album_name):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    album_id = getAlbumId(album_name, user_id)
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE Pictures.album_id = '{0}'".format(album_id))
    photos = cursor.fetchall()
    photo_tags = getPhotoTags([pid[1] for pid in photos])
    return render_template("pictures.html", album = album_name, name=getUsernameFromId(user_id), photos = photos, tags = photo_tags, info="in album")
#End Display Pictures code

#Edit tags of pictures
@app.route('/pictures/<int:picture_id>', methods = ['GET'])
@flask_login.login_required
def editTags(picture_id):
    username = getUsernameFromId(getUserIdFromEmail(flask_login.current_user.id))
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
    photo = cursor.fetchone()
    photo_tags = getPhotoTags([picture_id])[picture_id]
    print(photo_tags)
    return render_template("tags.html", name=username, photo=photo, tags=photo_tags)

#Delete Tag Code
@app.route('/pictures/<int:picture_id>/<string:tag_name>', methods = ['GET', 'POST'])
@flask_login.login_required
def deleteTag(tag_name, picture_id):
    username = getUsernameFromId(getUserIdFromEmail(flask_login.current_user.id))
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
    photo = cursor.fetchone()
    cursor.execute("DELETE FROM Tags WHERE tag_name = '{0}' AND picture_id = '{1}' ".format(str(tag_name), picture_id))
    conn.commit()
    photo_tags = getPhotoTags([picture_id])[picture_id]
    return render_template("tags.html", name=username, photo=photo, tags=photo_tags)

#Edit tags of pictures
@app.route('/pictures/<int:picture_id>', methods = ['POST'])
@flask_login.login_required
def addTag(picture_id):
    username = getUsernameFromId(getUserIdFromEmail(flask_login.current_user.id))
    tag = request.form.get('newtag').replace(" ", "").replace("'", "")
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
    photo = cursor.fetchone()
    cursor.execute("INSERT INTO Tags (tag_name,picture_id) VALUES ('{0}', '{1}')".format(tag, picture_id))
    conn.commit()
    photo_tags = getPhotoTags([picture_id])[picture_id]
    return render_template("tags.html", name=username, photo=photo, tags=photo_tags)

#Begin album creation code1
@app.route('/create', methods = ['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'GET':
        return render_template('album_create.html')
    elif request.method == 'POST':
        album_name = request.form.get('name')
        user_id = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        if not cursor.execute("SELECT * FROM Albums WHERE Albums.user_id = '{0}' AND Albums.album_name = '{1}'".format(user_id, album_name)):
            cursor.execute("INSERT INTO Albums(user_id, album_name) VALUES ('{0}', '{1}')".format(user_id, album_name))
            return flask.redirect(flask.url_for('protected'))
        else:
            return render_template('album_create.html', name = album_name)
#End album creation code

#Begin delete album code
@app.route('/delete/<string:album_id>', methods=['POST'])
@flask_login.login_required
def deleteUserAlbum(album_id):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Albums WHERE Albums.user_id = '{0}' AND Albums.album_name = '{1}'".format(user_id, album_id))
    return flask.redirect(flask.url_for('protected'))
#End delete album code

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload/<string:album_name>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(album_name):
    if request.method == 'POST':
        user_id = flask_login.current_user.id
        album_id = getAlbumId(album_name, getUserIdFromEmail(user_id))
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        tags = request.form.get('tags').replace(" ", "").replace("'", "")
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        cursor.execute("SELECT * from Pictures WHERE imgdata = '{0}'".format(photo_data))
        not_unique = cursor.fetchall()
        if not_unique:
            return render_template('upload.html', album = album_name, not_unique = not_unique)
        cursor.execute("INSERT INTO Pictures (imgdata, user_id, album_id, caption) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data, uid, album_id, caption))
        conn.commit()
        cursor.execute("SELECT picture_id FROM Pictures WHERE Pictures.imgdata = '{0}'".format(photo_data))
        picture_id = cursor.fetchone()[0]
        for tag in tags:
            cursor.execute("INSERT INTO Tags (picture_id, tag_name) VALUES ('{0}', '{1}')".format(picture_id, tag))
            conn.commit()
        albums = getUserAlbums(user_id)
        return flask.redirect(flask.url_for('protected'))
    #The method is GET so we return a  HTML form to upload the a photo.
    else:
    	return render_template('upload.html', album = album_name, not_unique = [])
#end photo uploading code

#Begin adding friend code
@app.route('/addFriend/<string:friend>', methods=['POST'])
@flask_login.login_required
def addFriend(friend):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE username = '{0}'".format(friend))
    friend_id = cursor.fetchone()[0]
    if user_id and user_id != friend_id:
        cursor.execute("INSERT INTO Friends (user1_id, user2_id) VALUES ('{0}', '{1}')".format(user_id, friend_id))
        conn.commit()
    return flask.redirect(flask.url_for('hello'))

#End adding friend code
#----------------------------------------------------------------------End User Profile Code------------------------------------------------------------------------------#

#------------------------------------------------General Functionality (Includes homepage and all code relating to searches-----------------------------------------------#


#Search results
@app.route("/search", methods=['POST'])
def search_results():
    search = request.form.get('search')
    search_type = request.form.get('search_type')
    cursor = conn.cursor()
    error = False
    photos = []
    print(search)
    if search_type == 'user': #Search by username
        cursor.execute("SELECT user_id FROM Users WHERE Users.username = '{0}'".format(search))
        user_id = cursor.fetchone()
        if user_id: 
            user_id = user_id[0]
            cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE Pictures.user_id = '{0}'".format(user_id))
            photos = cursor.fetchall()
            photos = [list(photo) for photo in photos]
            [photo.append(search) for photo in photos]
            if not photos:
                error = True
        else: #No user with that username found
            error = True
    elif search_type == 'tags': #Search by tag
        tag = search
        if tag: #Checks that search field wasn't empty
            cursor.execute("SELECT picture_id FROM Tags WHERE tag_name = '{0}'".format(tag))
            picture_ids = cursor.fetchall()
            for picture in picture_ids:
                cursor.execute("SELECT imgdata, picture_id, caption, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture[0]))
                photo_data = list(cursor.fetchall()[0])
                cursor.execute("SELECT username FROM Users WHERE user_id = '{0}'".format(photo_data[3]))
                photo_data[3]=cursor.fetchone()[0]
                photos.append(photo_data)
            if not picture_ids:
                error = True
        else:
            error = True
    elif search_type == 'caption':
        error = True
    for photo in photos: #Runs on photos found (if any) and appends amount of likes and comments for each respective photo
        cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(photo[1]))
        likes = cursor.fetchone()
        if likes:
            photo.append(likes[0])
        else:
            photo.append(0)
        cursor.execute("SELECT picture_text, user_id FROM Comments WHERE picture_id = '{0}'".format(photo[1]))
        comments = cursor.fetchall()
        converter = [item for item in comments]
        for commenter in range(len(comments)):
            cursor.execute("SELECT username FROM Users WHERE user_id = '{0}'".format(comments[commenter][1]))
            comment = [comments[commenter][0], cursor.fetchone()]
            converter[commenter]=comment
        comments = converter
        if comments:
            photo.append(comments)
    return render_template("search.html", error = error, photos = photos, search = search, search_type = search_type)

#Search result when clicking on friends name in friends list
@app.route("/search/<string:other_user>", methods=['GET', 'POST'])
def otherUserPics(other_user):
    cursor.execute("SELECT user_id FROM Users WHERE username = '{0}'".format(other_user))
    user_id = cursor.fetchone()[0]
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE Pictures.user_id = '{0}'".format(user_id))
    photos = cursor.fetchall()
    photos = [list(photo) for photo in photos]
    [photo.append(other_user) for photo in photos]
    for photo in photos:
        cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(photo[1]))
        likes = cursor.fetchone()
        if likes:
            photo.append(likes[0])
        else:
            photo.append(0)
        cursor.execute("SELECT picture_text, user_id FROM Comments WHERE picture_id = '{0}'".format(photo[1]))
        comments = cursor.fetchall()
        converter = [item for item in comments]
        for commenter in range(len(comments)):
            cursor.execute("SELECT username FROM Users WHERE user_id = '{0}'".format(comments[commenter][1]))
            comment = [comments[commenter][0], cursor.fetchone()]
            converter[commenter]=comment
        comments = converter
        if comments:
            photo.append(comments)
    return render_template("pictures.html", album = other_user, photos = photos, info="posted by user", user=True)

#Search by clicking tag (Works anywhere on site where there is a tag)
@app.route("/search/tags/<string:tag_name>", methods=['GET', 'POST'])
def tag_search(tag_name):
    cursor = conn.cursor()
    error = False
    photos = []
    search = str(tag_name)
    cursor.execute("SELECT picture_id FROM Tags WHERE tag_name = '{0}'".format(search))
    picture_ids = cursor.fetchall()
    for picture in picture_ids:
        cursor.execute("SELECT imgdata, picture_id, caption, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture[0]))
        photo_data = list(cursor.fetchall()[0])
        cursor.execute("SELECT username FROM Users WHERE user_id = '{0}'".format(photo_data[3]))
        photo_data[3]=cursor.fetchone()[0]
        photos.append(photo_data)
        if not picture_ids:
            error = True
    for photo in photos: #Runs on photos found (if any) and adds the amount of likes that that picture has
        cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(photo[1]))
        likes = cursor.fetchone()
        if likes:
            photo.append(likes[0])
        else:
            photo.append(0)
    return render_template("search.html", error = error, photos = photos, search = search, search_type = "tags")

#Add comment to picture code begin
@app.route('/search/comment/<int:picture_id>', methods=['GET'])
@flask_login.login_required
def commentPage(picture_id):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
    photo_data = cursor.fetchone()
    if photo_data[3] == user_id:
        return render_template('hello.html', message="Can't comment on your own picture")
    else:
        return render_template("comment.html", photo = photo_data)

@app.route('/search/comment/<int:picture_id>', methods=['POST'])
@flask_login.login_required
def addComment(picture_id):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    comment = request.form.get("newcomment")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (user_id, picture_id, picture_text) VALUES ('{0}', '{1}', '{2}')".format(user_id, picture_id, comment))
    conn.commit()
    return flask.redirect(flask.url_for('hello'))
#Add comment to picture code end
    
#Liking Pictures
@app.route('/search/<int:picture_id>', methods=['GET', 'POST'])
@flask_login.login_required
def addLike(picture_id):
    user_id = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
    pic_owner = cursor.fetchone()[0]
    cursor.execute("SELECT * FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(user_id, picture_id))
    already_liked = cursor.fetchone()
    if user_id!=pic_owner and not already_liked:
        cursor.execute("INSERT INTO Likes (picture_id, user_id) VALUES ('{0}', '{1}')".format(picture_id, user_id))
        conn.commit()
    return flask.redirect(flask.url_for('hello'))

#default page
@app.route("/", methods=['GET'])
def hello():
    if request.method == 'GET':
        return render_template('hello.html', message='Welcome to Photoshare')

if __name__ == "__main__":
    #this is invoked when in the shell  you run
    #$ python app.py
    app.run(port=5000, debug=True)
