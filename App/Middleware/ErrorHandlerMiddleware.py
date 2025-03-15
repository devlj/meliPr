from flask import jsonify, request
from functools import wraps
from marshmallow import ValidationError
from App.Utils.Exceptions import MeliApiError, NotFoundError, AuthenticationError
from App.Utils.Logger import app_logger


def handle_errors(f):
    """
    Decorador para manejar errores en las rutas de Flask.
    Captura excepciones específicas y devuelve respuestas JSON adecuadas.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            app_logger.warning(f"Error de validación: {e.messages} - Path: {request.path}")
            return jsonify({
                "error": "Datos de entrada inválidos",
                "details": e.messages,
                "status": "error"
            }), 400
        except MeliApiError as e:
            app_logger.error(f"Error de API MeLi: {e} - Path: {request.path}")
            return jsonify({
                "error": e.message,
                "details": e.details,
                "status": "error"
            }), e.status_code
        except NotFoundError as e:
            app_logger.warning(f"Recurso no encontrado: {e} - Path: {request.path}")
            return jsonify({
                "error": e.message,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "status": "error"
            }), 404
        except AuthenticationError as e:
            app_logger.warning(f"Error de autenticación: {e} - Path: {request.path}")
            return jsonify({
                "error": e.message,
                "details": e.details,
                "status": "error"
            }), 401
        except Exception as e:
            app_logger.exception(f"Error inesperado: {str(e)} - Path: {request.path}")
            return jsonify({
                "error": "Error interno del servidor " + e,
                "status": "error"
            }), 500

    return decorated_function


def apply_middleware_to_blueprint(blueprint):
    """
    Aplica el middleware de manejo de errores a todas las rutas de un blueprint.

    Args:
        blueprint: Blueprint de Flask al que se aplicará el middleware
    """
    for endpoint, view_func in blueprint.view_functions.items():
        blueprint.view_functions[endpoint] = handle_errors(view_func)

    return blueprint