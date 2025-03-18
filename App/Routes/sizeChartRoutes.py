from flask import Blueprint, request
from App.Controllers.SizeChartController import SizeChartController
from App.Middleware.ErrorHandlerMiddleware import apply_middleware_to_blueprint


def create_size_chart_routes(size_chart_controller: SizeChartController):
    """
    Crea las rutas para la gestión de guías de tallas.
    """
    size_chart_routes = Blueprint('size_chart_routes', __name__)

    @size_chart_routes.route('/meli/products/size_charts', methods=['GET'])
    def list_size_charts():
        """Obtiene todas las guías de tallas disponibles."""
        if request.method == 'GET':
            # Convertir query params a dict
            query_data = request.args.to_dict()
            # Asegurar que shop_id esté presente
            if 'shop_id' not in query_data:
                return size_chart_controller.response_handler_service.bad_request("shop_id is required")
            return size_chart_controller.list_size_charts(query_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/size_charts/<string:size_chart_id>', methods=['GET'])
    def get_size_chart(size_chart_id):
        """Obtiene una guía de tallas específica por su ID."""
        if request.method == 'GET':
            # Convertir query params a dict y añadir el ID de la ruta
            query_data = request.args.to_dict()
            query_data['size_chart_id'] = size_chart_id
            # Asegurar que shop_id esté presente
            if 'shop_id' not in query_data:
                return size_chart_controller.response_handler_service.bad_request("shop_id is required")
            return size_chart_controller.get_size_chart(query_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/size_charts', methods=['POST'])
    def create_size_chart():
        """Crea una nueva guía de tallas."""
        if request.method == 'POST':
            request_data = request.get_json()
            return size_chart_controller.create_size_chart(request_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/items/<string:item_id>/size_charts/<string:size_chart_id>', methods=['POST'])
    def associate_size_chart(item_id, size_chart_id):
        """Asocia una guía de tallas a un producto."""
        if request.method == 'POST':
            # Convertir query params a dict y añadir los IDs de la ruta
            query_data = request.args.to_dict()
            # Si hay datos en JSON, combinarlos con los query params
            if request.is_json:
                json_data = request.get_json()
                query_data.update(json_data)

            query_data['item_id'] = item_id
            query_data['size_chart_id'] = size_chart_id

            # Asegurar que shop_id esté presente
            if 'shop_id' not in query_data:
                return size_chart_controller.response_handler_service.bad_request("shop_id is required")

            return size_chart_controller.associate_size_chart(query_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/domains/<string:domain_id>/required_attributes', methods=['GET'])
    def get_domain_required_attributes(domain_id):
        """Obtiene los atributos requeridos para guías de tallas en un dominio específico."""
        if request.method == 'GET':
            # Convertir query params a dict y añadir el domain_id
            query_data = request.args.to_dict()
            query_data['domain_id'] = domain_id
            return size_chart_controller.get_domain_required_attributes(query_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/domains/<string:domain_id>/size_charts_template', methods=['POST'])
    def get_size_chart_template(domain_id):
        """Obtiene la ficha técnica específica para guías de tallas."""
        if request.method == 'POST':
            # Obtener datos del body
            request_data = request.get_json()
            # Añadir domain_id a los datos
            request_data['domain_id'] = domain_id
            return size_chart_controller.get_size_chart_template(request_data)
        else:
            return size_chart_controller.not_implemented()

    @size_chart_routes.route('/meli/products/size_charts/simple', methods=['POST'])
    def create_simple_size_chart():
        """Crea una guía de tallas utilizando un formato simplificado."""
        if request.method == 'POST':
            request_data = request.get_json()
            return size_chart_controller.create_simple_size_chart(request_data)
        else:
            return size_chart_controller.not_implemented()

    # Aplicar middleware de manejo de errores
    return apply_middleware_to_blueprint(size_chart_routes)