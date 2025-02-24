from App.Services.MeliUsersService import MeliUsersService
from App.Services.ResponseHandlerService import ResponseHandlerService


class ProductsController:
    def __init__(self,
                 responseHandlerService:ResponseHandlerService,
                 meliUsersService:MeliUsersService
                 ):
        self.responseHandlerService = responseHandlerService
        self.meliUsersService = meliUsersService
        pass

    def notImplemented(self):
        return self.responseHandlerService.bad_request("method not implemented")

    def get_category_by_product_name(self,data):
        if data is None or len(data) == 0:
            return self.responseHandlerService.bad_request("missing data")
        else:
            self.meliUsersService.getMeliUserByShopId(data["shop_id"])
            return self.responseHandlerService.ok(data)
