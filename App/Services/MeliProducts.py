import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
import json
from marshmallow import ValidationError

from App.Services.MeliUsersService import MeliUsersService
from App.Models.Schemas.MeliSchemas import (
    CategoryRequestSchema,
    CategoryAttributesRequestSchema,
    ImageUploadRequestSchema,
    ProductCreateRequestSchema,
    ProductVerifyRequestSchema,
    ProductUpdateRequestSchema
)
from App.Utils.Logger import app_logger
from App.Utils.Exceptions import MeliApiError, NotFoundError


class MeliProducts:
    def __init__(self, meliUsersService: MeliUsersService):
        self.meliUsersService = meliUsersService
        self.base_url = "https://api.mercadolibre.com"
        self.site_id = "MLM"  # México por defecto

        # Esquemas de validación
        self.category_schema = CategoryRequestSchema()
        self.category_attributes_schema = CategoryAttributesRequestSchema()
        self.image_upload_schema = ImageUploadRequestSchema()
        self.product_create_schema = ProductCreateRequestSchema()
        self.product_verify_schema = ProductVerifyRequestSchema()
        self.product_update_schema = ProductUpdateRequestSchema()

    def _validate_data(self, schema, data):
        """
        Valida los datos de entrada con el esquema proporcionado.
        Lanza ValidationError si los datos no son válidos.
        """
        try:
            return schema.load(data)
        except ValidationError as err:
            app_logger.error(f"Error de validación: {err.messages}")
            raise ValidationError(err.messages)

    def _get_user_by_shop_id(self, shop_id):
        """
        Obtiene un usuario de MeLi por su shop_id.
        """
        user = self.meliUsersService.getMeliUserByShopId(shop_id)
        if not user or len(user) == 0:
            app_logger.error(f"Usuario no encontrado para shop_id: {shop_id}")
            raise NotFoundError("Usuario", shop_id)

        app_logger.info(f"Usuario encontrado para shop_id: {shop_id}, user_id: {user[0].get('user_id', 'desconocido')}")
        return user[0]

    def _handle_api_response(self, response, operation_name, user_id=None, retry_func=None, retry_args=None):
        """
        Maneja la respuesta de la API, procesa errores y registra información relevante.

        Args:
            response: Respuesta HTTP de requests
            operation_name: Nombre de la operación (para logs)
            user_id: ID del usuario (opcional)
            retry_func: Función a llamar en caso de token expirado (401)
            retry_args: Argumentos para la función de reintento

        Returns:
            Datos de la respuesta procesados

        Raises:
            MeliApiError: En caso de error de la API
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
            tokens = self.meliUsersService.refreshAccessToken(user_id)
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

            # Enriquecemos el mensaje de error según el código
            if response.status_code == 400:
                error_type = "Datos inválidos"
            elif response.status_code == 401:
                error_type = "No autorizado"
            elif response.status_code == 403:
                error_type = "Acceso prohibido"
            elif response.status_code == 404:
                error_type = "Recurso no encontrado"
            elif response.status_code == 422:
                error_type = "Error de validación"
            else:
                error_type = "Error de servidor"

            raise MeliApiError(
                response.status_code,
                f"{error_type}: {error_message}",
                data
            )

        # Respuesta exitosa
        app_logger.info(f"Operación {operation_name} completada exitosamente")
        return data

    def get_category_by_product_name(self, data):
        """
        Obtiene las categorías basadas en el nombre del producto.
        """
        operation_name = "get_category_by_product_name"
        try:
            # Validar datos
            app_logger.info(f"Iniciando {operation_name} para producto: {data.get('product_name', 'desconocido')}")
            validated_data = self._validate_data(self.category_schema, data)

            shop_id = validated_data['shop_id']
            product_name = validated_data['product_name']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_meliCategories(product_name, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_meliCategories(self, product_name, user):
        """
        Consulta la API de Mercado Libre para obtener la categoría más relevante
        basándose en el nombre del producto.
        """
        operation_name = "invoke_meliCategories"
        base_url = "https://api.mercadolibre.com/sites/MLM/domain_discovery/search"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }
        params = {"q": product_name}

        try:
            app_logger.info(f"Consultando API para categorías de: {product_name}")
            response = requests.get(base_url, headers=headers, params=params)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_meliCategories,
                (product_name,)
            )

            categories = []
            if data and isinstance(data, list):
                for category in data:
                    categories.append({
                        "category_id": category.get("category_id"),
                        "category_name": category.get("category_name"),
                        "domain_id": category.get("domain_id"),
                        "domain_name": category.get("domain_name"),
                        "attributes": category.get("attributes", [])
                    })
                    app_logger.info(
                        f"Categoría encontrada: {category.get('category_name')} ({category.get('category_id')})")

            if not categories:
                app_logger.warning(f"No se encontraron categorías para: {product_name}")
                return {"error": "No se encontraron categorías relevantes."}

            return {"categories": categories}

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )

    def get_category_attributes(self, data):
        """
        Obtiene los atributos necesarios para una categoría específica.
        """
        operation_name = "get_category_attributes"
        try:
            # Validar datos
            app_logger.info(f"Iniciando {operation_name} para categoría: {data.get('category_id', 'desconocido')}")
            validated_data = self._validate_data(self.category_attributes_schema, data)

            shop_id = validated_data['shop_id']
            category_id = validated_data['category_id']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_category_attributes(category_id, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_category_attributes(self, category_id, user):
        """
        Consulta la API de Mercado Libre para obtener los atributos de una categoría.
        """
        operation_name = "invoke_category_attributes"
        endpoint = f"/categories/{category_id}/attributes"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            app_logger.info(f"Consultando API para atributos de categoría: {category_id}")
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_category_attributes,
                (category_id,)
            )

            # Separamos los atributos requeridos de los opcionales
            required_attributes = []
            optional_attributes = []

            for attr in data:
                if attr.get("tags") and "required" in attr.get("tags"):
                    required_attributes.append(attr)
                    app_logger.info(f"Atributo requerido encontrado: {attr.get('id')}")
                else:
                    optional_attributes.append(attr)

            app_logger.info(
                f"Total atributos requeridos: {len(required_attributes)}, opcionales: {len(optional_attributes)}")

            return {
                "required_attributes": required_attributes,
                "optional_attributes": optional_attributes
            }

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )

    def upload_image(self, data):
        """
        Sube una imagen para un producto a Mercado Libre.
        """
        operation_name = "upload_image"
        try:
            # Validar datos
            app_logger.info(f"Iniciando {operation_name}")
            validated_data = self._validate_data(self.image_upload_schema, data)

            shop_id = validated_data['shop_id']
            image_data = validated_data['image_data']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_upload_image(image_data, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_upload_image(self, image_data, user):
        """
        Realiza la subida de la imagen a Mercado Libre.
        Acepta datos de imagen en base64 o URL.
        """
        operation_name = "invoke_upload_image"
        endpoint = "/pictures"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            app_logger.info(f"Subiendo imagen a API")

            # Determinar el tipo de datos de la imagen
            if image_data.startswith('http'):
                app_logger.info("Subiendo imagen desde URL")
                payload = {"source": image_data}
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=payload)
            # Si es una ruta de archivo local
            elif os.path.isfile(image_data):
                app_logger.info(f"Subiendo imagen desde archivo local: {image_data}")
                with open(image_data, 'rb') as f:
                    multipart_data = MultipartEncoder(
                        fields={'file': ('filename', f, 'image/jpeg')}
                    )
                    headers['Content-Type'] = multipart_data.content_type
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        data=multipart_data
                    )
            # Asumimos que es base64
            else:
                app_logger.info("Subiendo imagen en formato base64")
                # Procesar base64
                multipart_data = MultipartEncoder(
                    fields={'file': ('filename', image_data, 'image/jpeg')}
                )
                headers['Content-Type'] = multipart_data.content_type
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    data=multipart_data
                )

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_upload_image,
                (image_data,)
            )

            app_logger.info(f"Imagen subida exitosamente: {data.get('id', 'desconocido')}")
            return {"image": data}

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )

    def create_product(self, data):
        """
        Crea un nuevo producto en Mercado Libre.
        """
        operation_name = "create_product"
        try:
            # Validar datos
            app_logger.info(
                f"Iniciando {operation_name} para producto: {data.get('product_data', {}).get('title', 'desconocido')}")
            validated_data = self._validate_data(self.product_create_schema, data)

            shop_id = validated_data['shop_id']
            product_data = validated_data['product_data']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_create_product(product_data, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_create_product(self, product_data, user):
        """
        Realiza la creación del producto en Mercado Libre.
        """
        operation_name = "invoke_create_product"
        endpoint = "/items"
        headers = {
            "Authorization": f"Bearer {user['access_token']}",
            "Content-Type": "application/json"
        }

        try:
            app_logger.info(f"Creando producto en API: {product_data.get('title', 'desconocido')}")
            app_logger.debug(f"Datos completos del producto: {json.dumps(product_data)}")

            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=product_data
            )

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_create_product,
                (product_data,)
            )

            app_logger.info(f"Producto creado exitosamente: {data.get('id', 'desconocido')}")
            return {"product": data}

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error interno del servidor: {str(e)}",
                {"error_type": "server_error"}
            )

    def verify_product(self, data):
        """
        Verifica el estado de un producto publicado.
        """
        operation_name = "verify_product"
        try:
            # Validar datos
            app_logger.info(f"Iniciando {operation_name} para item_id: {data.get('item_id', 'desconocido')}")
            validated_data = self._validate_data(self.product_verify_schema, data)

            shop_id = validated_data['shop_id']
            item_id = validated_data['item_id']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_verify_product(item_id, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_verify_product(self, item_id, user):
        """
        Consulta la API de Mercado Libre para verificar el estado de un producto.
        """
        operation_name = "invoke_verify_product"
        endpoint = f"/items/{item_id}"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            app_logger.info(f"Verificando producto en API: {item_id}")

            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_verify_product,
                (item_id,)
            )

            app_logger.info(f"Producto verificado: {item_id} - Estado: {data.get('status', 'desconocido')}")
            return {"product": data}

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )

    def update_product(self, data):
        """
        Actualiza un producto existente en Mercado Libre.
        """
        operation_name = "update_product"
        try:
            # Validar datos
            app_logger.info(f"Iniciando {operation_name} para item_id: {data.get('item_id', 'desconocido')}")
            validated_data = self._validate_data(self.product_update_schema, data)

            shop_id = validated_data['shop_id']
            item_id = validated_data['item_id']
            update_data = validated_data['update_data']

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Llamar a la API
            return self.__invoke_update_product(item_id, update_data, user)

        except ValidationError as err:
            return {"error": "Error de validación", "details": err.messages}
        except MeliApiError as err:
            return {"error": err.message, "details": err.details, "status_code": err.status_code}
        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def __invoke_update_product(self, item_id, update_data, user):
        """
        Realiza la actualización del producto en Mercado Libre.
        """
        operation_name = "invoke_update_product"
        endpoint = f"/items/{item_id}"
        headers = {
            "Authorization": f"Bearer {user['access_token']}",
            "Content-Type": "application/json"
        }

        try:
            app_logger.info(f"Actualizando producto en API: {item_id}")
            app_logger.debug(f"Datos de actualización: {json.dumps(update_data)}")

            response = requests.put(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=update_data
            )

            # Procesar respuesta
            data = self._handle_api_response(
                response,
                operation_name,
                user.get("user_id"),
                self.__invoke_update_product,
                (item_id, update_data)
            )

            app_logger.info(f"Producto actualizado exitosamente: {item_id}")
            return {"product": data}

        except MeliApiError as err:
            raise err
        except requests.exceptions.RequestException as e:
            app_logger.exception(f"Error de red en {operation_name}: {str(e)}")
            raise MeliApiError(
                500,
                f"Error en la solicitud: {str(e)}",
                {"error_type": "network_error"}
            )