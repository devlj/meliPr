from App.Services.MeliSizeChartService import MeliSizeChartService
from App.Services.ResponseHandlerService import ResponseHandlerService
from App.Utils.Logger import app_logger
from App.Models.Schemas.MeliSizeGridSchemas import (
    SizeChartCreateRequestSchema, SizeChartGetRequestSchema,
    SizeChartListRequestSchema, AssociateSizeChartRequestSchema
)


class SizeChartController:
    """
    Controlador para la gestión de guías de tallas (size charts).
    """

    def __init__(self,
                 response_handler_service: ResponseHandlerService,
                 meli_size_chart_service: MeliSizeChartService):
        self.response_handler_service = response_handler_service
        self.meli_size_chart_service = meli_size_chart_service

        # Esquemas de validación
        self.list_schema = SizeChartListRequestSchema()
        self.get_schema = SizeChartGetRequestSchema()
        self.create_schema = SizeChartCreateRequestSchema()
        self.associate_schema = AssociateSizeChartRequestSchema()

    def not_implemented(self):
        """Método para manejar solicitudes no implementadas."""
        app_logger.warning("Método no implementado llamado")
        return self.response_handler_service.bad_request("method not implemented")

    def _validate_data(self, schema, data):
        """Valida los datos con el esquema especificado."""
        errors = schema.validate(data)
        if errors:
            app_logger.warning(f"Errores de validación: {errors}")
            return False, errors
        return True, None

    def list_size_charts(self, data):
        """Lista todas las guías de tallas disponibles."""
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en list_size_charts")
            return self.response_handler_service.bad_request("missing data")

        # Validar datos
        valid, errors = self._validate_data(self.list_schema, data)
        if not valid:
            return self.response_handler_service.bad_request(errors)

        # Procesar solicitud
        app_logger.info(f"Listando guías de tallas para shop_id: {data.get('shop_id')}")
        result = self.meli_size_chart_service.list_size_charts(data)

        # Manejar errores
        if "error" in result:
            app_logger.warning(f"Error al listar guías de tallas: {result.get('error')}")
            return self.response_handler_service.bad_request(result)

        # Devolver resultado exitoso
        self.response_handler_service.setData(result)
        return self.response_handler_service.ok("OK")

    def get_size_chart(self, data):
        """Obtiene una guía de tallas específica."""
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en get_size_chart")
            return self.response_handler_service.bad_request("missing data")

        # Validar datos
        valid, errors = self._validate_data(self.get_schema, data)
        if not valid:
            return self.response_handler_service.bad_request(errors)

        # Procesar solicitud
        app_logger.info(f"Obteniendo guía de tallas {data.get('size_chart_id')} para shop_id: {data.get('shop_id')}")
        result = self.meli_size_chart_service.get_size_chart(data)

        # Manejar errores
        if "error" in result:
            app_logger.warning(f"Error al obtener guía de tallas: {result.get('error')}")
            return self.response_handler_service.bad_request(result)

        # Devolver resultado exitoso
        self.response_handler_service.setData(result)
        return self.response_handler_service.ok("OK")

    def create_size_chart(self, data):
        """Crea una nueva guía de tallas."""
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en create_size_chart")
            return self.response_handler_service.bad_request("missing data")

        # Validar datos
        valid, errors = self._validate_data(self.create_schema, data)
        if not valid:
            return self.response_handler_service.bad_request(errors)

        # Procesar solicitud
        app_logger.info(f"Creando guía de tallas '{data.get('title')}' para shop_id: {data.get('shop_id')}")
        result = self.meli_size_chart_service.create_size_chart(data)

        # Manejar errores
        if "error" in result:
            app_logger.warning(f"Error al crear guía de tallas: {result.get('error')}")
            return self.response_handler_service.bad_request(result)

        # Devolver resultado exitoso
        self.response_handler_service.setData(result)
        return self.response_handler_service.ok("OK")

    def associate_size_chart(self, data):
        """Asocia una guía de tallas a un producto."""
        if data is None or len(data) == 0:
            app_logger.warning("Datos faltantes en associate_size_chart")
            return self.response_handler_service.bad_request("missing data")

        # Validar datos
        valid, errors = self._validate_data(self.associate_schema, data)
        if not valid:
            return self.response_handler_service.bad_request(errors)

        # Procesar solicitud
        app_logger.info(f"Asociando guía de tallas {data.get('size_chart_id')} al producto {data.get('item_id')}")
        result = self.meli_size_chart_service.associate_size_chart(data)

        # Manejar errores
        if "error" in result:
            app_logger.warning(f"Error al asociar guía de tallas: {result.get('error')}")
            return self.response_handler_service.bad_request(result)

        # Devolver resultado exitoso
        self.response_handler_service.setData(result)
        return self.response_handler_service.ok("OK")