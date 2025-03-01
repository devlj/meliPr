import requests

from App.Services.MeliUsersService import MeliUsersService


class MeliProducts:
    def __init__(self,meliUsersService:MeliUsersService):
        self.meliUsersService = meliUsersService

    def get_category_by_product_name(self,data):
        shop_id = data['shop_id']
        user = self.meliUsersService.getMeliUserByShopId(shop_id)
        if len(user) > 0:
            print(data["product_name"])
            print(user)
            return self.__invoke_meliCategories(data["product_name"],user[0])
        else:
            return False
    def __invoke_meliCategories(self,product_name,user):
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
                return self.__invoke_meliCategories(product_name,tokens)

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
