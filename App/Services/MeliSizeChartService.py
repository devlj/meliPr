import requests
from App.Services.MeliUsersService import MeliUsersService
from App.Utils.Logger import app_logger
from App.Utils.Exceptions import MeliApiError, NotFoundError


class MeliSizeChartService:
    """
    Servicio para gestionar guías de tallas (size charts) en Mercado Libre.
    Basado en la documentación: https://developers.mercadolibre.com.ar/en_us/size-guide
    """

    def __init__(self, meli_users_service: MeliUsersService):
        self.meli_users_service = meli_users_service
        self.base_url = "https://api.mercadolibre.com"

    def _get_user_by_shop_id(self, shop_id):
        """
        Obtiene un usuario de MeLi por su shop_id.
        """
        user = self.meli_users_service.getMeliUserByShopId(shop_id)
        if not user or len(user) == 0:
            app_logger.error(f"Usuario no encontrado para shop_id: {shop_id}")
            raise NotFoundError("Usuario", shop_id)

        app_logger.info(f"Usuario encontrado para shop_id: {shop_id}, user_id: {user[0].get('user_id', 'desconocido')}")
        return user[0]

    def _handle_api_response(self, response, operation_name, user_id=None, retry_func=None, retry_args=None):
        """
        Maneja la respuesta de la API, procesa errores y registra información relevante.
        """
        try:
            data = response.json()
        except ValueError:
            app_logger.error(f"Error al decodificar JSON en respuesta para {operation_name}")
            raise MeliApiError(
                response.status_code,
                "Error al procesar la respuesta del servidor",
                {"error": "JSON inválido"}
            )

        # Log de la respuesta
        app_logger.info(f"Respuesta de API para {operation_name}: Status={response.status_code}")

        # Si el token expiró y tenemos la función de reintento
        if response.status_code == 401 and retry_func and user_id:
            app_logger.info(f"Token expirado para usuario {user_id}, renovando...")
            tokens = self.meli_users_service.refreshAccessToken(user_id)
            if tokens:
                app_logger.info(f"Token renovado exitosamente para usuario {user_id}")
                return retry_func(*retry_args, tokens)
            else:
                app_logger.error(f"No se pudo renovar el token para usuario {user_id}")
                raise MeliApiError(
                    401,
                    "No se pudo renovar el token de acceso",
                    {"error": "token_refresh_failed"}
                )

        # Para errores de la API que devuelven códigos de error
        if response.status_code >= 400:
            error_message = data.get('message', 'Error desconocido')
            error_detail = data.get('error', '')
            app_logger.error(
                f"Error de API {operation_name}: {response.status_code} - {error_message} - {error_detail}")

            raise MeliApiError(
                response.status_code,
                f"Error en operación {operation_name}: {error_message}",
                data
            )

        # Respuesta exitosa
        app_logger.info(f"Operación {operation_name} completada exitosamente")
        return data

    def list_size_charts(self, data):
        """
        Lista las guías de tallas disponibles para un usuario.

        Endpoint: GET /users/{user_id}/size_charts
        """
        operation_name = "list_size_charts"
        try:
            shop_id = data.get('shop_id')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)
            user_id = user.get('user_id')

            # Construir endpoint
            endpoint = f"/users/{user_id}/size_charts"
            params = {
                'limit': limit,
                'offset': offset
            }

            # Llamar a la API
            headers = {"Authorization": f"Bearer {user['access_token']}"}
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user_id,
                self.list_size_charts,
                ({"shop_id": shop_id, "limit": limit, "offset": offset},)
            )

            return {"size_charts": data}

        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def get_size_chart(self, data):
        """
        Obtiene una guía de tallas específica por su ID.

        Endpoint: GET /size_charts/{size_chart_id}
        """
        operation_name = "get_size_chart"
        try:
            shop_id = data.get('shop_id')
            size_chart_id = data.get('size_chart_id')

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Construir endpoint
            endpoint = f"/size_charts/{size_chart_id}"

            # Llamar a la API
            headers = {"Authorization": f"Bearer {user['access_token']}"}
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get('user_id'),
                self.get_size_chart,
                ({"shop_id": shop_id, "size_chart_id": size_chart_id},)
            )

            return {"size_chart": data}

        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def create_size_chart(self, data):
        """
        Crea una nueva guía de tallas.

        Endpoint: POST /catalog/charts
        """
        operation_name = "create_size_chart"
        try:
            shop_id = data.get('shop_id')

            # Extraer datos de la guía de tallas manteniendo la estructura esperada por la API
            chart_data = {
                "names": data.get('names'),
                "domain_id": data.get('domain_id'),
                "site_id": data.get('site_id'),
                "main_attribute": data.get('main_attribute'),
                "attributes": data.get('attributes'),
                "rows": data.get('rows')
            }

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Construir endpoint
            endpoint = "/catalog/charts"

            # Llamar a la API
            headers = {
                "Authorization": f"Bearer {user['access_token']}",
                "Content-Type": "application/json"
            }

            app_logger.info(f"Enviando solicitud para crear guía de tallas: {chart_data}")
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=chart_data)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get('user_id'),
                self.create_size_chart,
                (data,)
            )

            return {"size_chart": data}

        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def associate_size_chart(self, data):
        """
        Asocia una guía de tallas a un producto.

        Endpoint: POST /items/{item_id}/size_charts/{size_chart_id}
        """
        operation_name = "associate_size_chart"
        try:
            shop_id = data.get('shop_id')
            item_id = data.get('item_id')
            size_chart_id = data.get('size_chart_id')

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Construir endpoint
            endpoint = f"/items/{item_id}/size_charts/{size_chart_id}"

            # Llamar a la API
            headers = {
                "Authorization": f"Bearer {user['access_token']}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{self.base_url}{endpoint}", headers=headers)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get('user_id'),
                self.associate_size_chart,
                (data,)
            )

            return {"association": data}

        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}