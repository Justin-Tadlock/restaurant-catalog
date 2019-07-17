#!/usr/bin/env python3
from flask import Flask, render_template, url_for, redirect, jsonify, flash

app = Flask(__name__)


@app.route('/restaurants/')
@app.route('/')
def Show_All_Restaurants():
    return "List all restaurants"


@app.route('/restaurant/<int:rest_id>/')
def Show_Restaurant(rest_id):
    return "View Restaurant %d" % (rest_id)


@app.route('/restaurant/add/')
def Add_Restaurant():
    return "Add Restaurant"


@app.route('/restaurant/<int:rest_id>/edit')
def Edit_Restaurant(rest_id):
    return "Edit Restaurant"


@app.route('/restaurant/<int:rest_id>/delete')
def Delete_Restaurant(rest_id):
    return "Delete Restaurant"


@app.route('/restaurants/all/items/')
def Show_All_Items():
    return "Showing all items"


@app.route('/restaurant/<int:rest_id>/edit/<int:item_id>/')
def Edit_Menu_Item(rest_id, item_id):
    return "Editing restaurant %d, item %d" % (rest_id, item_id)


@app.route('/restaurant/<int:rest_id>/delete/<int:item_id>/')
def Delete_Menu_Item(rest_id, item_id):
    return "Delete %d item from restaurand %d" % (item_id, rest_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
