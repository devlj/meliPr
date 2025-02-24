from App.Dynamo.MeliUsers import MeliUsers
from App.Services.AccessTokenService import AccessTokenService


class MeliUsersService:
    def __init__(self,meli_users:MeliUsers,accessTokenService:AccessTokenService):
        self.dynamodb = meli_users
        self.accessTokenService = accessTokenService

    def getMeliUserByShopId(self,shopId:int):
        user = self.dynamodb.get_users_by_shop_id(shopId)
        print(user)
        self.accessTokenService.refresh_access_token_via_api(user[0]["refresh_token"])
