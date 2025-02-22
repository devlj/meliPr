import time


class ResponseHandlerService:
    def __init__(self):
        self._metaData = {
            "is_error": False,
            "http_status": 200,
            "http_status_phrase": "OK",
            "message": "OK",
            "time": int(time.time())
        }
        self._data = {}
        self._pagination = {
            "total_items": 0,
            "total_pages": 0,
            "current_page": 0,
            "items_per_page": 0
        }
        pass

    def buildMetadata(self, is_error, http_status, http_status_phrase, message):
        self._metaData['is_error'] = is_error
        self._metaData['http_status'] = http_status
        self._metaData['http_status_phrase'] = http_status_phrase
        self._metaData['message'] = message

    def buildPaginatedResponse(self, total_items, total_pages, current_page, items_per_page):
        self._pagination['total_items'] = total_items
        self._pagination['total_pages'] = total_pages
        self._pagination['current_page'] = current_page
        self._pagination['items_per_page'] = items_per_page

    def setData(self, data):
        self._data = data

    def doResponse(self):
        return {
            "metaData": self._metaData,
            "data": self._data,
            "pagination": self._pagination
        }, self._metaData["http_status"]

    def bad_request(self, message="Bad Request") -> tuple:
        """
        Retorna una respuesta de error 400 (Bad Request).
        """
        self.buildMetadata(
            True,
            400,
            "Bad Request",
            message
        )
        return self.doResponse()

    def unauthorized(self, message="Unauthorized") -> tuple:
        """
        Retorna una respuesta de error 401 (Unauthorized).
        """
        self.buildMetadata(
            True,
            401,
            "Unauthorized",
            message
        )
        return self.doResponse()

    def forbidden(self, message="Forbidden") -> tuple:
        """
        Retorna una respuesta de error 403 (Forbidden).
        """
        self.buildMetadata(
            True,
            403,
            "Forbidden",
            message
        )
        return self.doResponse()

    def not_found(self, message="Not Found") -> tuple:
        """
        Retorna una respuesta de error 404 (Not Found).
        """
        self.buildMetadata(
            True,
            404,
            "Not Found",
            message
        )
        return self.doResponse()

    def internal_server_error(self, message="Internal Server Error") -> tuple:
        """
        Retorna una respuesta de error 500 (Internal Server Error).
        """
        self.buildMetadata(
            True,
            500,
            "Internal Server Error",
            message
        )
        return self.doResponse()

    def ok(self, message="OK") -> tuple:
        """
        Retorna una respuesta de error 500 (Internal Server Error).
        """
        self.buildMetadata(
            False,
            200,
            "OK",
            message
        )
        return self.doResponse()
