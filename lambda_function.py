from flask import Flask
from aws_lambda_wsgi import response

from App.Containers.Container import Container
from App.Routes.customRoutes import create_custom_routes
from App.Routes.productsRoutes import create_products_routes
from App.Utils.Logger import configure_mongodb, app_logger

app = Flask(__name__)
container = Container()

app.register_blueprint(create_custom_routes(container.custom_controller()))
app.register_blueprint(create_products_routes(container.products_controller()))

#update
def lambda_handler(event, context):
    configure_mongodb(
        app_logger,
        "mongodb://root:qwerty@mongo:27017/",
        "meli_api_logs",
        "logs"
    )
    return response(app, event, context)