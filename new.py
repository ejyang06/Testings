#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.

eugene wu 2015
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, \
     session, flash, url_for
from jinja2 import Template

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# Configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'


#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db1.cloudapp.net:5432/proj1part2
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db1.cloudapp.net:5432/proj1part2"
#
# Original database
#
# DATABASEURI = "sqlite:///test.db"

DATABASEURI = "postgresql://vg2321:286@w4111db1.cloudapp.net:5432/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
# Commit from Github
# 
# engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a POST or GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
# 
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  # DEBUG: this is debugging code to see what request looks like
  print request.args
  return redirect(url_for('login'))

# Register path
@app.route('/register/', methods=['POST'])
def add_entry():
    if session.get('logged_in'):
        return redirect(url_for('logout'))
    g.conn.execute('INSERT INTO Hikers (loginID, password) VALUES (?, ?)',
                 [request.form['userID'], request.form['Password']])
    g.conn.commit()
    flash('Welcome new hiker! Please log in')
    return redirect(url_for('login'))

# Login path

@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':

        cursor = g.conn.execute("SELECT loginID,pw FROM Hikers")
        loginID = []
        password = []
        for result in cursor:
            loginID.append(result[0])  # can also be accessed using result[0]
            password.append(result[1])
        cursor.close()

        if int(request.form['username']) not in loginID or request.form['username'] == "":
            error = 'Invalid username'

        # password is hard coded for now until change in the database
        
        elif (str(request.form['password']) != password[loginID.index(int(request.form['username']))].encode('utf8')) or str(request.form['password']) == "":
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_parks'))

    return render_template('login.html', error=error)

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route('/parks/', methods=['GET', 'POST'])
def show_parks():
    cur = g.conn.execute("SELECT name,type,state FROM Parks")
    parks = [dict(parkname=row[0], parktype=row[1],parkstate=row[2]) for row in cur.fetchall()]
    return render_template('show_parks.html', parks=parks)

@app.route('/trails/', methods=['GET', 'POST'])
def show_trails(): 
    cur = g.conn.execute("SELECT name,type,difficulty FROM Trails")
    trails = [dict(trailname=row[0], trailtype=row[1],traild=row[2]) for row in cur.fetchall()]
    return render_template('show_trails.html', trails=trails)

@app.route('/events/', methods=['GET', 'POST'])
def show_events():
    cur = g.conn.execute("select e.name, p.name FROM  parks p, events e WHERE p.parkid=e.parkid")
    events = [dict(eventname=row[0], eventpark=row[1]) for row in cur.fetchall()]
    return render_template('show_events.html', events=events)	


@app.route('/campsites/', methods=['GET', 'POST'])
def show_campsites():
    cur = g.conn.execute("select c.name, p.name, t.name from campsites c, parks p, trails t where p.parkid=c.parkid AND t.trailid=c.trailid")
    campsites = [dict(campname=row[0], camppark=row[1], camptrail=row[2]) for row in cur.fetchall()]
    return render_template('show_campsites.html', campsites=campsites)


@app.route('/comments/', methods=['GET', 'POST'])
def comments():
    cur = g.conn.execute("select p.name, c.content, u.name, c.postdate from parks p, comments c, users u where c.parkid=p.parkid AND u.userid=c.userid")
    comments = [dict(parkname=row[0], content=row[1], username=row[2], postdate=row[3]) for row in cur.fetchall()]
    return render_template('show_comments.html', comments=comments)
	
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
