from flask import Blueprint, request


def create_products_routes():
    products_routes = Blueprint('products_routes', __name__)
    @products_routes.route('/meli/products/category', methods=['GET'])
    def get_products():
        if request.method == 'GET':
            return {"category":True}
    return products_routes