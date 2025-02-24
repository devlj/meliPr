import boto3
from botocore.exceptions import BotoCoreError, ClientError

class MeliUsers:
    def __init__(self, table_name = "meli_users", region_name="us-east-2"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def create_user(self, user_id, access_token, created_at, expires_in, refresh_token, shop_id, token_type):
        try:
            self.table.put_item(
                Item={
                    "user_id": user_id,
                    "access_token": access_token,
                    "created_at": created_at,
                    "expires_in": expires_in,
                    "refresh_token": refresh_token,
                    "shop_id": shop_id,
                    "token_type": token_type
                }
            )
            return {"message": "User created successfully"}
        except (BotoCoreError, ClientError) as error:
            return {"error": str(error)}

    def get_user_by_id(self, user_id):
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            return response.get("Item", None)
        except (BotoCoreError, ClientError) as error:
            return {"error": str(error)}

    def get_users_by_shop_id(self, shop_id):
        try:
            response = self.table.query(
                IndexName="shop_id-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key("shop_id").eq(str(shop_id))
            )
            return response.get("Items", [])
        except (BotoCoreError, ClientError) as error:
            return {"error": str(error)}

    def update_user(self, user_id, updates):
        try:
            update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in updates.keys())
            expression_values = {f":{k}": v for k, v in updates.items()}
            self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return {"message": "User updated successfully"}
        except (BotoCoreError, ClientError) as error:
            return {"error": str(error)}

    def delete_user(self, user_id):
        try:
            self.table.delete_item(Key={"user_id": user_id})
            return {"message": "User deleted successfully"}
        except (BotoCoreError, ClientError) as error:
            return {"error": str(error)}