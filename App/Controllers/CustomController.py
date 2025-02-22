from flask import jsonify

from App.Services.ResponseHandlerService import ResponseHandlerService


class CustomController:
    def __init__(self, responseHandlerService: ResponseHandlerService):
        self.responseHandlerService = responseHandlerService
        pass

    def hello(self,data):
        self.responseHandlerService.setData(data)
        return self.responseHandlerService.ok("OK")