rm -rf package
pip install -r requirements.txt
mkdir package
pip install -r requirements.txt -t package/
rm -rf lambda_function.zip
cp *.py package/
cp -r App package
cd package
zip -r ../lambda_function.zip .
cd ..
rm -rf package
aws lambda update-function-code --function-name meliProductsAPI --zip-file fileb://lambda_function.zip >> /tmp/null
rm -rf lambda_function.zip