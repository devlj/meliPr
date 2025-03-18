import logging
import os
import datetime
from typing import Dict, Any, Optional


class MongoDBHandler(logging.Handler):
    """
    Handler personalizado para enviar logs a MongoDB con formato personalizado.
    """

    def __init__(self, connection_string=None, db_name=None, collection_name=None, mongo_client=None,
                 formatter_func=None):
        super().__init__()
        self.enabled = False
        self.collection = None
        # Función personalizada para formatear el documento que se guardará en MongoDB
        self.formatter_func = formatter_func or self._default_formatter

        # Si se proporciona el cliente o los parámetros de conexión, intentar configurar
        if mongo_client is not None:
            self.setup_mongo_client(mongo_client, db_name, collection_name)
        elif connection_string and db_name and collection_name:
            self.setup_connection(connection_string, db_name, collection_name)

    def setup_connection(self, connection_string, db_name, collection_name):
        """
        Configura la conexión a MongoDB posteriormente.
        """
        try:
            from pymongo import MongoClient
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.enabled = True
        except Exception as e:
            print(f"Error al configurar MongoDB: {str(e)}")
            self.enabled = False

    def setup_mongo_client(self, mongo_client, db_name, collection_name):
        """
        Configura el handler usando un cliente MongoDB existente.
        """
        try:
            self.client = mongo_client
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.enabled = True
        except Exception as e:
            print(f"Error al configurar MongoDB: {str(e)}")
            self.enabled = False

    def set_formatter_func(self, formatter_func):
        """
        Establece la función personalizada de formato para los documentos de MongoDB.
        """
        self.formatter_func = formatter_func

    def _default_formatter(self, record):
        """
        Formateador por defecto si no se proporciona uno personalizado.
        """
        log_entry = {
            "timestamp": datetime.datetime.utcnow(),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "path": record.pathname
        }

        # Añadir datos de excepción si existen
        if record.exc_info:
            log_entry["exception"] = self.formatter.formatException(record.exc_info)

        # Añadir datos personalizados si existen
        if hasattr(record, "extra_data"):
            log_entry["extra_data"] = record.extra_data

        return log_entry

    def emit(self, record):
        """
        Envía el registro de log a MongoDB si está habilitado.
        """
        if not self.enabled or self.collection is None:
            return

        try:
            # Usar el formateador personalizado para crear el documento
            log_entry = self.formatter_func(record)

            # Insertar en MongoDB
            self.collection.insert_one(log_entry)

        except Exception as e:
            # Evitar bucles infinitos de logging
            print(f"Error al guardar log en MongoDB: {str(e)}")


def setup_logger(name, level=logging.INFO, mongodb_config=None, mongo_formatter_func=None):
    """
    Configura y devuelve un logger con el nombre especificado.

    Args:
        name: Nombre del logger
        level: Nivel de logging (default: INFO)
        mongodb_config: Configuración para MongoDB (opcional)
        mongo_formatter_func: Función personalizada para formatear los documentos de MongoDB

    Returns:
        Un objeto logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicación de handlers
    if not logger.handlers:
        # Crear handler para consola
        console_handler = logging.StreamHandler()

        # Determinar formato según entorno
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # En Lambda, usar formato JSON para CloudWatch
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "service":"%(name)s", "message":"%(message)s"}'
            )
        else:
            # Formato estándar para desarrollo
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Aplicar formato a handler de consola
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Crear el handler de MongoDB aunque no esté configurado
        mongo_handler = MongoDBHandler(formatter_func=mongo_formatter_func)
        mongo_handler.setFormatter(formatter)
        logger.addHandler(mongo_handler)

        # Si hay configuración, intentar habilitarlo
        if mongodb_config:
            mongo_handler.setup_connection(
                mongodb_config.get("connection_string"),
                mongodb_config.get("db_name"),
                mongodb_config.get("collection_name")
            )

    return logger


# Obtener el handler de MongoDB si ya existe
def get_mongo_handler(logger):
    """
    Obtiene el handler de MongoDB asociado a un logger.
    """
    for handler in logger.handlers:
        if isinstance(handler, MongoDBHandler):
            return handler
    return None


# Configurar MongoDB posteriormente
def configure_mongodb(logger, connection_string, db_name, collection_name, formatter_func=None):
    """
    Configura MongoDB para un logger existente.

    Args:
        logger: El logger a configurar
        connection_string: URL de conexión a MongoDB
        db_name: Nombre de la base de datos
        collection_name: Nombre de la colección
        formatter_func: Función para formatear los documentos (opcional)
    """
    mongo_handler = get_mongo_handler(logger)
    if mongo_handler:
        if formatter_func:
            mongo_handler.set_formatter_func(formatter_func)
        mongo_handler.setup_connection(connection_string, db_name, collection_name)
    else:
        # Si no existe, crear nuevo handler
        mongo_handler = MongoDBHandler(
            connection_string,
            db_name,
            collection_name,
            formatter_func=formatter_func
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        mongo_handler.setFormatter(formatter)
        logger.addHandler(mongo_handler)


# Ejemplo de formateador personalizado para MongoDB
def custom_mongo_formatter(record):
    """
    Define tu estructura personalizada para el documento de MongoDB aquí.
    """
    # Aquí defines exactamente cómo quieres que sea el objeto que se guarda en MongoDB
    log_entry = {
        "date": datetime.datetime.utcnow().isoformat(),
        "level": record.levelname,
        "app": "meli_api",
        "message": record.getMessage(),
        "source": {
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
    }

    # Añadir datos extra si existen
    if hasattr(record, "extra_data"):
        log_entry["datos_adicionales"] = record.extra_data

    return log_entry


# Logger principal de la aplicación (sin MongoDB por ahora)
app_logger = setup_logger('meli_api', mongo_formatter_func=custom_mongo_formatter)


# Funciones de ayuda para loguear
def info(message, extra_data=None):
    """Registra un mensaje de nivel INFO."""
    if extra_data:
        # Crear un LogRecord personalizado con datos extra
        record = logging.LogRecord(
            name=app_logger.name,
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data

        # Emitir a todos los handlers
        for handler in app_logger.handlers:
            if handler.level <= logging.INFO:
                handler.handle(record)
    else:
        app_logger.info(message)


def warning(message, extra_data=None):
    """Registra un mensaje de nivel WARNING."""
    if extra_data:
        record = logging.LogRecord(
            name=app_logger.name,
            level=logging.WARNING,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data

        for handler in app_logger.handlers:
            if handler.level <= logging.WARNING:
                handler.handle(record)
    else:
        app_logger.warning(message)


def error(message, extra_data=None):
    """Registra un mensaje de nivel ERROR."""
    if extra_data:
        record = logging.LogRecord(
            name=app_logger.name,
            level=logging.ERROR,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data

        for handler in app_logger.handlers:
            if handler.level <= logging.ERROR:
                handler.handle(record)
    else:
        app_logger.error(message)


def debug(message, extra_data=None):
    """Registra un mensaje de nivel DEBUG."""
    if extra_data:
        record = logging.LogRecord(
            name=app_logger.name,
            level=logging.DEBUG,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra_data

        for handler in app_logger.handlers:
            if handler.level <= logging.DEBUG:
                handler.handle(record)
    else:
        app_logger.debug(message)


def exception(message, exc=None, extra_data=None):
    """Registra una excepción."""
    if extra_data:
        record = logging.LogRecord(
            name=app_logger.name,
            level=logging.ERROR,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=sys.exc_info() if exc is None else (type(exc), exc, None)
        )
        record.extra_data = extra_data

        for handler in app_logger.handlers:
            if handler.level <= logging.ERROR:
                handler.handle(record)
    else:
        if exc:
            app_logger.error(message, exc_info=(type(exc), exc, None))
        else:
            app_logger.exception(message)