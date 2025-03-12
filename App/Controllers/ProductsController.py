from App.Services.MeliProducts import MeliProducts
from App.Services.ResponseHandlerService import ResponseHandlerService


class ProductsController:
    def __init__(self,
                 responseHandlerService: ResponseHandlerService,
                 meliProducts: MeliProducts,
                 ):
        self.responseHandlerService = responseHandlerService
        self.meliProducts = meliProducts
        pass

    def notImplemented(self):
        return self.responseHandlerService.bad_request("method not implemented")

    def get_category_by_product_name(self, data):
        if data is None or len(data) == 0:
            return self.responseHandlerService.bad_request("missing data")
        else:
            categories = self.meliProducts.get_category_by_product_name(data)
            self.responseHandlerService.setData(categories)
            return self.responseHandlerService.ok("OK")

    def get_category_attributes(self, data):
        if data is None or len(data) == 0 or 'category_id' not in data:
            return self.responseHandlerService.bad_request("missing data or category_id")
        else:
            attributes = self.meliProducts.get_category_attributes(data)
            self.responseHandlerService.setData(attributes)
            return self.responseHandlerService.ok("OK")

    def upload_image(self, data):
        if data is None or len(data) == 0 or 'image_data' not in data:
            return self.responseHandlerService.bad_request("missing data or image_data")
        else:
            result = self.meliProducts.upload_image(data)
            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def create_product(self, data):
        if data is None or len(data) == 0 or 'product_data' not in data:
            return self.responseHandlerService.bad_request("missing data or product_data")
        else:
            result = self.meliProducts.create_product(data)
            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def verify_product(self, data):
        if data is None or len(data) == 0 or 'item_id' not in data:
            return self.responseHandlerService.bad_request("missing data or item_id")
        else:
            result = self.meliProducts.verify_product(data)
            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")

    def update_product(self, data):
        if data is None or len(data) == 0 or 'item_id' not in data or 'update_data' not in data:
            return self.responseHandlerService.bad_request("missing data, item_id or update_data")
        else:
            result = self.meliProducts.update_product(data)
            self.responseHandlerService.setData(result)
            return self.responseHandlerService.ok("OK")