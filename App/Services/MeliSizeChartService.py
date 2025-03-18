import json

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

    def get_domain_required_attributes(self, domain_id, site_id="MLM"):
        """
        Obtiene los atributos marcados como grid_template_required para un dominio específico.
        Estos atributos son necesarios para consultar la ficha técnica de guías de tallas.

        Args:
            domain_id (str): ID del dominio (ej: "SNEAKERS", "CLOTHING")
            site_id (str): ID del sitio (ej: "MLM" para México)

        Returns:
            dict: Atributos requeridos para guías de tallas
        """
        operation_name = "get_domain_required_attributes"
        try:
            # Endpoint para obtener ficha técnica del dominio
            endpoint = f"/domains/MLM-{domain_id}/technical_specs"

            app_logger.info(f"Consultando ficha técnica para dominio: {domain_id}")
            response = requests.get(f"{self.base_url}{endpoint}")

            if response.status_code != 200:
                app_logger.error(f"Error al obtener ficha técnica: {response.status_code}")
                return {"error": "Error al obtener ficha técnica", "status_code": response.status_code}

            data = response.json()

            # Buscar atributos con tag grid_template_required
            required_attributes = []

            # Navegar por la estructura de la ficha técnica
            if "input" in data and "groups" in data["input"]:
                for group in data["input"]["groups"]:
                    if "components" in group:
                        for component in group["components"]:
                            if "attributes" in component:
                                for attribute in component["attributes"]:
                                    # Verificar si tiene el tag grid_template_required
                                    if "tags" in attribute and "grid_template_required" in attribute["tags"]:
                                        required_attributes.append({
                                            "id": attribute.get("id"),
                                            "name": attribute.get("name"),
                                            "value_type": attribute.get("value_type"),
                                            "required": True,
                                            "values": attribute.get("values", [])
                                        })

            return {
                "domain_id": domain_id,
                "site_id": site_id,
                "required_attributes": required_attributes,
                "total_required_attributes": len(required_attributes)
            }

        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def get_size_chart_template(self, data):
        """
        Obtiene la ficha técnica específica para guías de tallas de un dominio.

        Args:
            data (dict): Datos de la solicitud que incluyen:
                - shop_id (str): ID de la tienda
                - domain_id (str): ID del dominio
                - site_id (str, opcional): ID del sitio
                - attributes (list): Lista de atributos requeridos con sus valores

        Returns:
            dict: Ficha técnica simplificada para guías de tallas
        """
        operation_name = "get_size_chart_template"
        try:
            # Extraer datos
            shop_id = data.get('shop_id')
            domain_id = data.get('domain_id')
            site_id = data.get('site_id', 'MLM')
            attributes = data.get('attributes', [])

            # Validar datos obligatorios
            if not shop_id or not domain_id or not attributes:
                app_logger.warning("Datos incompletos para obtener ficha técnica de guía de tallas")
                return {"error": "Se requiere shop_id, domain_id y attributes"}

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Endpoint para obtener ficha técnica específica para guías de tallas
            endpoint = f"/domains/MLM-{domain_id}/technical_specs?section=grids"

            # Preparar payload con formato esperado por Mercado Libre
            payload = {
                "attributes": []
            }

            # Formatear atributos según el formato esperado por MeLi
            for attr in attributes:
                attr_id = attr.get('id')
                value_id = attr.get('value_id')
                value_name = attr.get('value_name')

                formatted_attr = {
                    "id": attr_id,
                    "name": attr_id,  # Usar ID como nombre por defecto
                    "value_id": value_id,
                    "value_name": value_name,
                    "value_struct": None,
                    "values": [
                        {
                            "id": value_id,
                            "name": value_name,
                            "struct": None
                        }
                    ],
                    "attribute_group_id": "OTHERS",
                    "attribute_group_name": "Otros"
                }

                payload["attributes"].append(formatted_attr)

            app_logger.info(f"Consultando ficha técnica para guías de tallas en dominio: {domain_id}")

            headers = {
                "Authorization": f"Bearer {user['access_token']}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=payload
            )

            # Procesar respuesta
            if response.status_code != 200:
                app_logger.error(f"Error al obtener ficha técnica: {response.status_code}")
                return {"error": "Error al obtener ficha técnica", "status_code": response.status_code}

            original_data = response.json()

            # Buscar el componente GRID que contiene la estructura de la guía
            grid_component = None
            if "input" in original_data and "groups" in original_data["input"]:
                for group in original_data["input"]["groups"]:
                    if "components" in group:
                        for component in group["components"]:
                            if component.get("component") == "GRID":
                                grid_component = component
                                break

            if not grid_component or "components" not in grid_component:
                return {"error": "No se encontró la estructura para guía de tallas"}

            # Estructura simplificada
            simplified_template = {
                "domain_id": domain_id,
                "site_id": site_id,
                "required_fields": [],
                "optional_fields": [],
                "measurement_types": {
                    "body_measurements": [],  # Medidas corporales
                    "clothing_measurements": []  # Medidas de prenda
                },
                "main_attribute_candidates": []  # Candidatos a atributo principal
            }

            # Extraer campos requeridos y opcionales
            for sub_component in grid_component.get("components", []):
                if "attributes" in sub_component:
                    for attribute in sub_component["attributes"]:
                        # Ignorar atributos ocultos o de solo lectura
                        if "hidden" in attribute.get("tags", []) or "read_only" in attribute.get("tags", []):
                            continue

                        # Extraer información básica del atributo
                        attr_info = {
                            "id": attribute.get("id"),
                            "name": attribute.get("name"),
                            "type": attribute.get("value_type"),
                            "default_unit": attribute.get("default_unit_id", ""),
                            "units": [unit.get("id") for unit in attribute.get("units", [])]
                        }

                        # Añadir valores predefinidos si existen
                        if "values" in attribute and attribute["values"]:
                            attr_info["values"] = [
                                {"id": val.get("id"), "name": val.get("name")}
                                for val in attribute["values"]
                            ]

                        # Determinar si es requerido
                        is_required = "required" in attribute.get("tags", [])

                        # Determinar si es medida corporal o de prenda
                        is_body_measure = "BODY_MEASURE" in attribute.get("tags", [])
                        is_clothing_measure = "CLOTHING_MEASURE" in attribute.get("tags", [])

                        # Determinar si es candidato a atributo principal
                        is_main_candidate = "main_attribute_candidate" in attribute.get("tags", [])

                        # Añadir a la lista correspondiente
                        if is_required:
                            simplified_template["required_fields"].append(attr_info)
                        else:
                            simplified_template["optional_fields"].append(attr_info)

                        # Añadir a medidas si corresponde
                        if is_body_measure:
                            simplified_template["measurement_types"]["body_measurements"].append(attr_info)
                        elif is_clothing_measure:
                            simplified_template["measurement_types"]["clothing_measurements"].append(attr_info)

                        # Añadir a candidatos de atributo principal si corresponde
                        if is_main_candidate:
                            simplified_template["main_attribute_candidates"].append({
                                "id": attribute.get("id"),
                                "name": attribute.get("name")
                            })

            # Identificar el atributo principal (talla)
            size_attribute = None
            for component in grid_component.get("components", []):
                if "attributes" in component:
                    for attribute in component["attributes"]:
                        if attribute.get("id") == "SIZE":
                            size_attribute = {
                                "id": attribute.get("id"),
                                "name": attribute.get("name"),
                                "type": attribute.get("value_type")
                            }
                            break

            if size_attribute:
                simplified_template["size_attribute"] = size_attribute

                # Si no hay candidatos a atributo principal, añadir SIZE
                if not simplified_template["main_attribute_candidates"]:
                    simplified_template["main_attribute_candidates"].append({
                        "id": "SIZE",
                        "name": "Talla de la etiqueta"
                    })

            # Si todavía no hay candidatos a atributo principal, buscar en campos requeridos
            if not simplified_template["main_attribute_candidates"]:
                for field in simplified_template["required_fields"]:
                    if field["id"] not in ["GENDER", "BRAND"]:
                        simplified_template["main_attribute_candidates"].append({
                            "id": field["id"],
                            "name": field["name"]
                        })
                        break

            # Añadir información para crear una guía de tallas
            example_measurements = {}
            for field in simplified_template["required_fields"]:
                if field["id"] not in ["GENDER", "BRAND", "SIZE"] and field["type"] == "number_unit":
                    example_measurements[field["id"]] = {
                        "value": "valor_ejemplo",
                        "unit": field.get("default_unit", "cm")
                    }

            # Determinar el main_attribute_id para el ejemplo
            suggested_main_attribute = None
            if simplified_template["main_attribute_candidates"]:
                suggested_main_attribute = simplified_template["main_attribute_candidates"][0]["id"]
            elif "size_attribute" in simplified_template:
                suggested_main_attribute = simplified_template["size_attribute"]["id"]
            else:
                # Buscar cualquier atributo que pueda servir como principal
                for field in simplified_template["required_fields"]:
                    if field["id"] not in ["GENDER", "BRAND"]:
                        suggested_main_attribute = field["id"]
                        break

            simplified_template["example_format"] = {
                "shop_id": "ID_DE_LA_TIENDA",
                "domain_id": domain_id,
                "site_id": site_id,
                "chart_name": "Nombre de la guía de tallas",
                "brand": "Marca",
                "gender": attributes[0].get("value_name") if attributes and attributes[0].get(
                    "id") == "GENDER" else "Valor de género",
                "main_attribute_id": suggested_main_attribute,  # Atributo principal sugerido
                "rows": [
                    {
                        "size": "S",
                        "measurements": example_measurements
                    },
                    {
                        "size": "M",
                        "measurements": example_measurements
                    }
                ]
            }

            # Añadir explicación sobre el atributo principal
            simplified_template["important_notes"] = [
                "Se requiere especificar un main_attribute_id al crear la guía de tallas.",
                "Este atributo se utilizará como referencia principal en la tabla.",
                "Debe ser uno de los candidatos listados en main_attribute_candidates."
                "El main_attribute_id se transformará internamente al formato esperado por Mercado Libre (main_attribute.attributes[].id)"
            ]

            return simplified_template

        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": "Error interno del servidor", "details": str(e)}

    def create_simple_size_chart(self, data):
        """
        Crea una guía de tallas utilizando un formato simplificado y adaptándose dinámicamente
        a los requerimientos de cada dominio.

        Args:
            data (dict): Datos en formato simplificado

        Returns:
            dict: Resultado de la creación de la guía de tallas incluyendo detalles completos
        """
        operation_name = "create_simple_size_chart"
        try:
            # Extraer datos básicos
            shop_id = data.get('shop_id')
            domain_id = data.get('domain_id')
            site_id = data.get('site_id', 'MLM')
            chart_name = data.get('chart_name')
            brand = data.get('brand')
            gender = data.get('gender')
            rows = data.get('rows', [])
            main_attribute_id = data.get('main_attribute_id')

            # Validar datos obligatorios
            if not shop_id or not domain_id or not chart_name or not brand or not gender or not rows:
                app_logger.warning("Datos incompletos para crear guía de tallas")
                return {"error": "Se requiere shop_id, domain_id, chart_name, brand, gender y rows"}

            # Verificar que se haya especificado un main_attribute_id
            if not main_attribute_id:
                app_logger.warning("Falta main_attribute_id, es requerido")
                return {"error": "Se requiere main_attribute_id para crear guías de tallas"}

            # Obtener usuario
            user = self._get_user_by_shop_id(shop_id)

            # Construir formato requerido por MeLi
            meli_format = {
                "names": {
                    site_id: chart_name
                },
                "domain_id": domain_id,
                "site_id": site_id,
                "type": "SPECIFIC",
                "main_attribute": {
                    "attributes": [
                        {
                            "site_id": site_id,
                            "id": main_attribute_id
                        }
                    ]
                },
                "attributes": [
                    {
                        "id": "GENDER",
                        "values": [
                            {
                                "name": gender
                            }
                        ]
                    },
                    {
                        "id": "BRAND",
                        "values": [
                            {
                                "name": brand
                            }
                        ]
                    }
                ],
                "rows": []
            }

            # Procesar filas - usando solo las medidas proporcionadas por el cliente
            for row in rows:
                meli_row = {
                    "attributes": []
                }

                measurements = row.get('measurements', {})
                for measure_id, measure_data in measurements.items():
                    # Verificar que tiene la estructura correcta
                    if not isinstance(measure_data, dict) or 'value' not in measure_data:
                        continue

                    # Preparar valor con o sin unidad según se proporcione
                    if 'unit' in measure_data and measure_data['unit']:
                        # Para valores con unidad (number_unit)
                        attr_value = {
                            "id": measure_id,
                            "values": [
                                {
                                    "name": f"{measure_data['value']} {measure_data['unit']}"
                                }
                            ]
                        }
                    else:
                        # Para valores sin unidad (string)
                        attr_value = {
                            "id": measure_id,
                            "values": [
                                {
                                    "name": str(measure_data['value'])
                                }
                            ]
                        }

                    meli_row["attributes"].append(attr_value)

                # Solo añadir la fila si tiene atributos
                if meli_row["attributes"]:
                    meli_format["rows"].append(meli_row)

            # Llamar a la API de MeLi para crear la guía de tallas
            endpoint = "/catalog/charts"

            headers = {
                "Authorization": f"Bearer {user['access_token']}",
                "Content-Type": "application/json"
            }

            app_logger.info(f"Creando guía de tallas para dominio: {domain_id}")
            app_logger.debug(f"Payload para crear guía de tallas: {json.dumps(meli_format)}")

            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=meli_format
            )

            # Procesar respuesta
            if response.status_code != 201 and response.status_code != 200:
                app_logger.error(f"Error al crear guía de tallas: {response.status_code}")
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Error desconocido')
                    app_logger.error(f"Detalle del error: {error_message}")
                    return {"error": f"Error al crear guía de tallas: {error_message}", "details": error_data}
                except:
                    return {"error": f"Error al crear guía de tallas: {response.status_code}",
                            "response_text": response.text}

            result = response.json()

            # Obtener detalles completos de la guía de tallas creada
            chart_id = result.get("id")
            chart_details = self.get_size_chart_details(user, chart_id)

            return {
                "chart_id": chart_id,
                "name": chart_name,
                "domain_id": domain_id,
                "site_id": site_id,
                "brand": brand,
                "gender": gender,
                "main_attribute_id": main_attribute_id,
                "message": "Guía de tallas creada exitosamente",
                "details": chart_details  # Incluir detalles completos de la guía
            }

        except NotFoundError as err:
            return {"error": err.message, "resource_type": err.resource_type, "resource_id": err.resource_id}
        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": f"Error interno del servidor: {str(e)}", "details": str(e)}

    def get_size_chart_details(self, user, chart_id):
        """
        Obtiene los detalles completos de una guía de tallas, incluyendo IDs de filas.

        Args:
            user (dict): Información del usuario con token de acceso
            chart_id (str): ID de la guía de tallas

        Returns:
            dict: Detalles completos de la guía de tallas
        """
        operation_name = "get_size_chart_details"
        try:
            endpoint = f"/catalog/charts/{chart_id}"

            headers = {
                "Authorization": f"Bearer {user['access_token']}"
            }

            app_logger.info(f"Obteniendo detalles de guía de tallas: {chart_id}")

            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )

            if response.status_code != 200:
                app_logger.error(f"Error al obtener detalles de guía: {response.status_code}")
                return {"error": "No se pudieron obtener los detalles de la guía"}

            chart_data = response.json()

            # Extraer información relevante
            simplified_details = {
                "id": chart_data.get("id"),
                "names": chart_data.get("names", {}),
                "domain_id": chart_data.get("domain_id"),
                "type": chart_data.get("type"),
                "main_attribute": chart_data.get("main_attribute"),
                "rows": []
            }

            # Procesar filas para incluir sus IDs y detalles
            for row in chart_data.get("rows", []):
                row_details = {
                    "id": row.get("id"),
                    "attributes": {}
                }

                # Extraer valores de atributos en formato simplificado
                for attr in row.get("attributes", []):
                    attr_id = attr.get("id")
                    values = attr.get("values", [])
                    if values:
                        # Si hay un solo valor, guardar directamente
                        if len(values) == 1:
                            value = values[0].get("name", "")
                            row_details["attributes"][attr_id] = value
                        # Si hay múltiples valores, guardar como lista
                        else:
                            row_details["attributes"][attr_id] = [val.get("name", "") for val in values]

                simplified_details["rows"].append(row_details)

            return simplified_details

        except Exception as e:
            app_logger.exception(f"Error inesperado en {operation_name}: {str(e)}")
            return {"error": f"Error al obtener detalles: {str(e)}"}