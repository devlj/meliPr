from marshmallow import Schema, fields, validates, validate, ValidationError
import re


class CategoryRequestSchema(Schema):
    """Esquema para validar peticiones de búsqueda de categorías."""
    shop_id = fields.Str(required=True)
    product_name = fields.Str(required=True, validate=validate.Length(min=3, max=60))


class CategoryAttributesRequestSchema(Schema):
    """Esquema para validar peticiones de atributos de categoría."""
    shop_id = fields.Str(required=True)
    category_id = fields.Str(required=True)

    @validates('category_id')
    def validate_category_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El category_id debe tener el formato correcto (ej: MLM1055)")


class ImageUploadRequestSchema(Schema):
    """Esquema para validar peticiones de subida de imágenes."""
    shop_id = fields.Str(required=True)
    image_data = fields.Str(required=True)


class ProductAttributeSchema(Schema):
    """Esquema para validar atributos de productos."""
    id = fields.Str(required=True)
    value_name = fields.Str(required=True)


class PictureSchema(Schema):
    """Esquema para validar imágenes de productos."""
    id = fields.Str(required=True)


class SaleTermSchema(Schema):
    """Esquema para validar términos de venta."""
    id = fields.Str(required=True)
    value_name = fields.Str(required=True)


class DescriptionSchema(Schema):
    """Esquema para validar descripciones de productos."""
    plain_text = fields.Str(required=True, validate=validate.Length(min=20))


class ShippingSchema(Schema):
    """Esquema para validar información de envío."""
    mode = fields.Str()
    local_pick_up = fields.Bool()
    free_shipping = fields.Bool()
    methods = fields.List(fields.Dict())
    dimensions = fields.Str()


class ProductDataSchema(Schema):
    """Esquema para validar datos completos de productos."""
    title = fields.Str(required=True, validate=validate.Length(min=10, max=60))
    category_id = fields.Str(required=True)
    price = fields.Float(required=True, validate=validate.Range(min=1))
    currency_id = fields.Str(required=True)
    available_quantity = fields.Int(required=True, validate=validate.Range(min=1))
    buying_mode = fields.Str(required=True)
    condition = fields.Str(required=True)
    listing_type_id = fields.Str(required=True)
    description = fields.Nested(DescriptionSchema, required=True)
    sale_terms = fields.List(fields.Nested(SaleTermSchema), required=False)
    pictures = fields.List(fields.Nested(PictureSchema), required=True, validate=validate.Length(min=1))
    attributes = fields.List(fields.Nested(ProductAttributeSchema), required=True, validate=validate.Length(min=1))
    shipping = fields.Nested(ShippingSchema, required=False)


class ProductCreateRequestSchema(Schema):
    """Esquema para validar peticiones de creación de productos."""
    shop_id = fields.Str(required=True)
    product_data = fields.Nested(ProductDataSchema, required=True)


class ProductVerifyRequestSchema(Schema):
    """Esquema para validar peticiones de verificación de productos."""
    shop_id = fields.Str(required=True)
    item_id = fields.Str(required=True)

    @validates('item_id')
    def validate_item_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El item_id debe tener el formato correcto (ej: MLM123456789)")


class ProductUpdateDataSchema(Schema):
    """Esquema para validar datos de actualización de productos."""
    price = fields.Float(validate=validate.Range(min=1))
    available_quantity = fields.Int(validate=validate.Range(min=0))
    title = fields.Str(validate=validate.Length(min=10, max=60))
    description = fields.Nested(DescriptionSchema)
    pictures = fields.List(fields.Nested(PictureSchema))
    # Puedes añadir más campos actualizables según sea necesario


class ProductUpdateRequestSchema(Schema):
    """Esquema para validar peticiones de actualización de productos."""
    shop_id = fields.Str(required=True)
    item_id = fields.Str(required=True)
    update_data = fields.Nested(ProductUpdateDataSchema, required=True)

    @validates('item_id')
    def validate_item_id(self, value):
        if not re.match(r'^ML[A-Z][0-9]+$', value):
            raise ValidationError("El item_id debe tener el formato correcto (ej: MLM123456789)")