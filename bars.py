from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import make_response, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Bar, Drink, User
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)


# @todo
# CLIENT_ID = json.loads(
#        open('client_secret.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "Bar Menu Application"
CLIENT_ID = 1


# Connect to Database and create database session
engine = create_engine('sqlite:///bars.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(data['name'])
    if not user_id:
        user_id = createUser(data)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        print 'result is '
        print result
        if result['status'] == '200':
            del login_session['access_token'] 
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            response = make_response(json.dumps('Successfully disconnected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
        else:

            response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            return response


# JSON APIs to view Bar Information
@app.route('/bar/<int:bar_id>/menu/JSON')
def barMenuJSON(bar_id):
    bar = session.query(Bar).filter_by(id=bar_id).one()
    drinks = session.query(Drink).filter_by(
        bar_id=bar_id).all()
    return jsonify(Bars=[i.serialize for i in drinks])


@app.route('/bar/<int:bar_id>/menu/<int:drink_id>/JSON')
def barJSON(bar_id, drink_id):
    drink = session.query(Drink).filter_by(id=drink_id).one()
    return jsonify(drink=drink.serialize)


@app.route('/bar/JSON')
def barsJSON():
    bars = session.query(Bar).all()
    return jsonify(bars=[r.serialize for r in bars])


# Show all bars
@app.route('/')
@app.route('/bar/')
def showBars():
    bars = session.query(Bar).order_by(asc(Bar.name))
    return render_template('bars.html', bars=bars)


# Create a new bar
@app.route('/bar/new/', methods=['GET', 'POST'])
def newBar():
    if request.method == 'POST':
        newBar = Bar(name=request.form['name'], user_id=1)  # @todo: login_session['user_id'])
        session.add(newBar)
        flash('New Bar %s Successfully Created' % newBar.name)
        session.commit()
        return redirect(url_for('showBars'))
    else:
        return render_template('new_bar.html')


# Edit a bar
@app.route('/bar/<int:bar_id>/edit/', methods=['GET', 'POST'])
def editBar(bar_id):
    editedBar = session.query(Bar).filter_by(id=bar_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBar.name = request.form['name']
            flash('Bar Successfully Edited %s' % editedBar.name)
            return redirect(url_for('showBars'))
    else:
        return render_template('edit_bar.html', bar=editedBar)


# Delete a bar
@app.route('/bar/<int:bar_id>/delete/', methods=['GET', 'POST'])
def deleteBar(bar_id):
    barToDelete = session.query(
        Bar).filter_by(id=bar_id).one()
    if request.method == 'POST':
        session.delete(barToDelete)
        flash('%s Successfully Deleted' % barToDelete.name)
        session.commit()
        return redirect(url_for('showBars', bar_id=bar_id))
    else:
        return render_template('delete_bar.html', bar=barToDelete)

# Show a bar menu


@app.route('/bar/<int:bar_id>/')
@app.route('/bar/<int:bar_id>/menu/')
def showMenu(bar_id):
    bar = session.query(Bar).filter_by(id=bar_id).one()
    drinks = session.query(Drink).filter_by(bar_id=bar_id).all()
    return render_template('menu.html', drinks=drinks, bar=bar)


# Create a new menu item
@app.route('/bar/<int:bar_id>/menu/new/', methods=['GET', 'POST'])
def newDrink(bar_id):
    if request.method == 'POST':
        newDrink = Drink(name=request.form['name'],
                         description=request.form['description'],
                         price=request.form['price'], bar_id=bar_id,
                         user_id=1)  # @todo: login_session['user_id'])
        session.add(newDrink)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newDrink.name))
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('new_drink.html', bar_id=bar_id)


# Edit a menu item
@app.route('/bar/<int:bar_id>/menu/<int:drink_id>/edit', methods=['GET', 'POST'])
def editDrink(bar_id, drink_id):

    editedDrink = session.query(Drink).filter_by(id=drink_id).one()
    if request.method == 'POST':
        if request.form.get('name'):
            editedDrink.name = request.form['name']
        if request.form.get('description'):
            editedDrink.description = request.form['description']
        if request.form.get('price'):
            editedDrink.price = request.form['price']
        session.add(editedDrink)
        session.commit()
        flash('Drink Successfully Edited')
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('edit_drink.html', bar_id=bar_id, drink_id=drink_id, drink=editedDrink)


# Delete a menu item
@app.route('/bar/<int:bar_id>/menu/<int:drink_id>/delete', methods=['GET', 'POST'])
def deleteDrink(bar_id, drink_id):
    drinkToDelete = session.query(Drink).filter_by(id=drink_id).one()
    if request.method == 'POST':
        session.delete(drinkToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('delete_drink.html', drink=drinkToDelete)


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)