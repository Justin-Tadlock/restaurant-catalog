#!/usr/bin/env python3
from flask import Flask, render_template, url_for, redirect, jsonify, flash, request
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2

app = Flask(__name__)

# Adding db functionality for CRUD operations
engine = create_engine('sqlite:///restaurantmenu.db?check_same_thread=False')
DBsession = sessionmaker(bind=engine)
session = DBsession()

''' #Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'} '''


@app.route('/restaurants/')
@app.route('/')
def Show_All_Restaurants():
    restaurants = session.query(Restaurant).all()
    
    return render_template('show-all-restaurants.html', restaurants=restaurants)


@app.route('/restaurant/<int:rest_id>/')
@app.route('/restaurant/<int:rest_id>/menu')
def Show_Restaurant(rest_id):
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=rest_id)

    return render_template('show-restaurant.html', restaurant=restaurant, menu_items=items)


@app.route('/restaurant/add/', methods=['GET', 'POST'])
def Add_Restaurant():
    if request.method == 'POST':
        new_restaurant = Restaurant(name = request.form['rest_name'])

        session.add(new_restaurant)
        session.commit()

        return redirect(url_for('Show_All_Restaurants'))

    return render_template('add-restaurant.html')


@app.route('/restaurant/<int:rest_id>/edit', methods=['GET', 'POST'])
def Edit_Restaurant(rest_id):
    if request.method == 'POST':
        updated_restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
        updated_restaurant.name = request.form['rest_name']

        session.add(updated_restaurant)
        session.commit()

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))
    
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=rest_id).all()

    return render_template('edit-restaurant.html', restaurant=restaurant, menu_items=items)


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
    
    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()

    return render_template('delete-restaurant.html', restaurant=restaurant)


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

        flash("Successfully added the %s menu item." % (new_menu_item.name))

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

        flash('Updated item %s successfully' % (updated_item.name)) 

        return redirect(url_for('Edit_Restaurant', rest_id=rest_id))

    restaurant = session.query(Restaurant).filter_by(id=rest_id).one()
    item = session.query(MenuItem).filter_by(id=item_id).one()

    return render_template('edit-menu-item.html', restaurant=restaurant, item=item)


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/')
def Delete_Menu_Item(rest_id, item_id):
    return render_template('delete-menu-item.html', restaurant=restaurant, item=item)


if __name__ == '__main__':
    app.secret_key = 'my_super_secret_but_not_really_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
