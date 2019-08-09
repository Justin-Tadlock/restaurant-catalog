#!/usr/bin/env python3
from flask import (
    Flask,
    session as login_session,
    render_template,
    url_for,
    redirect,
    jsonify,
    flash,
    request,
    make_response
)

from database_setup import Base, User, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import psycopg2
import random
import string
import httplib2
import json
import requests
import bleach

from google.oauth2 import id_token
from google.auth.transport import requests


app = Flask(__name__)
app.debug = True

# Add the secret key for the app
try:
    app.secret_key = open('secret_key.txt', 'r').read()
except:
    print('ERROR: Please create a \'secret_key.txt\' file within the app\'s directory')


# Get Secrets Data
try:
    SECRET_DATA = json.loads(open('client_secrets.json', 'r').read())['web']
    CLIENT_ID = SECRET_DATA['client_id']
    CLIENT_SECRET = SECRET_DATA['client_secret']

    # Get the redirect uri from the file in the form of '/url'
    CLIENT_REDIRECT = SECRET_DATA['redirect_uris'][0]
    CLIENT_REDIRECT = '/%s' % (CLIENT_REDIRECT.split('/')[-1])
except:
    print('ERROR: Please download your \'client_secrets.json\' file from your \'https://console.developers.google.com\' project')


# Add the client id to all templates
try:
    app.add_template_global(name='client_id', f=CLIENT_ID)
except:
    print('ERROR: Could not add jinja2 global client id variable')


# Adding db functionality for CRUD operations
engine = create_engine('sqlite:///restaurantmenu.db?check_same_thread=False')
DBsession = sessionmaker(bind=engine)
session = DBsession()


def Log(msg, err=False):
    if not err and app.debug:
        print('INFO: %s' % (msg))
    else:
        print('ERROR: %s' % (msg))


def Is_Authenticated():
    return ('user' in login_session)


def Get_User_Info(user_info):
    Log('Enter: Get_User_Info')

    user = session.query(User).filter_by(
        name=user_info.get('name'), 
        email=user_info.get('email')
    ).one_or_none()
    
    if user is not None:
        Log('   Finding user %s... Found!' % (user.email))

        login_session['user'] = {
            'name': user.name,
            'email': user.email,
            'picture': user.picture,
            'user_id': user.id
        }

        Log('   login_session: %s' % json.dumps(login_session['user']))
        return True
    else:
        Log('   Finding user %s... Not found!' % (user_info.get('email')))
        return None
    
def Get_User_ID():
    if Is_Authenticated():
        return login_session['user']['user_id']
    else:
        return -1

def Add_User(user_info):
    Log('Enter: Add_User')

    name = user_info.get('name')
    email = bleach.clean(user_info.get('email'))
    picture = user_info.get('picture')

    try:
        new_user = User(name=name,
                        email=email,
                        picture=picture)
        session.add(new_user)
        session.commit()

        login_session['user'] = Get_User_Info(user_info)
        Log('   User_id: %d' % login_session['user']['user_id'])


        Log('Successfully added the user.')

        return True
    except:
        err_msg = (
            "".join((
                "Could not add the user to the db with the following information: \n",
                "{\n",
                "   name: ", name, "\n",
                "   email: ", email, "\n",
                "   picture: ", picture, "\n"
                "}"
            ))
        )
        Log(err_msg, True)

        return False


@app.route('/login')
def Login():
    return render_template('login.html', client_id=CLIENT_ID)


@app.route(CLIENT_REDIRECT, methods=['POST'])
def Google_Login():
    try:
        # Check if the POST request is trying to log in
        if 'idtoken' in request.form:
            if not Is_Authenticated():
                # Get the token from the POST form
                token = request.form['idtoken']

                # Specify the CLIENT_ID of the app that accesses the backend:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    CLIENT_ID
                )

                verified_providers = [
                    'accounts.google.com',
                    'https://accounts.google.com'
                ]

                if idinfo['iss'] not in verified_providers:
                    raise ValueError('Wrong issuer.')

                # ID token is valid.
                # Get the user's Google Account ID and the other profile
                # information from the decoded token, then add the token to
                # the flask session variable
                profile_info = {
                    'name': idinfo.get('name'),
                    'email': bleach.clean(idinfo.get('email')),
                    'picture': idinfo.get('picture')
                }
                Log(
                    'profile_info Details: %s' % 
                    json.dumps(profile_info)
                )

                # If we don't have the user in our db, add them.
                if Get_User_Info(profile_info) is None:
                    Log("User is not within the db. Adding them...")

                    # Attempt to add the user
                    if Add_User(profile_info) != True:
                        return make_response(jsonify(
                            message="Error, could not add the user to the database.",
                            status=501
                        ))

                Log('User has been successfully logged in.')

                ret_response = make_response(
                    jsonify(
                        message='Successfully verified. You are logged in!',
                        status=200)
                )

            # If the user is already logged in,
            # we don't need to do any authentication.
            else:
                Log('User is already logged in.')

                ret_response = make_response(
                    jsonify(message='User is already logged in.', status=201)
                )

        # If the POST request does not contain the idtoken field,
        # that means we are trying to log out.
        else:
            # When we have a logged in user,
            # we should remove their token from our
            # logged in sessions variable
            if Is_Authenticated():
                Log('User has been logged out.')

                login_session.pop('user', None)

            ret_response = make_response(
                jsonify(message="User has been logged out", status=200)
            )

    except ValueError:
        # Invalid token
        ret_response = make_response(
            jsonify(message='ERROR: unable to verify token id', status=401)
        )

    return ret_response


@app.route('/authenticated')
def Is_Logged_In():
    if Is_Authenticated():
        return make_response(
            jsonify(message="Logged in", status=201)
        )

    return make_response(
        jsonify(message="Not logged in", status=202)
    )

def Get_Restaurant_Data(rest_id):
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    appetizer_items = session.query(MenuItem).filter_by(
        course="Appetizer", restaurant_id=rest_id).all()
    drink_items = session.query(MenuItem).filter_by(
        course="Beverage", restaurant_id=rest_id).all()
    entree_items = session.query(MenuItem).filter_by(
        course="Entree", restaurant_id=rest_id).all()
    dessert_items = session.query(MenuItem).filter_by(
        course="Dessert", restaurant_id=rest_id).all()

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
    restaurants = session.query(Restaurant).all()

    return render_template(
        'show-all-restaurants.html',
        title="Restaurant Catalog",
        restaurants=restaurants,
        user_id=Get_User_ID()
    )


@app.route('/restaurant/<int:rest_id>/')
@app.route('/restaurant/<int:rest_id>/menu')
def Show_Restaurant(rest_id):
    rest_data = Get_Restaurant_Data(rest_id)

    return render_template('show-restaurant.html',
                           restaurant=rest_data['restaurant'],
                           appetizer_items=rest_data['appetizers'],
                           drink_items=rest_data['drinks'],
                           entree_items=rest_data['entrees'],
                           dessert_items=rest_data['desserts'],
                           user_id=Get_User_ID())


@app.route('/restaurant/add/', methods=['GET', 'POST'])
def Add_Restaurant():
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to add a restaurant.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        new_restaurant = Restaurant(
            name=request.form['rest_name'], 
            user_id=login_session['user']['user_id']
        )

        session.add(new_restaurant)
        session.commit()

        flash('Successfully added %s.' % (new_restaurant.name))

        return redirect(url_for('Show_All_Restaurants'))
    else:
        return render_template('add-restaurant.html',
                               back_url=url_for('Show_All_Restaurants'))


@app.route('/restaurant/<int:rest_id>/edit', methods=['GET', 'POST'])
def Edit_Restaurant(rest_id):
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to edit a restaurant.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        updated_restaurant = session.query(
            Restaurant).filter_by(id=rest_id).one()

        if updated_restaurant.user_id == login_session['user']['user_id']:
            updated_restaurant.name = request.form['rest_name']
            session.add(updated_restaurant)
            session.commit()

            flash('Successfully updated %s.' % (updated_restaurant.name))
        else:
            flash('Error: You are not authorized to modify %s.' % (updated_restaurant.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    else:
        rest_data = Get_Restaurant_Data(rest_id)

        return render_template('edit-restaurant.html',
                               back_url=url_for('Show_All_Restaurants'),
                               restaurant=rest_data['restaurant'],
                               appetizer_items=rest_data['appetizers'],
                               drink_items=rest_data['drinks'],
                               entree_items=rest_data['entrees'],
                               dessert_items=rest_data['desserts'],
                               user_id=Get_User_ID())


@app.route('/restaurant/<int:rest_id>/delete', methods=['GET', 'POST'])
def Delete_Restaurant(rest_id):
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to delete a restaurant.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

        if restaurant.user_id == login_session['user']['user_id']:
            if restaurant != []:
                session.query(MenuItem).filter_by(restaurant_id=rest_id).delete()

            flash('Successfully deleted %s.' % (restaurant.name))

            session.delete(restaurant)
            session.commit()
        else:
            flash('Error: You are not authorized to delete %s' % restaurant.name)

        return redirect(url_for('Show_All_Restaurants'))
    else:
        rest_data = Get_Restaurant_Data(rest_id)

        return render_template('delete-restaurant.html',
                               back_url=url_for('Show_All_Restaurants'),
                               restaurant=rest_data['restaurant'],
                               appetizer_items=rest_data['appetizers'],
                               drink_items=rest_data['drinks'],
                               entree_items=rest_data['entrees'],
                               dessert_items=rest_data['desserts'],
                               user_id=Get_User_ID())


@app.route('/restaurants/all/items/')
def Show_All_Items():
    items = session.query(MenuItem).all()

    return render_template('show-all-items.html', menu_items=items)


@app.route('/restaurant/<int:rest_id>/add', methods=['GET', 'POST'])
def Add_Menu_Item(rest_id):
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to add a menu item.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        form = request.form

        new_menu_item = MenuItem(
            name=form['item_name'],
            price=form['item_price'],
            course=form['item_course'],
            description=form['item_description'],
            restaurant_id=rest_id,
            user_id=login_session['user']['user_id']
        )

        session.add(new_menu_item)
        session.commit()

        flash("Successfully added %s." % (new_menu_item.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    else:
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

        return render_template('add-menu-item.html', restaurant=restaurant)
    return render_template('add-menu-item.html',
                           back_url=url_for('Edit_Restaurant',
                                            rest_id=rest_id),
                           restaurant=restaurant,
                           user_id=Get_User_ID())


@app.route('/restaurant/<int:rest_id>/edit/<int:item_id>/', methods=['GET', 'POST'])
def Edit_Menu_Item(rest_id, item_id):
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to edit a menu item.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        form = request.form

        menu_item = session.query(MenuItem).filter_by(id=item_id).one()

        if menu_item.user_id == login_session['user']['user_id']:
            menu_item.name = form['item_name']
            menu_item.price = form['item_price']
            menu_item.course = form['item_course']
            menu_item.description = form['item_description']

            session.add(menu_item)
            session.commit()

            flash('Successfully updated %s.' % (menu_item.name))
        else:
            flash('Error: You are not authorized to modify %s.' % menu_item.name)

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    else:
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        item = session.query(MenuItem).filter_by(id=item_id).one()

        return render_template('edit-menu-item.html',
                               back_url=url_for(
                                   'Edit_Restaurant', rest_id=rest_id),
                               item=item,
                               user_id=Get_User_ID())


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/', methods=['GET', 'POST'])
def Delete_Menu_Item(rest_id, item_id):
    if not Is_Authenticated():
        flash('Warning: You are not logged in. You must log in to delete a menu item.')
        return redirect(url_for('Show_All_Restaurants'))

    if request.method == 'POST':
        menu_item = session.query(MenuItem).filter_by(id=item_id).one()
        if menu_item != [] and menu_item.user_id == login_session['user']['user_id']:
            session.delete(menu_item)
            session.commit()

            flash('Successfully removed %s.' % (menu_item.name))
        else:
            flash('Error: You are not authorized to delete %s.' % menu_item.name)

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))

    else:
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        item = session.query(MenuItem).filter_by(id=item_id).one()

        return render_template('delete-menu-item.html',
                               back_url=url_for(
                                   'Edit_Restaurant', rest_id=rest_id),
                               item=item,
                               user_id=Get_User_ID())


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
    item = session.query(MenuItem).filter_by(
        restaurant_id=rest_id, id=item_id).one()

    return jsonify(MenuItem=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'my_super_secret_but_not_really_key'
    app.run(host='0.0.0.0', port=5000)
