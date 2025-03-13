import logging
import os


def setup_logger(name, level=logging.INFO):
    """
    Configura y devuelve un logger con el nombre especificado.

    Args:
        name: Nombre del logger
        level: Nivel de logging (default: INFO)

    Returns:
        Un objeto logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicación de handlers
    if not logger.handlers:
        # Crear handler para consola
        handler = logging.StreamHandler()

        # Determinar formato según entorno
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # En Lambda, usar formato JSON para CloudWatch
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "service":"%(name)s", "message":"%(message)s"}'
            )
        else:
            # Formato estándar para desarrollo
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Aplicar formato
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Logger principal de la aplicación
app_logger = setup_logger('meli_api')