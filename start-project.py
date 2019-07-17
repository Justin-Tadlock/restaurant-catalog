#!/usr/bin/env python3
from flask import Flask, render_template, url_for, redirect, jsonify, flash

app = Flask(__name__)

#Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}


@app.route('/restaurants/')
@app.route('/')
def Show_All_Restaurants():
    return render_template('show-all-restaurants.html', restaurants=restaurants)


@app.route('/restaurant/<int:rest_id>/')
@app.route('/restaurant/<int:rest_id>/menu')
def Show_Restaurant(rest_id):
    return render_template('show-restaurant.html', restaurant=restaurants[0], menu_items=items)


@app.route('/restaurant/add/')
def Add_Restaurant():
    return render_template('add-restaurant.html')


@app.route('/restaurant/<int:rest_id>/edit')
def Edit_Restaurant(rest_id):
    return render_template('edit-restaurant.html', restaurant=restaurant, menu_items=items)


@app.route('/restaurant/<int:rest_id>/delete')
def Delete_Restaurant(rest_id):
    return render_template('delete-restaurant.html', restaurant=restaurant)


@app.route('/restaurants/all/items/')
def Show_All_Items():
    return render_template('show-all-items.html', menu_items=items)


@app.route('/restaurant/<int:rest_id>/add')
def Add_Menu_Item(rest_id):
    return render_template('add-menu-item.html', restaurant=restaurant)

@app.route('/restaurant/<int:rest_id>/edit/<int:item_id>/')
def Edit_Menu_Item(rest_id, item_id):
    return render_template('edit-menu-item.html', restaurant=restaurant, item=item)


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/')
def Delete_Menu_Item(rest_id, item_id):
    return "Delete %d item from restaurand %d" % (item_id, rest_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
