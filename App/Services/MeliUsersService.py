from App.Dynamo.MeliUsers import MeliUsers
from App.Services.AccessTokenService import AccessTokenService


class MeliUsersService:
    def __init__(self,meli_users:MeliUsers,accessTokenService:AccessTokenService):
        self.dynamodb = meli_users
        self.accessTokenService = accessTokenService

    def getMeliUserByShopId(self,shopId:int):
        user = self.dynamodb.get_users_by_shop_id(shopId)
        return user

    def refreshAccessToken(self,user):
        return self.accessTokenService.execption401(user)
