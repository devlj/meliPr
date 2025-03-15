from datetime import datetime
import inspect
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from App.Models.Schemas.MeliSchemas import (
    CategoryRequestSchema, CategoryAttributesRequestSchema, ImageUploadRequestSchema,
    ProductDataSchema, ProductCreateRequestSchema, ProductVerifyRequestSchema, ProductUpdateRequestSchema
)
from App.Utils.Logger import app_logger


class MeliRulesHelper:
    """
    Clase auxiliar para extraer dinámicamente las reglas de validación
    de los esquemas Marshmallow para la API de Mercado Libre.
    """

    def __init__(self):
        # Mapeo de tipos de Marshmallow a tipos en el formato requerido
        self.type_mapping = {
            fields.String: "string",
            fields.Str: "string",
            fields.Integer: "integer",
            fields.Int: "integer",
            fields.Float: "double",
            fields.Number: "double",
            fields.Boolean: "boolean",
            fields.Bool: "boolean",
            fields.Dict: "object",
            fields.List: "arrayObject",
            fields.Nested: "object"
        }

    def get_field_type(self, field):
        """Determina el tipo de un campo de Marshmallow."""
        for field_cls, type_name in self.type_mapping.items():
            if isinstance(field, field_cls):
                if isinstance(field, fields.Nested):
                    return "object"
                elif isinstance(field, fields.List):
                    if field.inner and isinstance(field.inner, fields.Nested):
                        return "arrayObject"
                    return "arrayObject"
                return type_name
        return "string"  # Tipo por defecto

    def extract_field_rules(self, field_name, field, schema_cls=None):
        """Extrae las reglas de validación de un campo."""
        try:
            rules = {
                "type": self.get_field_type(field),
                "required": field.required,
                "is_show": True,
                "description": field.metadata.get("description", f"{field_name}")
            }

            # Extraer reglas de validadores
            for validator in field.validators:
                if hasattr(validator, "min") and validator.min is not None:
                    if isinstance(validator, validate.Length):
                        rules["min_length"] = validator.min
                    else:
                        rules["min"] = validator.min

                if hasattr(validator, "max") and validator.max is not None:
                    if isinstance(validator, validate.Length):
                        rules["max_length"] = validator.max
                    else:
                        rules["max"] = validator.max

                if hasattr(validator, "choices") and validator.choices:
                    rules["acepted"] = list(validator.choices)

                if hasattr(validator, "equal") and validator.equal is not None:
                    rules["equal"] = validator.equal

            # Buscar validadores personalizados
            if schema_cls:
                for name, method in inspect.getmembers(schema_cls, predicate=inspect.isfunction):
                    if name == f"validate_{field_name}":
                        rules["has_custom_validation"] = True

            # Para campos anidados, extraer reglas de campos internos
            if isinstance(field, fields.Nested) and field.schema:
                nested_schema = field.schema
                if isinstance(nested_schema, type) and issubclass(nested_schema, Schema):
                    nested_schema = nested_schema()

                if hasattr(nested_schema, 'fields'):
                    nested_rules = {}
                    for nested_field_name, nested_field in nested_schema.fields.items():
                        nested_rules[nested_field_name] = self.extract_field_rules(
                            nested_field_name, nested_field, nested_schema.__class__)

                    rules["keys"] = nested_rules

            # Para campos Dict generales, indicar que pueden contener cualquier estructura
            if isinstance(field, fields.Dict):
                rules["flexible"] = True
                rules["description"] += " (estructura flexible)"

            # Para listas de campos anidados o campos Dict
            if isinstance(field, fields.List):
                if isinstance(field.inner, fields.Nested) and hasattr(field.inner.schema, 'fields'):
                    nested_schema = field.inner.schema
                    if isinstance(nested_schema, type) and issubclass(nested_schema, Schema):
                        nested_schema = nested_schema()

                    nested_rules = {}
                    for nested_field_name, nested_field in nested_schema.fields.items():
                        nested_rules[nested_field_name] = self.extract_field_rules(
                            nested_field_name, nested_field, nested_schema.__class__)

                    rules["keys"] = nested_rules
                elif isinstance(field.inner, fields.Dict):
                    rules["flexible"] = True
                    rules["description"] += " (estructura flexible)"

            return rules
        except Exception as e:
            app_logger.warning(f"Error al procesar campo {field_name}: {str(e)}")
            # Devolver tipo y requerido para no romper la estructura
            return {
                "type": self.get_field_type(field),
                "required": field.required,
                "is_show": True,
                "description": f"{field_name}"
            }

    def extract_schema_rules(self, schema):
        """Extrae reglas de todos los campos de un esquema."""
        if isinstance(schema, type) and issubclass(schema, Schema):
            schema = schema()

        rules = {}
        for field_name, field in schema.fields.items():
            rules[field_name] = self.extract_field_rules(field_name, field, schema.__class__)

        return rules

    def get_normalized_rules(self):
        """
        Extrae y normaliza las reglas del esquema principal.
        """
        try:
            # Extraer reglas del esquema principal (ProductDataSchema)
            product_schema = ProductDataSchema()
            product_rules = self.extract_schema_rules(product_schema)

            # Agregar campo uniqueId que no está en el esquema pero es importante
            normalized_rules = {
                "uniqueId": {
                    "type": "integer",
                    "required": True,
                    "is_show": False,
                    "description": "ID único del producto en sistema"
                }
            }

            # Añadir reglas extraídas
            for field_name, rules in product_rules.items():
                normalized_rules[field_name] = rules

            # Agregar nota sobre atributos por categoría
            if "attributes" in normalized_rules:
                normalized_rules["attributes"][
                    "note"] = "Consulte el endpoint /categories/{category_id}/attributes para ver requisitos específicos por categoría"

            if "variations" in normalized_rules:
                normalized_rules["variations"][
                    "note"] = "Consulte el endpoint /categories/{category_id}/attributes para ver qué atributos permiten variantes"

                # Si variations es flexible, añadir estructura esperada por MeLi
                if normalized_rules["variations"].get("flexible"):
                    normalized_rules["variations"]["expected_structure"] = {
                        "available_quantity": {
                            "type": "integer",
                            "required": True,
                            "description": "Cantidad disponible de esta variante"
                        },
                        "price": {
                            "type": "double",
                            "required": True,
                            "description": "Precio de la variante"
                        },
                        "attribute_combinations": {
                            "type": "arrayObject",
                            "required": True,
                            "description": "Combinaciones de atributos que definen la variante",
                            "keys": {
                                "id": {
                                    "type": "string",
                                    "required": True,
                                    "description": "ID del atributo (ej: COLOR, SIZE)"
                                },
                                "value_id": {
                                    "type": "string",
                                    "required": True,
                                    "description": "ID del valor"
                                },
                                "value_name": {
                                    "type": "string",
                                    "required": True,
                                    "description": "Nombre del valor"
                                }
                            }
                        }
                    }

            # Agregar reglas para tipos de fotos
            normalized_rules["photos_types_rules"] = {
                "types": [
                    {
                        "type": "MAIN",
                        "max_quantity": 1,
                        "min_quantity": 1,
                        "sizes_px": [{"min": 900, "max": 2200, "ratio": "1:1"}],
                        "file_size_max_mb": 3,
                        "description": "Imagen principal del producto"
                    },
                    {
                        "type": "DETAIL",
                        "max_quantity": 10,
                        "min_quantity": 1,
                        "sizes_px": [{"min": 900, "max": 2200, "ratio": "1:1"}],
                        "file_size_max_mb": 3,
                        "description": "Imágenes de detalle del producto"
                    }
                ],
                "formats": ["jpg", "jpeg", "png"]
            }

            return {
                "rules": normalized_rules,
                "timestamp": datetime.now().isoformat(),
                "message": "Especificación de datos para validación en Mercado Libre"
            }

        except Exception as e:
            app_logger.error(f"Error al generar reglas normalizadas: {str(e)}")
            # Fallback a reglas básicas si hay error
            return {
                "rules": {
                    "title": {
                        "type": "string",
                        "required": True,
                        "is_show": True,
                        "description": "Título del producto"
                    },
                    "category_id": {
                        "type": "string",
                        "required": True,
                        "is_show": True,
                        "description": "ID de categoría en Mercado Libre"
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "message": "Reglas básicas (modo fallback)"
            }