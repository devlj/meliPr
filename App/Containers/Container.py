from dependency_injector import containers, providers

from App.Controllers.CustomController import CustomController
from App.Services.ResponseHandlerService import ResponseHandlerService


# factories
class Container(containers.DeclarativeContainer):
    response_handler_service = providers.Factory(ResponseHandlerService)
    custom_controller = providers.Factory(CustomController,response_handler_service)


