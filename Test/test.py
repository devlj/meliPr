import requests
import json

# URL base de tu API
base_url = "http://127.0.0.1:3008"

# Datos comunes
shop_id = "126526290"  # Usa un ID de tienda válido

# 1. Buscar categoría
print("1. Buscando categoría...")
r = requests.post(
    f"{base_url}/meli/products/category",
    json={"shop_id": shop_id, "product_name": "Smartphone Samsung Galaxy"}
)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
category_data = r.json()
category_id = category_data.get("data", {}).get("categories", [])[0].get("category_id")

# 2. Obtener atributos de la categoría
if category_id:
    print("\n2. Obteniendo atributos de categoría...")
    r = requests.post(
        f"{base_url}/meli/products/category/attributes",
        json={"shop_id": shop_id, "category_id": category_id}
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

# 3. Subir una imagen
print("\n3. Subiendo imagen...")
r = requests.post(
    f"{base_url}/meli/products/image",
    json={"shop_id": shop_id, "image_data": "https://ejemplo.com/imagen.jpg"}
)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
image_data = r.json()
image_id = image_data.get("data", {}).get("image", {}).get("id")

# 4. Crear un producto (solo si tenemos categoría e imagen)
if category_id and image_id:
    print("\n4. Creando producto...")
    product_data = {
        "title": "Smartphone Samsung Galaxy S21 128GB",
        "category_id": category_id,
        "price": 12999.99,
        "currency_id": "MXN",
        "available_quantity": 10,
        "buying_mode": "buy_it_now",
        "condition": "new",
        "listing_type_id": "gold_special",
        "description": {
            "plain_text": "Smartphone Samsung Galaxy S21 con 128GB de almacenamiento. Excelente rendimiento y batería."
        },
        "pictures": [
            {"id": image_id}
        ],
        "attributes": [
            {
                "id": "BRAND",
                "value_name": "Samsung"
            },
            {
                "id": "MODEL",
                "value_name": "Galaxy S21"
            }
        ]
    }

    r = requests.post(
        f"{base_url}/meli/products",
        json={"shop_id": shop_id, "product_data": product_data}
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    product_data = r.json()
    item_id = product_data.get("data", {}).get("product", {}).get("id")

    # 5. Verificar el producto
    if item_id:
        print("\n5. Verificando producto...")
        r = requests.post(
            f"{base_url}/meli/products/verify",
            json={"shop_id": shop_id, "item_id": item_id}
        )
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))

        # 6. Actualizar el producto
        print("\n6. Actualizando producto...")
        r = requests.post(
            f"{base_url}/meli/products/update",
            json={
                "shop_id": shop_id,
                "item_id": item_id,
                "update_data": {
                    "price": 11999.99,
                    "available_quantity": 8
                }
            }
        )
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))