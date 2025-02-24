from App.Dynamo.MeliUsers import MeliUsers


class MeliUsersService:
    def __init__(self,meli_users:MeliUsers):
        self.dynamodb = meli_users

    def getMeliUserByShopId(self,shopId:int):
        user = self.dynamodb.get_users_by_shop_id(shopId)
        print(user)
