from App.Services.MeliProducts import MeliProducts
from App.Services.ResponseHandlerService import ResponseHandlerService
from App.Utils.Logger import app_logger


class ProductsController:
    def __init__(self,
                 responseHandlerService: ResponseHandlerService,
                 meliProducts: MeliProducts,
                 ):
        self.responseHandlerService = responseHandlerService
        self.meliProducts = meliProducts

    def notImplemented(self):
        app_logger.warning("Método no implementado llamado")
        return self.responseHandlerService.bad_request("method not implemented")

    def get_category_by_product_name(self, data):
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en get_category_by_product_name")
            return self.responseHandlerService.bad_request("missing data")
        else:
            app_logger.info(f"Buscando categorías para: {data.get('product_name', 'desconocido')}")
            categories = self.meliProducts.get_category_by_product_name(data)

            if "error" in categories:
                app_logger.warning(f"Error al buscar categorías: {categories.get('error')}")
                return self.responseHandlerService.bad_request(categories)

            self.responseHandlerService.setData(categories)
            return self.responseHandlerService.ok("OK")

    def get_category_attributes(self, data):
        if data is None or len(data) == 0 or 'category_id' not in data:
            app_logger.warning("Datos faltantes en get_category_attributes")
            return self.responseHandlerService.bad_request("missing data or category_id")
        else:
            app_logger.info(f"Obteniendo atributos para categoría: {data.get('category_id')}")
            attributes = self.meliProducts.get_category_attributes(data)

            if "error" in attributes:
                app_logger.warning(f"Error al obtener atributos: {attributes.get('error')}")
                return self.responseHandlerService.bad_request(attributes)

            self.responseHandlerService.setData(attributes)
            return self.responseHandlerService.ok("OK")

    def upload_image(self, data):
        if data is None or len(data) == 0 or 'image_data' not in data:
            app_logger.warning("Datos faltantes en upload_image")
            return self.responseHandlerService.bad_request("missing data or image_data")
        else:
            app_logger.info(f"Subiendo imagen para shop_id: {data.get('shop_id')}")
            result = self.meliProducts.upload_image(data)

            if "error" in result:
                app_logger.warning(f"Error al subir imagen: {result.get('error')}")
                return self.responseHandlerService.bad_request(result)

            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def create_product(self, data):
        if data is None or len(data) == 0 or 'product_data' not in data:
            app_logger.warning("Datos faltantes en create_product")
            return self.responseHandlerService.bad_request("missing data or product_data")
        else:
            app_logger.info(f"Creando producto: {data.get('product_data', {}).get('title', 'desconocido')}")
            result = self.meliProducts.create_product(data)

            if "error" in result:
                app_logger.warning(f"Error al crear producto: {result.get('error')}")
                return self.responseHandlerService.bad_request(result)

            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def verify_product(self, data):
        if data is None or len(data) == 0 or 'item_id' not in data:
            app_logger.warning("Datos faltantes en verify_product")
            return self.responseHandlerService.bad_request("missing data or item_id")
        else:
            app_logger.info(f"Verificando producto: {data.get('item_id')}")
            result = self.meliProducts.verify_product(data)

            if "error" in result:
                app_logger.warning(f"Error al verificar producto: {result.get('error')}")
                return self.responseHandlerService.bad_request(result)

            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def update_product(self, data):
        if data is None or len(data) == 0 or 'item_id' not in data or 'update_data' not in data:
            app_logger.warning("Datos faltantes en update_product")
            return self.responseHandlerService.bad_request("missing data, item_id or update_data")
        else:
            app_logger.info(f"Actualizando producto: {data.get('item_id')}")
            result = self.meliProducts.update_product(data)

            if "error" in result:
                app_logger.warning(f"Error al actualizar producto: {result.get('error')}")
                return self.responseHandlerService.bad_request(result)

            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def get_product_rules(self, data):
        from App.Utils.MeliRulesHelper import MeliRulesHelper

        app_logger.info("Obteniendo reglas de producto")

        # Usar el helper para extraer y normalizar las reglas
        rules_helper = MeliRulesHelper()
        rules = rules_helper.get_normalized_rules()

        self.responseHandlerService.setData(rules)
        return self.responseHandlerService.ok("OK")

    # Agregar este método en la clase ProductsController

    def get_category_tree(self, data):
        """
        Controlador para obtener el árbol de categorías de forma recursiva con información de padres.

        Args:
            data (dict): Datos de la solicitud que incluyen:
                - shop_id (str): ID de la tienda
                - site_id (str, opcional): ID del sitio (default: 'MLM')
                - category_id (str, opcional): Categoría inicial
                - max_depth (int, opcional): Profundidad máxima de recursión
                - include_parents (bool, opcional): Si es True, incluirá la ruta completa de padres
                - fetch_pathways (bool, opcional): Si es True, obtendrá rutas adicionales de categorías

        Returns:
            Response: Respuesta HTTP con el árbol de categorías o error
        """
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en get_category_tree")
            return self.responseHandlerService.bad_request("missing data")

        if 'shop_id' not in data:
            app_logger.warning("shop_id es obligatorio para obtener árbol de categorías")
            return self.responseHandlerService.bad_request("shop_id is required")

        app_logger.info(f"Obteniendo árbol de categorías para shop_id: {data.get('shop_id')}")

        # Validar max_depth para prevenir sobrecarga
        if 'max_depth' in data:
            try:
                max_depth = int(data['max_depth'])
                if max_depth > 5:
                    app_logger.warning(f"max_depth ({max_depth}) es demasiado grande, limitando a 5")
                    data['max_depth'] = 5
            except ValueError:
                app_logger.warning(f"max_depth inválido ({data['max_depth']}), usando valor predeterminado")
                data['max_depth'] = 3

        # Manejar parámetros booleanos que pueden venir como strings
        if 'include_parents' in data and isinstance(data['include_parents'], str):
            data['include_parents'] = data['include_parents'].lower() in ('true', '1', 't', 'y', 'yes')

        if 'fetch_pathways' in data and isinstance(data['fetch_pathways'], str):
            data['fetch_pathways'] = data['fetch_pathways'].lower() in ('true', '1', 't', 'y', 'yes')

        # Llamar al servicio para obtener el árbol
        result = self.meliProducts.get_category_tree(data)

        # Verificar errores en la respuesta
        if "error" in result:
            app_logger.warning(f"Error al obtener árbol de categorías: {result.get('error')}")
            return self.responseHandlerService.bad_request(result)

        # Devolver resultado exitoso
        self.responseHandlerService.setData(result)
        return self.responseHandlerService.ok("Árbol de categorías obtenido correctamente")