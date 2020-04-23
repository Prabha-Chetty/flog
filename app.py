from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os
import requests

app = Flask(__name__)
Bootstrap(app)

db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)
CKEditor(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    res_value = cur.execute("Select * from blog")
    if res_value > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html', blogs=blogs)
    cur.close()
    return render_template('index.html', blogs=None)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>/')
def blogs(id):
    cur = mysql.connection.cursor()
    res_value = cur.execute("Select * from blog where blog_id = {}".format(id))
    if res_value > 0:
        blog = cur.fetchone()
        return render_template('blogs.html', blog=blog)
    return 'Blog not found'

@app.route('/register/', methods=['GET','POST'])
def register():
    if request.method=='POST':
        userDetails = request.form
        if userDetails['password'] != userDetails['confirm_password']:
            flash('Password do not match! Try Again', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        cur.execute("Insert into user(first_name,last_name,username,email,password) Values(%s,%s,%s,%s,%s)",(userDetails['first_name'],userDetails['last_name'],userDetails['username'],userDetails['email'],generate_password_hash(userDetails['password'])))
        mysql.connection.commit()
        cur.close()
        flash('Registration succesful! Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        username = userDetails['username']
        cur = mysql.connection.cursor()
        res_value = cur.execute("Select * from user where username = %s",([username]))
        if res_value > 0:
            user = cur.fetchone()
            if check_password_hash(user['password'],userDetails['password']):
                session['login'] = True
                session['firstName'] = user['first_name']
                session['lastName'] = user['last_name']
                flash('Welcome ' + session['firstName'] + '! You have loggedin successfully', 'success')
            else:
                cur.close()
                flash('Credentials did not match', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog/',methods=['GET','POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['firstName']+ ' '+ session['lastName']
        cur = mysql.connection.cursor()
        cur.execute("Insert into blog(title, body, author) Values(%s, %s, %s)",(title,body,author))
        mysql.connection.commit()
        cur.close()
        flash("successfully posted new blog", 'success')
        return redirect('/')
    return render_template('write-blog.html')

@app.route('/my-blogs/')
def my_blogs():
    author = session['firstName']+ ' ' + session['lastName']
    cur = mysql.connection.cursor()
    res_value = cur.execute("Select * from blog where author = %s",[author])
    if res_value > 0:
        my_blogs = cur.fetchall()
        return render_template('my-blogs.html', my_blogs=my_blogs)
    else:
        return render_template('my-blogs.html', my_blogs=None)

@app.route('/edit-blog/<int:id>/',methods=['GET','POST'])
def edit_blog(id):
    if request.method == 'POST':
        editBlog = request.form
        title = editBlog['title']
        body = editBlog['body']
        cur = mysql.connection.cursor()
        cur.execute("Update blog set title = %s, body = %s where blog_id = %s",(title,body,id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully', 'success')
        return redirect('/blogs/{}'.format(id))
    cur = mysql.connection.cursor()
    res_value = cur.execute("Select * from blog where blog_id = {}".format(id))
    if res_value > 0 :
        blogDetails = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blogDetails['title']
        blog_form['body'] = blogDetails['body']
        return render_template('edit-blog.html',blog_form = blog_form)

@app.route('/delete-blog/<int:id>')
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("Delete from blog where blog_id = {}".format(id))
    mysql.connection.commit()
    flash("Deleted blog successfully", 'success')
    return redirect('/my-blogs')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out", 'success')
    return redirect('/')

@app.route('/covid19india', methods=['GET','POST'])
def covid19india():
    #request.get("https://api.covid19india.org/data.json")
    data = requests.get("https://api.covid19india.org/data.json")
    contents = data.json()
    content = []
    if request.method == 'POST':
        searchData = request.form
        statename = searchData['statename']
        newcontents = next((item for item in contents['statewise'] if item['state'] == statename), None)
        content.append(newcontents)
    else:
        content = contents['statewise']
    return render_template('covid-report.html', contents = content)

if __name__ == '__main__':
    app.run(debug=True)
