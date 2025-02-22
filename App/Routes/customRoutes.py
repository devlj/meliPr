from flask import Blueprint, request

from App.Controllers.CustomController import CustomController


def create_custom_routes(custom_controller:CustomController):
    custom_routes_bp = Blueprint('custom_routes', __name__)

    @custom_routes_bp.route('/meli/products/hello', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def customRoutes():
        if request.method == "GET":
            return custom_controller.hello(request.args)

    return custom_routes_bp
