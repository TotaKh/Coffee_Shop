import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()


# ROUTES

'''
    GET /drinks
        a public endpoint
        it contain only the drink.short() data representation
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()

    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    }), 200


'''
    GET /drinks-detail
        it require the 'get:drinks-detail' permission
        it contain the drink.long() data representation
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = Drink.query.all()
    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    }), 200


'''
    POST /drinks
        it create a new row in the drinks table
        it require the 'post:drinks' permission
        it contain the drink.long() data representation
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(jwt):

    body = request.get_json()
    try:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        new_drink = Drink(title=new_title, recipe=json.dumps(new_recipe))
        new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": [new_drink.long()]
        }), 200

    except BaseException:
        abort(422)


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it respond with a 404 error if <id> is not found
        it update the corresponding row for <id>
        it require the 'patch:drinks' permission
        it contain the drink.long() data representation
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)

    try:

        drink.title = title
        drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })

    except BaseException:
        abort(422)


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it respond with a 404 error if <id> is not found
        it delete the corresponding row for <id>
        it require the 'delete:drinks' permission
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)

    try:

        drink.delete()

        return jsonify({
            "success": True,
            "delete": drink_id
        })

    except BaseException:
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
    error handler for AuthError
    error handler conform to general task above
'''


@app.errorhandler(AuthError)
def not_authenticated(auth_error):
    return jsonify({
        "success": False,
        "error": auth_error.status_code,
        "message": auth_error.error
    }), 401
