from marshmallow import Schema, fields, validates, validate, ValidationError


class MeasurementSchema(Schema):
    """Esquema para medidas específicas en una guía de tallas."""
    id = fields.Str(required=True, description="ID del tipo de medida (ej: SHOULDER_WIDTH, LENGTH)")
    value = fields.Float(required=True, description="Valor de la medida")
    unit = fields.Str(required=True, description="Unidad de medida (ej: cm, in)")


class SizeRowSchema(Schema):
    """Esquema para una fila de talla en la guía."""
    size = fields.Str(required=True, description="Nombre de la talla (ej: S, M, L)")
    measurements = fields.List(
        fields.Nested(MeasurementSchema),
        required=True,
        validate=validate.Length(min=1),
        description="Medidas para esta talla"
    )


class SizeChartCreateRequestSchema(Schema):
    """Esquema para solicitudes de creación de guías de tallas."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    title = fields.Str(required=True, description="Título de la guía de tallas")
    domain_id = fields.Str(required=True, description="Category domain ID")
    description = fields.Str(required=False, description="Descripción de la guía de tallas (opcional)")
    category_id = fields.Str(required=True, description="ID de la categoría para esta guía")
    rows = fields.List(
        fields.Nested(SizeRowSchema),
        required=True,
        validate=validate.Length(min=1),
        description="Filas de tallas con sus medidas"
    )


class SizeChartGetRequestSchema(Schema):
    """Esquema para solicitudes de obtención de una guía de tallas específica."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    size_chart_id = fields.Str(required=True, description="ID de la guía de tallas")


class SizeChartListRequestSchema(Schema):
    """Esquema para solicitudes de listado de guías de tallas."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    limit = fields.Int(required=False, description="Límite de resultados a devolver (opcional)")
    offset = fields.Int(required=False, description="Offset para paginación (opcional)")


class AssociateSizeChartRequestSchema(Schema):
    """Esquema para solicitudes de asociación de guías de tallas a productos."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    item_id = fields.Str(required=True, description="ID del producto en Mercado Libre")
    size_chart_id = fields.Str(required=True, description="ID de la guía de tallas a asociar")