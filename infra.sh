#!/bin/bash

# Solicitar Región y ID de cuenta al usuario
read -p "🌎 Ingresa la región AWS (ej. us-east-2): " REGION
read -p "🔑 Ingresa tu ID de cuenta AWS: " ACCOUNT_ID

# Configuración de API Gateway y Lambda
API_ID="kqu4vgt9uk"  # ID de API Gateway
PARENT_ID="se2oqp"   # ID del recurso /meli
LAMBDA_NAME="meliProductsAPI"
LAMBDA_ROLE_NAME="MeliProductsLambdaRole"
ZIP_FILE="lambda_package.zip"

# Función para empaquetar la Lambda
package_lambda() {
    echo "🚀 Empaquetando código de la Lambda..."
    mkdir -p lambda
    echo '
import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from meliProductsAPI on ARM64!"})
    }
' > lambda/lambda_function.py

    cd lambda || exit
    zip -r9 ../$ZIP_FILE .
    cd ..
    echo "✅ Código de la Lambda empaquetado."
}

# Función para crear/actualizar Lambda
deploy_lambda() {
    package_lambda
    ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null)

    if [ -z "$ROLE_ARN" ]; then
        echo "🚀 Creando rol IAM para Lambda..."
        ROLE_ARN=$(aws iam create-role \
            --role-name "$LAMBDA_ROLE_NAME" \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }' --query 'Role.Arn' --output text)

        aws iam attach-role-policy --role-name "$LAMBDA_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        sleep 5
        echo "✅ Rol IAM creado y políticas asignadas."
    else
        echo "✅ Rol IAM ya existe."
    fi

    LAMBDA_ARN=$(aws lambda get-function --function-name "$LAMBDA_NAME" --query 'Configuration.FunctionArn' --output text 2>/dev/null)

    if [ -z "$LAMBDA_ARN" ]; then
        echo "🚀 Creando función Lambda $LAMBDA_NAME..."
        LAMBDA_ARN=$(aws lambda create-function \
            --function-name "$LAMBDA_NAME" \
            --runtime python3.10 \
            --role "$ROLE_ARN" \
            --handler lambda_function.lambda_handler \
            --zip-file fileb://$ZIP_FILE \
            --architectures x86_64 \
            --region "$REGION" \
            --query 'FunctionArn' --output text)
        echo "✅ Lambda creada con ARN: $LAMBDA_ARN"
    else
        echo "🚀 Actualizando código de la Lambda..."
        aws lambda update-function-code --function-name "$LAMBDA_NAME" --zip-file fileb://$ZIP_FILE --region "$REGION"
        echo "✅ Código de Lambda actualizado."
    fi
}

# Función para crear/actualizar API Gateway con /meli/products
deploy_api_gateway() {
    echo "🚀 Creando/verificando recurso /meli/products en API Gateway..."
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id "$API_ID" --region "$REGION" --query "items[?path=='/meli/products'].id" --output text)

    if [ -z "$RESOURCE_ID" ]; then
        RESOURCE_ID=$(aws apigateway create-resource \
            --rest-api-id "$API_ID" \
            --parent-id "$PARENT_ID" \
            --path-part "products" \
            --region "$REGION" \
            --query 'id' --output text)
        echo "✅ Recurso /meli/products creado con ID: $RESOURCE_ID"
    else
        echo "✅ Recurso /meli/products ya existe con ID: $RESOURCE_ID"
    fi

    echo "🚀 Configurando método ANY en /meli/products..."
    aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --http-method ANY --authorization-type NONE --region "$REGION"

    echo "🚀 Configurando integración con Lambda..."
    aws apigateway put-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method ANY \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
        --region "$REGION"
    echo "✅ Integración con Lambda configurada."

    echo "🚀 Dando permisos a API Gateway para invocar Lambda..."
    aws lambda add-permission \
        --function-name "$LAMBDA_NAME" \
        --statement-id "apigateway-invoke" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/ANY/meli/products" \
        --region "$REGION"
    echo "✅ Permisos de API Gateway para Lambda agregados."

    echo "🚀 Desplegando cambios en API Gateway..."
    aws apigateway create-deployment --rest-api-id "$API_ID" --stage-name "development" --region "$REGION"
    echo "✅ Despliegue exitoso."
}

# Función para hacer rollback
rollback() {
    echo "🚀 Eliminando recurso /meli/products de API Gateway..."
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id "$API_ID" --region "$REGION" --query "items[?path=='/meli/products'].id" --output text)

    if [ -n "$RESOURCE_ID" ]; then
        aws apigateway delete-resource --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" --region "$REGION"
        echo "✅ Recurso /meli/products eliminado."
    else
        echo "⚠️ No se encontró el recurso /meli/products."
    fi
}

# Función para eliminar todo
delete_all() {
    echo "🚀 Eliminando Lambda..."
    aws lambda delete-function --function-name "$LAMBDA_NAME" --region "$REGION"

    echo "🚀 Eliminando recurso /meli/products de API Gateway..."
    rollback

    echo "🚀 Eliminando rol IAM..."
    aws iam delete-role --role-name "$LAMBDA_ROLE_NAME" --region "$REGION"

    echo "✅ Todo ha sido eliminado."
}

# Menú interactivo
while true; do
    echo "========================="
    echo "🚀 MENÚ DE DESPLIEGUE 🚀"
    echo "1. Deploy completo"
    echo "2. Rollback (Eliminar /meli/products)"
    echo "3. Eliminar todo"
    echo "4. Salir"
    echo "========================="
    read -p "Selecciona una opción: " choice

    case $choice in
        1) deploy_lambda && deploy_api_gateway ;;
        2) rollback ;;
        3) delete_all ;;
        4) echo "👋 Saliendo..." && exit ;;
        *) echo "❌ Opción no válida. Intenta de nuevo." ;;
    esac
done