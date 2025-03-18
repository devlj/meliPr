from flask import Blueprint, request

from App.Controllers.ProductsController import ProductsController
from App.Middleware.ErrorHandlerMiddleware import apply_middleware_to_blueprint


def create_products_routes(productsController: ProductsController):
    products_routes = Blueprint('products_routes', __name__)

    @products_routes.route('/meli/products/categories', methods=['POST'])
    def get_products():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.get_category_by_product_name(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/categories/attributes', methods=['POST'])
    def get_category_attributes():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.get_category_attributes(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/image', methods=['POST'])
    def upload_image():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.upload_image(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/create', methods=['POST'])
    def create_product():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.create_product(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/verify', methods=['POST'])
    def verify_product():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.verify_product(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/update/product', methods=['POST'])
    def update_product():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.update_product(requestData)
        else:
            return productsController.notImplemented()
    @products_routes.route('/meli/products/update/price', methods=['POST'])
    def update_price_product():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.update_product(requestData)
        else:
            return productsController.notImplemented()

    @products_routes.route('/meli/products/update/stock', methods=['POST'])
    def update_stock_product():
        if request.method == 'POST':
            requestData = request.get_json()
            return productsController.update_product(requestData)
        else:
            return productsController.notImplemented()


    @products_routes.route('/meli/products/rules', methods=['GET'])
    def product_rules():
        if request.method == 'GET':
            return productsController.get_product_rules(request.args.to_dict())
        else:
            return productsController.notImplemented()

    # Aplicar middleware de manejo de errores a todas las rutas
    return apply_middleware_to_blueprint(products_routes)