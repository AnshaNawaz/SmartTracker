#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response,jsonify
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime



# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera_opencv import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)

mysql = MySQL()

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


app.config["MYSQL_DATABASE_USER"] = 'root'
app.config["MYSQL_DATABASE_PASSWORD"] = ''
app.config["MYSQL_DATABASE_DB"] = 'fyp_db'
app.config["MYSQL_DATABASE_HOST"] = 'localhost'


mysql = MySQL(app)

class AppUser(object):

    def __init__(self,firstName="", lastName="", username="", password=""):
        self.username = username
        self.set_password(password)
        self.first_name = firstName
        self.last_name = lastName
        self.date_created = datetime.utcnow()

    def __str__(self):
        print("First Name : " + self.first_name)
        print("Last Name : " + self.last_name)
        print("Username : " + self.username)
        print("Date Created : " + str(self.date_created))

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def setFirstName(self,firstName):
        self.first_name=firstName

    def getFirstName(self):
        return self.first_name

    def setLastName(self,lastName):
        self.last_name = lastName

    def getLastName(self):
        return self.last_name

    def getDateCreated(self):
        return self.date_created


def isExists(username):
    conn = mysql.connect()
    cursor = conn.cursor()

    query = "select * from app_users where username = '" + username + "'"
    cursor.execute(query)
    user = cursor.fetchone()
    isAvailable = False
    if not user == None:
        isAvailable = True
    return isAvailable


@app.route('/api/v1.0/registerUser', methods=['POST'])
def registerUser(user):
    conn = mysql.connect()
    cursor = conn.cursor()

    if isExists(user.username) == True:
        print("Already Available")
        return False
    isRegistered = False
    query = "insert into app_users (first_name,last_name,username,password,date_created)"\
             + "values ('" + user.first_name + "','" + user.last_name + "','" + user.username\
             + "','" + generate_password_hash(user.pw_hash) + "','" \
             + str(datetime.utcnow()) + "')"

    try:
        cursor.execute(query)
        conn.commit()
        isRegistered = True
    except:
        conn.rollback()
        isRegistered = False

    conn.close()
    return isRegistered


@app.route('/api/v1.0/validateUser/<string:username>', methods=['GET'])
def validateUser(username):
    conn = mysql.connect()
    cursor = conn.cursor()

    isAvailable = isExists(username)
    if not isAvailable == False:
        password = 'khan'
        query = "select password from app_users where username = '" + username + "'"

        cursor.execute(query)
        userPassword = cursor.fetchone()
        if check_password_hash(userPassword,password) == True:
            isAvailable = True
        else:
            isAvailable = False
    return jsonify({'Status': isAvailable})


if __name__ == '__main__':
    app.debug = True

    app.run(host='0.0.0.0', threaded=True)
