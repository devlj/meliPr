from dependency_injector import containers, providers

from App.Controllers.CustomController import CustomController
from App.Controllers.ProductsController import ProductsController
from App.Dynamo.MeliUsers import MeliUsers
from App.Services.MeliUsersService import MeliUsersService
from App.Services.ResponseHandlerService import ResponseHandlerService


# factories
class Container(containers.DeclarativeContainer):

    #dynamo
    meli_users = providers.Factory(MeliUsers)


    meli_users_service = providers.Factory(MeliUsersService, meli_users)

    response_handler_service = providers.Factory(ResponseHandlerService)
    custom_controller = providers.Factory(CustomController,response_handler_service)
    products_controller = providers.Factory(ProductsController,response_handler_service,meli_users_service)




