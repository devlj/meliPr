class MeliApiError(Exception):
    """Excepción personalizada para errores de la API de Mercado Libre."""

    def __init__(self, status_code, message, details=None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f"MeliApiError: {self.status_code} - {self.message}"


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""

    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f"ValidationError: {self.message}"


class NotFoundError(Exception):
    """Excepción personalizada para recursos no encontrados."""

    def __init__(self, resource_type, resource_id):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = f"{resource_type} no encontrado con ID: {resource_id}"
        super().__init__(self.message)

    def __str__(self):
        return f"NotFoundError: {self.message}"


class AuthenticationError(Exception):
    """Excepción personalizada para errores de autenticación."""

    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f"AuthenticationError: {self.message}"