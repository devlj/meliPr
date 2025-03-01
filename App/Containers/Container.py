from dependency_injector import containers, providers

from App.Controllers.CustomController import CustomController
from App.Controllers.ProductsController import ProductsController
from App.Dynamo.MeliUsers import MeliUsers
from App.Services.AccessTokenService import AccessTokenService
from App.Services.MeliProducts import MeliProducts
from App.Services.MeliUsersService import MeliUsersService
from App.Services.ResponseHandlerService import ResponseHandlerService


# factories
class Container(containers.DeclarativeContainer):

    #dynamo
    meli_users = providers.Factory(MeliUsers)


    access_token_service = providers.Factory(AccessTokenService)
    meli_users_service = providers.Factory(MeliUsersService, meli_users,access_token_service)
    meli_products_service = providers.Factory(MeliProducts, meli_users_service)

    response_handler_service = providers.Factory(ResponseHandlerService)
    custom_controller = providers.Factory(CustomController,response_handler_service)
    products_controller = providers.Factory(ProductsController,response_handler_service,meli_products_service)




