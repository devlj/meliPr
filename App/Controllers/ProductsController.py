from App.Services.MeliProducts import MeliProducts
from App.Services.MeliUsersService import MeliUsersService
from App.Services.ResponseHandlerService import ResponseHandlerService


class ProductsController:
    def __init__(self,
                 responseHandlerService:ResponseHandlerService,
                 meliProducts:MeliProducts,
                 ):
        self.responseHandlerService = responseHandlerService
        self.meliProducts = meliProducts
        pass

    def notImplemented(self):
        return self.responseHandlerService.bad_request("method not implemented")

    def get_category_by_product_name(self,data):
        if data is None or len(data) == 0:
            return self.responseHandlerService.bad_request("missing data")
        else:
            categories = self.meliProducts.get_category_by_product_name(data)
            self.responseHandlerService.setData(categories)
            return self.responseHandlerService.ok("OK")
