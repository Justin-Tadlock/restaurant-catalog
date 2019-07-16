#!/usr/bin/env python3
from flask import Flask, render_template, url_for, redirect, jsonify, flash

app = Flask(__name__)

@app.route('/restaurants')
@app.route('/')
def Show_All_Restaurants():
  return "List all restaurants"

if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=5000)
