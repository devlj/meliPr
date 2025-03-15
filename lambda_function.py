from flask import Flask
from aws_lambda_wsgi import response

from App.Containers.Container import Container
from App.Routes.customRoutes import create_custom_routes
from App.Routes.productsRoutes import create_products_routes
from App.Routes.sizeChartRoutes import create_size_chart_routes

app = Flask(__name__)
container = Container()

# Registrar rutas existentes
app.register_blueprint(create_custom_routes(container.custom_controller()))
app.register_blueprint(create_products_routes(container.products_controller()))

# Registrar nuevas rutas para guías de tallas
app.register_blueprint(create_size_chart_routes(container.size_chart_controller()))

def lambda_handler(event, context):
    return response(app, event, context)