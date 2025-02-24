from flask import Blueprint, request

from App.Controllers.ProductsController import ProductsController


def create_products_routes(productsController:ProductsController):
    products_routes = Blueprint('products_routes', __name__)
    @products_routes.route('/meli/products/category', methods=['POST'])
    def get_products():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.get_category_by_product_name(requestData)
        else:
            return productsController.notImplemented()
    return products_routes