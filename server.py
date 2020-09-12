from flask import Flask, render_template, redirect, request, session, flash, jsonify
from flask_bcrypt import Bcrypt   
from mysqlconnection import connectToMySQL
from datetime import datetime

import re   # "re"regular expression operations
import pymysql
import pymysql.cursors #makes data sent as python dictionaries

mysql = connectToMySQL('forumsdb')

# used for email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__) 
bcrypt = Bcrypt(app)  
app.secret_key = "ThisIsSecret!"

# =====================================================
#                     INDEX ROUTE
# =====================================================
@app.route('/')
def index():
    mysql = connectToMySQL('forumsdb')
    return render_template('index.html')

# =======================================================
#                  REGISTER BUTTON ROUTE
# =======================================================
@app.route('/register', methods=['POST'])
def register():

    # name validation
    # --------------------------------------
    if len(request.form['fname']) < 2:
        flash("first name must be at least 2 characters", 'fname')
    if len(request.form['lname']) < 2:
        flash("last name must be at least 2 characters", 'lname')
    
    # new-email validation
    # --------------------------------------
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'email')

    # checking if email already exists in db
    # --------------------------------------
    mysql = connectToMySQL('forumsdb')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email']}
    matchingEmail = mysql.query_db(query, data)

    if matchingEmail:
        flash("Email already exists", 'email')
    
    # new-password validation
    # --------------------------------------
    if len(request.form['password']) < 8:
        flash("password must be at least 8 characters", 'password')
    
    # confirm-password validation
    # --------------------------------------
    if request.form['password'] != request.form['confirm-password']:
        flash("passwords don't match", 'confirm-password')
    
    # initiate any flash messages on index.html
    # --------------------------------------
    if '_flashes' in session.keys():
        return redirect("/")

    # ADD NEW USER TO DATABASE : hash password
    # --------------------------------------
    else:
        mysql = connectToMySQL('forumsdb')
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 

        query = "INSERT INTO users (first_name, last_name, email, password_hash, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s, NOW(), NOW());"
        data = {
             "first_name": request.form['fname'],
             "last_name": request.form['lname'],
             "email": request.form['email'],
             "password_hash": pw_hash,
        }
        new_user_id=mysql.query_db(query, data)

        # get user_id and store into session
        session['user_id'] = new_user_id
        session['user_name'] = request.form['fname']
        print('SESSION:', session)
        flash("Aww yeah, you successfully registered.  You can now log in using the same information you provided!", 'success')

        return redirect('/')
    

# =======================================================
#                  LOGIN BUTTON ROUTE
# =======================================================
@app.route('/login', methods=['POST'])
def login():
    
    # check if email exists in database
    # --------------------------------------
    mysql = connectToMySQL('forumsdb')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email'] }
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password_hash'], request.form['password']):
            
            # if True: store some user data in session
            session['user_id'] = result[0]['id']
            session['user_name'] = result[0]['first_name']

            return redirect('/getMessages')
    
        # if username & password don't match
        # --------------------------------------
        else:
            flash("You could not be logged in", 'login')
            return redirect("/")


# =======================================================
#           /getMessages: after logging in
# =======================================================
@app.route('/getMessages', methods=['GET'])
def getMessages():
    user_id = session['user_id']

    # data to show "ALL messages", newest first, 5 max
    # -------------------------------------------
    mysql = connectToMySQL('forumsdb')
    message_query = "SELECT messages.id, messages.user_id, messages.message, messages.updated_at, users.id, users.first_name FROM messages JOIN users ON messages.user_id = users.id ORDER BY messages.id DESC LIMIT 5;"
  
    result = mysql.query_db(message_query)
    print(result)
    # SEND ALL OF THIS DATA TO BE MANIPULATED ON HTML
    return render_template('messages.html', messages=result)


# =====================================================
#                 CREATE A MESSAGE
# =====================================================
@app.route('/create', methods=['POST'])
def create():
    user_id = session['user_id']

    mysql = connectToMySQL("forumsdb")
    query= "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (%(user_id)s, %(message)s, NOW(), NOW());"
    data = {
        'user_id': session['user_id'],
        'message': request.form['create']
        }
    mysql.query_db(query, data)

    return redirect('/getMessages')


# # =====================================================
# #                 DELETE A MESSAGE
# # =====================================================
# @app.route('/delete_message', methods=['POST'])
# def delete_message():

#     mysql = connectToMySQL("forumsdb")
#     query = "DELETE FROM messages WHERE (id = %(messagesId)s);"
#     data = {
#         'messagesId': request.form['messagesId']
#     }
#     mysql.query_db(query, data)

#     return redirect('/getData')


# ====================================================
#        LOG OUT: clear session
# ====================================================
@app.route('/logout', methods=['POST'])
def logout():
    return redirect('/clear_session')
# ----------------------------------------
@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect('/')


# =======================================================
#         START SERVER **********
# =======================================================
if __name__ == "__main__":
    app.run(debug=True)



