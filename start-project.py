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

from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import psycopg2
import random
import string
import httplib2
import json
import requests

import google_authentication as gAuth


app = Flask(__name__)

# Add the secret key for the app
try:
    app.secret_key = open('secret_key.txt', 'r').read()
except:
    print('Error: Please create a \'secret_key.txt\' file within the app\'s directory')

# Add the client id to all templates
try:
    app.add_template_global(name='client_id', f=gAuth.CLIENT_ID)
except:
    print('Error: Could not add jinja2 global client id variable')


# Adding db functionality for CRUD operations
engine = create_engine('sqlite:///restaurantmenu.db?check_same_thread=False')
DBsession = sessionmaker(bind=engine)
session = DBsession()


@app.route('/login')
def Login():
    return render_template('login.html', client_id=gAuth.CLIENT_ID)


@app.route(gAuth.CLIENT_REDIRECT, methods=['POST'])
def Google_Login():
    return gAuth.Authentication_Callback()


@app.route('/authenticated')
def Is_Logged_In():
    if gAuth.Is_Authenticated():
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
        client_id=gAuth.CLIENT_ID,
        restaurants=restaurants
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
                           dessert_items=rest_data['desserts'])


@app.route('/restaurant/add/', methods=['GET', 'POST'])
def Add_Restaurant():
    if request.method == 'POST' and gAuth.Is_Authenticated():
        new_restaurant = Restaurant(name=request.form['rest_name'])

        session.add(new_restaurant)
        session.commit()

        flash('Successfully added %s.' % (new_restaurant.name))

        return redirect(url_for('Show_All_Restaurants'))
    elif gAuth.Is_Authenticated():
        return render_template('add-restaurant.html')
    else:
        return redirect(url_for('Show_All_Restaurants'))


@app.route('/restaurant/<int:rest_id>/edit', methods=['GET', 'POST'])
def Edit_Restaurant(rest_id):
    if request.method == 'POST' and gAuth.Is_Authenticated():
        updated_restaurant = session.query(
            Restaurant).filter_by(id=rest_id).one()
        updated_restaurant.name = request.form['rest_name']

        session.add(updated_restaurant)
        session.commit()

        flash('Successfully updated %s.' % (updated_restaurant.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    elif gAuth.Is_Authenticated():
        rest_data = Get_Restaurant_Data(rest_id)

        return render_template('edit-restaurant.html',
                               restaurant=rest_data['restaurant'],
                               appetizer_items=rest_data['appetizers'],
                               drink_items=rest_data['drinks'],
                               entree_items=rest_data['entrees'],
                               dessert_items=rest_data['desserts'])

    else:
        return redirect(url_for('Show_All_Restaurants'))


@app.route('/restaurant/<int:rest_id>/delete', methods=['GET', 'POST'])
def Delete_Restaurant(rest_id):
    if request.method == 'POST' and gAuth.Is_Authenticated():
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        if restaurant != []:
            session.query(MenuItem).filter_by(restaurant_id=rest_id).delete()

        flash('Successfully deleted %s.' % (restaurant.name))

        session.delete(restaurant)
        session.commit()

        return redirect(url_for('Show_All_Restaurants'))
    elif gAuth.Is_Authenticated():
        rest_data = Get_Restaurant_Data(rest_id)

        return render_template('delete-restaurant.html',
                               restaurant=rest_data['restaurant'],
                               appetizer_items=rest_data['appetizers'],
                               drink_items=rest_data['drinks'],
                               entree_items=rest_data['entrees'],
                               dessert_items=rest_data['desserts'])
    else:
        return redirect(url_for('Show_All_Restaurants'))


@app.route('/restaurants/all/items/')
def Show_All_Items():
    items = session.query(MenuItem).all()

    return render_template('show-all-items.html', menu_items=items)


@app.route('/restaurant/<int:rest_id>/add', methods=['GET', 'POST'])
def Add_Menu_Item(rest_id):
    if request.method == 'POST' and gAuth.Is_Authenticated():
        form = request.form

        new_menu_item = MenuItem(
            name=form['item_name'],
            price=form['item_price'],
            course=form['item_course'],
            description=form['item_description'],
            restaurant_id=rest_id
        )

        session.add(new_menu_item)
        session.commit()

        flash("Successfully added %s." % (new_menu_item.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    elif gAuth.Is_Authenticated():
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

        return render_template('add-menu-item.html', restaurant=restaurant)
    else:
        return redirect(url_for('Show_All_Restaurants'))


@app.route('/restaurant/<int:rest_id>/edit/<int:item_id>/', methods=['GET', 'POST'])
def Edit_Menu_Item(rest_id, item_id):
    if request.method == 'POST' and gAuth.Is_Authenticated():
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
    elif gAuth.Is_Authenticated():
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        item = session.query(MenuItem).filter_by(id=item_id).one()

        return render_template('edit-menu-item.html', restaurant=restaurant, item=item)
    else:
        return redirect(url_for('Show_All_Restaurants'))


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/', methods=['GET', 'POST'])
def Delete_Menu_Item(rest_id, item_id):
    if request.method == 'POST' and gAuth.Is_Authenticated():
        item_to_delete = session.query(MenuItem).filter_by(id=item_id).one()
        if item_to_delete != []:
            session.delete(item_to_delete)
            session.commit()

            flash('Successfully removed %s.' % (item_to_delete.name))

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    elif gAuth.Is_Authenticated():
        restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        item = session.query(MenuItem).filter_by(id=item_id).one()

        return render_template('delete-menu-item.html', restaurant=restaurant, item=item)
    else:
        return redirect(url_for('Show_All_Restaurants'))


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
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
