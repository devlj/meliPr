from marshmallow import Schema, fields, validates, validate, ValidationError


class ValueSchema(Schema):
    """Esquema para valores de atributos en la guía de tallas."""
    id = fields.Str(required=False, description="ID del valor (opcional)")
    name = fields.Str(required=True, description="Nombre o valor del atributo")


class AttributeValueSchema(Schema):
    """Esquema para atributos con sus valores."""
    id = fields.Str(required=True, description="ID del atributo (ej: AR_SIZE, FOOT_LENGTH)")
    values = fields.List(
        fields.Nested(ValueSchema),
        required=True,
        validate=validate.Length(min=1),
        description="Valores para este atributo"
    )


class MainAttributeSchema(Schema):
    """Esquema para el atributo principal de la guía de tallas."""
    attributes = fields.List(
        fields.Nested(Schema.from_dict({
            "site_id": fields.Str(required=True, description="ID del sitio (ej: MLA, MLM)"),
            "id": fields.Str(required=True, description="ID del atributo principal")
        })),
        required=True,
        validate=validate.Length(min=1),
        description="Atributos principales"
    )


class RowSchema(Schema):
    """Esquema para una fila de la guía de tallas."""
    attributes = fields.List(
        fields.Nested(AttributeValueSchema),
        required=True,
        validate=validate.Length(min=1),
        description="Atributos que conforman esta fila de tallas"
    )


class SizeChartCreateRequestSchema(Schema):
    """Esquema para solicitudes de creación de guías de tallas."""
    shop_id = fields.Str(required=True, description="ID de la tienda")
    names = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        required=True,
        description="Nombres de la guía de tallas por sitio (ej: {'MLA': 'Guía de talles de calzado de hombre'})"
    )
    domain_id = fields.Str(required=True, description="ID del dominio de categoría (ej: SNEAKERS)")
    site_id = fields.Str(required=True, description="ID del sitio (ej: MLA, MLM)")
    main_attribute = fields.Nested(
        MainAttributeSchema,
        required=True,
        description="Configuración del atributo principal"
    )
    attributes = fields.List(
        fields.Nested(AttributeValueSchema),
        required=True,
        description="Atributos generales de la guía de tallas"
    )
    rows = fields.List(
        fields.Nested(RowSchema),
        required=True,
        validate=validate.Length(min=1),
        description="Filas de la guía de tallas"
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