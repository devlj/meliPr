from marshmallow import Schema, fields, validates, validate, ValidationError
import re


class CategoryRequestSchema(Schema):
    """Esquema para validar peticiones de búsqueda de categorías."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    product_name = fields.Str(required=True, validate=validate.Length(min=3, max=60),
                              description="Nombre del producto para buscar categorías")


class CategoryAttributesRequestSchema(Schema):
    """Esquema para validar peticiones de atributos de categoría."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    category_id = fields.Str(required=True, description="ID de la categoría en Mercado Libre")

    @validates('category_id')
    def validate_category_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El category_id debe tener el formato correcto (ej: MLM1055)")


class ProductRulesRequestSchema(Schema):
    """Esquema para validar peticiones de reglas de productos."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    category_id = fields.Str(required=False, description="ID de categoría (opcional)")


class ImageUploadRequestSchema(Schema):
    """Esquema para validar peticiones de subida de imágenes."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    image_data = fields.Str(required=True, description="Datos de la imagen (URL o base64)")


# Esquemas base simplificados
class DescriptionSchema(Schema):
    """Esquema para validar descripciones de productos."""
    plain_text = fields.Str(required=True, validate=validate.Length(min=20),
                            description="Descripción en texto plano")


class PictureSchema(Schema):
    """Esquema para validar imágenes de productos."""
    id = fields.Str(required=True, description="ID de la imagen previamente subida")


class ProductDataSchema(Schema):
    """Esquema para validar datos básicos de productos."""
    # Campos estructurales obligatorios
    title = fields.Str(required=True, validate=validate.Length(min=10, max=60),
                       description="Título del producto")
    category_id = fields.Str(required=True, description="ID de categoría en Mercado Libre")
    price = fields.Float(required=True, validate=validate.Range(min=1),
                         description="Precio base del producto")
    currency_id = fields.Str(required=True, description="Código de moneda (ej: MXN)")
    available_quantity = fields.Int(required=True, validate=validate.Range(min=1),
                                    description="Cantidad disponible total")
    buying_mode = fields.Str(required=True, description="Modo de compra")
    condition = fields.Str(required=True, description="Condición del producto")
    listing_type_id = fields.Str(required=True, description="Tipo de publicación (ej: gold_special)")

    # Campos obligatorios para una buena publicación
    description = fields.Nested(DescriptionSchema, required=True,
                                description="Descripción detallada del producto")
    pictures = fields.List(fields.Nested(PictureSchema), required=True,
                           validate=validate.Length(min=1),
                           description="Imágenes del producto")

    # Campos flexibles para atributos y variantes
    attributes = fields.List(fields.Dict(), required=False,
                             description="Atributos del producto")
    variations = fields.List(fields.Dict(), required=False,
                             description="Variantes del producto")
    shipping = fields.Dict(required=False,
                           description="Configuración de envío")
    sale_terms = fields.List(fields.Dict(), required=False,description="Terminos del producto")
    accepts_mercadopago = fields.Boolean(required=False, description="Acepta mercadopago")


class ProductCreateRequestSchema(Schema):
    """Esquema para validar peticiones de creación de productos."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    product_data = fields.Nested(ProductDataSchema, required=True,
                                 description="Datos completos del producto")


class ProductVerifyRequestSchema(Schema):
    """Esquema para validar peticiones de verificación de productos."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    item_id = fields.Str(required=True, description="ID del producto en Mercado Libre")

    @validates('item_id')
    def validate_item_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El item_id debe tener el formato correcto (ej: MLM123456789)")


class ProductUpdateDataSchema(Schema):
    """Esquema para validar datos de actualización de productos."""
    # Campos actualizables principales
    price = fields.Float(validate=validate.Range(min=1), description="Nuevo precio")
    available_quantity = fields.Int(validate=validate.Range(min=0),
                                    description="Nueva cantidad disponible")
    title = fields.Str(validate=validate.Length(min=10, max=60),
                       description="Nuevo título")
    description = fields.Nested(DescriptionSchema, description="Nueva descripción")
    pictures = fields.List(fields.Nested(PictureSchema), description="Nuevas imágenes")

    # Campos flexibles para actualización
    attributes = fields.List(fields.Dict(), required=False, description="Atributos actualizados")
    variations = fields.List(fields.Dict(), required=False, description="Variantes actualizadas")


class ProductUpdateRequestSchema(Schema):
    """Esquema para validar peticiones de actualización de productos."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    item_id = fields.Str(required=True, description="ID del producto en Mercado Libre")
    update_data = fields.Nested(ProductUpdateDataSchema, required=True,
                                description="Datos a actualizar")

    @validates('item_id')
    def validate_item_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El item_id debe tener el formato correcto (ej: MLM123456789)")