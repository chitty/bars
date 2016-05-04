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


CLIENT_ID = json.loads(
       open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Bar Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///bars.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    """Creates anti-forgery state token and renders login page"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Sign in with Google+"""
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
    login_session['provider'] = 'google'
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

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    username = login_session['username']
    flash("you are now logged in as %s" % username)
    return username


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Sign In with facebook"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secret.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secret.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "http://graph.facebook.com/v2.5/me"
    token = result.split('&')[0]

    url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Get user picture
    url = "https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    username = login_session['username']
    flash("you are now logged in as %s" % username)
    return username


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['credentials']
            del login_session['gplus_id']
        elif login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("Successfully logged out." )
    else:
        flash("You were not logged in.")
    return redirect(url_for('showBars'))


def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]


def gdisconnect():
    credentials = login_session.get('credentials')
    access_token = credentials.access_token
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]


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
        newBar = Bar(name=request.form['name'], user_id=login_session['user_id'])
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
    if 'username' not in login_session:
        return redirect('login')
    elif editedBar.user_id != login_session['user_id']:
        flash('You are not authorized to edit this bar!')
        return redirect(url_for('showBars'))
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
    barToDelete = session.query(Bar).filter_by(id=bar_id).one()
    if 'username' not in login_session:
        return redirect('login')
    elif barToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete this bar!')
        return redirect(url_for('showBars'))
    if request.method == 'POST':
        session.delete(barToDelete)
        flash('%s Successfully Deleted' % barToDelete.name)
        session.commit()
        return redirect(url_for('showBars'))
    else:
        return render_template('delete_bar.html', bar=barToDelete)


@app.route('/bar/<int:bar_id>/')
@app.route('/bar/<int:bar_id>/menu/')
def showMenu(bar_id):
    bar = session.query(Bar).filter_by(id=bar_id).one()
    creator = getUserInfo(bar.user_id)
    drinks = session.query(Drink).filter_by(bar_id=bar_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_menu.html', drinks=drinks, bar=bar, creator=creator)
    else:
        return render_template('menu.html', drinks=drinks, bar=bar, creator=creator)


@app.route('/bar/<int:bar_id>/menu/new/', methods=['GET', 'POST'])
def newDrink(bar_id):
    if request.method == 'POST':
        newDrink = Drink(name=request.form['name'],
                         description=request.form['description'],
                         price=request.form['price'], bar_id=bar_id,
                         user_id=login_session['user_id'])
        session.add(newDrink)
        session.commit()
        flash('New Drink %s Successfully Created' % (newDrink.name))
        return redirect(url_for('showMenu', bar_id=bar_id))
    else:
        return render_template('new_drink.html', bar_id=bar_id)


@app.route('/bar/<int:bar_id>/menu/<int:drink_id>/edit', methods=['GET', 'POST'])
def editDrink(bar_id, drink_id):

    editedDrink = session.query(Drink).filter_by(id=drink_id).one()
    if 'username' not in login_session:
        return redirect('login')
    elif editedDrink.user_id != login_session['user_id']:
        flash('You are not authorized to edit this drink!')
        return redirect(url_for('showMenu', bar_id=bar_id))
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


@app.route('/bar/<int:bar_id>/menu/<int:drink_id>/delete', methods=['GET', 'POST'])
def deleteDrink(bar_id, drink_id):
    drinkToDelete = session.query(Drink).filter_by(id=drink_id).one()
    if 'username' not in login_session:
        return redirect('login')
    elif drinkToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete this drink!')
        return redirect(url_for('showMenu', bar_id=bar_id))
    if request.method == 'POST':
        session.delete(drinkToDelete)
        session.commit()
        flash('Drink Successfully Deleted')
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
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
