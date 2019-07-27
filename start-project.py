#!/usr/bin/env python3
from flask import Flask, render_template, url_for, redirect, jsonify, flash, request
from flask import session as login_session
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

# Adding db functionality for CRUD operations
engine = create_engine('sqlite:///restaurantmenu.db?check_same_thread=False')
DBsession = sessionmaker(bind=engine)
session = DBsession()


@app.route('/login')
def Login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(1,32))
    login_session['state'] = state
    
    return render_template('login.html', STATE=state)

@app.route('/gdisconnect', methods=['POST'])
def Google_Logout():
    if login_session.get('access_token') is not None and login_session.get('connect_id') is not None:
        for property in login_session.keys():
            login_session.pop(login_session[property], None)

        flash('You have been successfully logged out.')
    
    return redirect(url_for('Show_All_Restaurants'))

@app.route('/gconnect', methods=['POST'])
def Google_Login():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)

        response.headers['content-type'] = 'application/json'

        return response
    else:
        code = request.data

        # Update the authentication code
        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'

            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to update the authentication code'), 401)
            response.headers['content-type'] = 'application/json'
            dir(response)
            
            return response

        # Validate token code
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])

        if result.get('error') is not None:
            response = make_response(json.dumps('Error: Could not validate the access token'), 401)
            response.headers['content-type'] = 'application/json'
            
            return response

        # Verify token for a given user
        user_id = credentials.id_token['sub']
        if result['user_id'] != user_id:
            response = make_response(json.dumps('Error: The user ID does not match the given ID.'), 401)
            response.headers['content-type'] = 'application/json'

            return response
        
        # Verify the token is valid for this app
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps('Error: Client ID does not match the app\'s id.'), 401)
            response.headers['content-type'] = 'application/json'
            print("Error: The client ID does not match the App's ID")

            return response
        stored_access_token = login_session.get('access_token')
        stored_connect_id = login_session.get('connect_id')
        if stored_access_token is not None and stored_connect_id is not None:
            response = make_response(json.dumps('User is already connected'), 200)
            response.headers['content-type'] = 'application/json'
            response.headers['status'] = 200

            return response

        # Store the token and id for later use
        login_session['access_token'] = credentials.access_token
        login_session['connect_id'] = user_id

        # Get user info
        user_info_uri = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = { 'access_token': credentials.access_token, 'alt':'json' }
        answer = requests.get(user_info_uri, params=params)
        data = answer.json()

        # Set the login session user info
        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']

        flash('You are successfully logged in!')

        response = make_response(json.dumps('Logged in successfuly!'), status=200)
        response.headers['content-type'] = 'application/json'

        return response

def Get_Restaurant_Data(rest_id):
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    appetizer_items = session.query(MenuItem).filter_by(course="Appetizer", restaurant_id=rest_id).all()
    drink_items = session.query(MenuItem).filter_by(course="Beverage", restaurant_id=rest_id).all()
    entree_items = session.query(MenuItem).filter_by(course="Entree", restaurant_id=rest_id).all()
    dessert_items = session.query(MenuItem).filter_by(course="Dessert", restaurant_id=rest_id).all()

    rest_data = {
        "restaurant": restaurant,
        "appetizers": appetizer_items,
        "drinks": drink_items,
        "entrees": entree_items,
        "desserts": dessert_items
    }

    return rest_data

@app.route('/restaurants/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def Show_All_Restaurants():

    if request.method == 'POST':
        print(login_session['state'])
        login_session.pop('state', None)

    restaurants = session.query(Restaurant).all()
    
    return render_template('show-all-restaurants.html', restaurants=restaurants)


@app.route('/restaurant/<int:rest_id>/')
@app.route('/restaurant/<int:rest_id>/menu')
def Show_Restaurant(rest_id):
    rest_data = Get_Restaurant_Data(rest_id)

    return render_template('show-restaurant.html', 
                            restaurant=rest_data['restaurant'], 
                            appetizer_items=rest_data['appetizers'], 
                            drink_items=rest_data['drinks'],
                            entree_items=rest_data['entrees'],
                            dessert_items=rest_data['desserts'])


@app.route('/restaurant/add/', methods=['GET', 'POST'])
def Add_Restaurant():
    if request.method == 'POST':
        new_restaurant = Restaurant(name = request.form['rest_name'])

        session.add(new_restaurant)
        session.commit()

        flash('Successfully added %s.' % (new_restaurant.name))

        return redirect(url_for('Show_All_Restaurants'))

    return render_template('add-restaurant.html')


@app.route('/restaurant/<int:rest_id>/edit', methods=['GET', 'POST'])
def Edit_Restaurant(rest_id):
    if request.method == 'POST':
        updated_restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        updated_restaurant.name = request.form['rest_name']

        session.add(updated_restaurant)
        session.commit()

        flash('Successfully updated %s.' % (updated_restaurant.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    
    rest_data = Get_Restaurant_Data(rest_id)

    return render_template('edit-restaurant.html', 
                            restaurant=rest_data['restaurant'], 
                            appetizer_items=rest_data['appetizers'], 
                            drink_items=rest_data['drinks'],
                            entree_items=rest_data['entrees'],
                            dessert_items=rest_data['desserts'])


@app.route('/restaurant/<int:rest_id>/delete', methods=['GET', 'POST'])
def Delete_Restaurant(rest_id):
    if request.method == 'POST':
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        if restaurant != []:
            session.query(MenuItem).filter_by(restaurant_id=rest_id).delete()
        
        flash('Successfully deleted %s.' % (restaurant.name))

        session.delete(restaurant)
        session.commit()

        return redirect(url_for('Show_All_Restaurants'))
    
    rest_data = Get_Restaurant_Data(rest_id)

    return render_template('delete-restaurant.html', 
                            restaurant=rest_data['restaurant'], 
                            appetizer_items=rest_data['appetizers'], 
                            drink_items=rest_data['drinks'],
                            entree_items=rest_data['entrees'],
                            dessert_items=rest_data['desserts'])


@app.route('/restaurants/all/items/')
def Show_All_Items():
    items = session.query(MenuItem).all()

    return render_template('show-all-items.html', menu_items=items)


@app.route('/restaurant/<int:rest_id>/add', methods=['GET', 'POST'])
def Add_Menu_Item(rest_id):
    if request.method == 'POST':
        form = request.form

        new_menu_item = MenuItem(
            name = form['item_name'],
            price = form['item_price'],
            course = form['item_course'],
            description = form['item_description'],
            restaurant_id = rest_id
        )

        session.add(new_menu_item)
        session.commit()

        flash("Successfully added %s." % (new_menu_item.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))

    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

    return render_template('add-menu-item.html', restaurant=restaurant)

@app.route('/restaurant/<int:rest_id>/edit/<int:item_id>/', methods=['GET', 'POST'])
def Edit_Menu_Item(rest_id, item_id):
    if request.method == 'POST':
        form = request.form 

        updated_item = session.query(MenuItem).filter_by(id=item_id).one()

        updated_item.name = form['item_name']
        updated_item.price = form['item_price']
        updated_item.course = form['item_course']
        updated_item.description = form['item_description']

        session.add(updated_item)
        session.commit()

        flash('Successfully updated %s.' % (updated_item.name)) 

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))

    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    item = session.query(MenuItem).filter_by(id=item_id).one()

    return render_template('edit-menu-item.html', restaurant=restaurant, item=item)


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/', methods=['GET', 'POST'])
def Delete_Menu_Item(rest_id, item_id):
    if request.method == 'POST':
        item_to_delete = session.query(MenuItem).filter_by(id=item_id).one()
        if item_to_delete != []:
            session.delete(item_to_delete)
            session.commit()

            flash('Successfully removed %s.' % (item_to_delete.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    item = session.query(MenuItem).filter_by(id=item_id).one()

    return render_template('delete-menu-item.html', restaurant=restaurant, item=item)


@app.route('/restaurants/JSON')
def Get_Restaurants_JSON():
    restaurants_json = session.query(Restaurant).all()

    return jsonify(Restaurants=[i.serialize for i in restaurants_json])


@app.route('/restaurant/<int:rest_id>/JSON')
def Get_Restaurant_JSON(rest_id):
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

    return jsonify(Restaurant=restaurant.serialize)

@app.route('/restaurant/<int:rest_id>/item/<int:item_id>/JSON')
def Get_Menu_Item_JSON(rest_id, item_id):
    item = session.query(MenuItem).filter_by(restaurant_id=rest_id, id=item_id).one()

    return jsonify(MenuItem=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'my_super_secret_but_not_really_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
