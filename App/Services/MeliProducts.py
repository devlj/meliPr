import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
from App.Services.MeliUsersService import MeliUsersService


class MeliProducts:
    def __init__(self, meliUsersService: MeliUsersService):
        self.meliUsersService = meliUsersService
        self.base_url = "https://api.mercadolibre.com"
        self.site_id = "MLM"  # México por defecto, podría configurarse dinámicamente

    def get_category_by_product_name(self, data):
        shop_id = data['shop_id']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)
        if len(user) > 0:
            print(data["product_name"])
            print(user)
            return self.__invoke_meliCategories(data["product_name"], user[0])
        else:
            return False

    def __invoke_meliCategories(self, product_name, user):
        """
        Consulta la API de Mercado Libre para obtener la categoría más relevante
        basándose en el nombre del producto.
        """
        base_url = "https://api.mercadolibre.com/sites/MLM/domain_discovery/search"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }
        params = {"q": product_name}

        try:
            response = requests.get(base_url, headers=headers, params=params)
            data = response.json()
            if response.status_code == 401:
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_meliCategories(product_name, tokens)

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

            if not categories:
                return {"error": "No se encontraron categorías relevantes."}

            return {"categories": categories}

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}

    def get_category_attributes(self, data):
        """
        Obtiene los atributos necesarios para una categoría específica.
        """
        shop_id = data['shop_id']
        category_id = data['category_id']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)

        if len(user) == 0:
            return {"error": "Usuario no encontrado"}

        return self.__invoke_category_attributes(category_id, user[0])

    def __invoke_category_attributes(self, category_id, user):
        """
        Consulta la API de Mercado Libre para obtener los atributos de una categoría.
        """
        endpoint = f"/categories/{category_id}/attributes"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

            if response.status_code == 401:
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_category_attributes(category_id, tokens)

            data = response.json()

            # Separamos los atributos requeridos de los opcionales
            required_attributes = []
            optional_attributes = []

            for attr in data:
                if attr.get("tags") and "required" in attr.get("tags"):
                    required_attributes.append(attr)
                else:
                    optional_attributes.append(attr)

            return {
                "required_attributes": required_attributes,
                "optional_attributes": optional_attributes
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}

    def upload_image(self, data):
        """
        Sube una imagen para un producto a Mercado Libre.
        """
        shop_id = data['shop_id']
        image_data = data['image_data']  # Base64 o URL de la imagen
        user = self.meliUsersService.getMeliUserByShopId(shop_id)

        if len(user) == 0:
            return {"error": "Usuario no encontrado"}

        return self.__invoke_upload_image(image_data, user[0])

    def __invoke_upload_image(self, image_data, user):
        """
        Realiza la subida de la imagen a Mercado Libre.
        Acepta datos de imagen en base64 o URL.
        """
        endpoint = "/pictures"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            # Si image_data es una URL
            if image_data.startswith('http'):
                print("es imagen con url")
                payload = {"source": image_data}
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=payload)
                print(response.json())
            # Si es una ruta de archivo local
            elif os.path.isfile(image_data):
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

            if response.status_code == 401:
                print("se supone que hace refresh")
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_upload_image(image_data, tokens)

            data = response.json()
            return {"image": data}

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}

    def create_product(self, data):
        """
        Crea un nuevo producto en Mercado Libre.
        """
        shop_id = data['shop_id']
        product_data = data['product_data']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)

        if len(user) == 0:
            return {"error": "Usuario no encontrado"}

        return self.__invoke_create_product(product_data, user[0])

    def __invoke_create_product(self, product_data, user):
        """
        Realiza la creación del producto en Mercado Libre.
        """
        endpoint = "/items"
        headers = {
            "Authorization": f"Bearer {user['access_token']}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=product_data
            )

            if response.status_code == 401:
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_create_product(product_data, tokens)

            data = response.json()

            # Si la publicación fue exitosa
            if response.status_code in (200, 201):
                return {"product": data}
            else:
                return {
                    "error": "Error al crear el producto",
                    "details": data
                }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}

    def verify_product(self, data):
        """
        Verifica el estado de un producto publicado.
        """
        shop_id = data['shop_id']
        item_id = data['item_id']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)

        if len(user) == 0:
            return {"error": "Usuario no encontrado"}

        return self.__invoke_verify_product(item_id, user[0])

    def __invoke_verify_product(self, item_id, user):
        """
        Consulta la API de Mercado Libre para verificar el estado de un producto.
        """
        endpoint = f"/items/{item_id}"
        headers = {
            "Authorization": f"Bearer {user['access_token']}"
        }

        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

            if response.status_code == 401:
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_verify_product(item_id, tokens)

            data = response.json()

            return {"product": data}

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}

    def update_product(self, data):
        """
        Actualiza un producto existente en Mercado Libre.
        """
        shop_id = data['shop_id']
        item_id = data['item_id']
        update_data = data['update_data']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)

        if len(user) == 0:
            return {"error": "Usuario no encontrado"}

        return self.__invoke_update_product(item_id, update_data, user[0])

    def __invoke_update_product(self, item_id, update_data, user):
        """
        Realiza la actualización del producto en Mercado Libre.
        """
        endpoint = f"/items/{item_id}"
        headers = {
            "Authorization": f"Bearer {user['access_token']}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.put(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=update_data
            )

            if response.status_code == 401:
                tokens = self.meliUsersService.refreshAccessToken(user["user_id"])
                return self.__invoke_update_product(item_id, update_data, tokens)

            data = response.json()

            # Si la actualización fue exitosa
            if response.status_code in (200, 201):
                return {"product": data}
            else:
                return {
                    "error": "Error al actualizar el producto",
                    "details": data
                }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud: {str(e)}"}