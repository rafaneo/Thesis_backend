import requests
import asyncio

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from api.models import (Order, UserProfile)
from hashids import Hashids
from django.core.mail import send_mail
from django.conf import settings
import environ
from api.contract_abi import Contract
from web3 import Web3

env = environ.Env(
    DEBUG=(bool, False)
)


class CreateOrder(APIView):
    def post(self, request):
        email = request.data.get("email")
        name = request.data.get("name")
        surname = request.data.get("surname")
        seller = request.data.get("seller")
        buyer = request.data.get("buyer")
        tokenId = request.data.get("tokenId")
        address = request.data.get("address")
        country = request.data.get("country")
        city = request.data.get("city")
        postalCode = request.data.get("postalCode")
        unit = request.data.get("unit")
        delivery = request.data.get("delivery")
        phone = request.data.get("phone")
        productCost = request.data.get("productCost")
        total = request.data.get("total")
        
        if not email or not seller or not buyer or not tokenId or not address or not country or not city or not postalCode or not delivery or not productCost or not total:
            data = {
                "message": "Missing required fields",
                "response": False
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(data, status=status_code)

        try:
            order = Order.objects.create(
                email = email, #mandatory
                name = name, 
                surname = surname,
                seller = seller, #mandatory
                buyer = buyer, #mandatory
                tokenId = tokenId, #mandatory
                address = address, #mandatory
                country = country, #mandatory
                city = city, #mandatory
                postalCode = postalCode, #mandatory
                unit = unit, 
                delivery = delivery, #mandatory
                phone_number = phone, 
                productCost = productCost, #mandatory
                total = total #mandatory
            )
            order.save()

            w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/2bsr75GEPZGZ5I8C7KYtiDpmCDTgQZk4'))

            if w3.is_connected():
                contract_address = env('CONTRACT_ADDRESS')
                contract_owner = env('CONTRACT_OWNER')
                wallet_private_key = env('WALLET_PRIVATE_KEY')

                contract_abi = Contract.abi
                contract = w3.eth.contract(address=contract_address, abi=contract_abi)
                
                txn = contract.functions.updateOrderNumber( int(order.tokenId), order.order_number)
                estimate_gas = txn.estimate_gas({'from': w3.to_checksum_address(contract_owner)})
                gas_price = w3.eth.gas_price

                txn = txn.build_transaction({
                    'chainId': 11155111,
                    'gas': estimate_gas,
                    'gasPrice': w3.to_wei('10', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(w3.to_checksum_address(contract_owner)),
                    'from': w3.to_checksum_address(contract_owner),
                })
                
                sign_txn = w3.eth.account.sign_transaction(txn, wallet_private_key)
                txn_hash = w3.eth.send_raw_transaction(sign_txn.rawTransaction)
                txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
                print(txn_receipt)

                get_token_data = contract.functions.getTokenData(int(order.tokenId)).call()
                print(get_token_data)
            
            data = {
                "message": "Order created successfully",
                "response": True,
                "order_number": order.order_number
            }
            
            body="""
                    <html>
                        <body>
                            <h2>Thank you for your order!</h2>
                            <p style="color: green;">You order number is <strong>{order.order_number}</strong>.</p>
                            <p>For any problems with your order please mail to this address with this number as subject</p>
                        </body>
                    </html>
                """.format(order=order)
            
            send_mail(
                "Order Confirmation",
                "",
                str(env('SERVER_EMAIL')),
                [str(email),],
                fail_silently=False,
                html_message=body,
            )
            status_code = status.HTTP_200_OK

        except ValidationError as e:
            data = {
                "message": "Validation error occurred",
                "details": str(e)
            }
            status_code = status.HTTP_400_BAD_REQUEST

        except Exception as e:
            print(f"An error occurred: {e}")

            hashid = Hashids(min_length=8, salt="thesis_salt")
            order_number = hashid.encode(int(tokenId)+int(buyer, 16))
            print(order_number)
            if (Order.objects.filter(order_number=order_number).exists()):
                data = {
                    "error": "Order already exists"
                }
            else:
                data = {
                    "error": "An error occurred"
                }
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(data, status=status_code)


class ReturnOrder(APIView):
     def get(self, request):
        order_number = request.headers.get("Order-Number")
        try:
            order = Order.objects.get(order_number__exact=order_number)
            data = {
                "email": order.email,
                "name": order.name,
                "surname": order.surname,
                "buyer": order.buyer,
                "seller": order.seller,
                "tokenId": order.tokenId,
                "address": order.address,
                "country": order.country,
                "city": order.city,
                "postalCode": order.postalCode,
                "unit": order.unit,
                "delivery": order.delivery,
                "phone": str(order.phone_number),
                "productCost": order.productCost,
                "total": order.total
            }
            status_code = status.HTTP_200_OK
        except:
            data = {
                "message": "Order not found"
            }
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(data, status=status_code)

class SaveAccountDetails(APIView):
    def post(self, request):
        name = request.data.get("name")
        surname = request.data.get("surname")
        wallet_address = request.data.get("wallet_address")
        if not wallet_address or not name or not surname:
            data = {
                "message": "Missing required fields",
                "response": False
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(data, status=status_code)
        try:
            user = UserProfile.objects.get(wallet_address__exact=wallet_address)
            user.name = name
            user.surname = surname
            user.save()
            data = {
                "message": "Account details saved successfully",
                "response": True
            }
            status_code = status.HTTP_200_OK
        except Exception as e:
            try:
                user = UserProfile.objects.create(
                        name = name,
                        surname = surname,
                        wallet_address = wallet_address
                    )
                user.save()
                data = {
                        "message": "Account details saved successfully",
                        "response": True
                    }
                status_code = status.HTTP_200_OK

            except ValidationError as e:
                data = {
                    "message": "Validation error occurred",
                    "details": str(e)
                }
                status_code = status.HTTP_400_BAD_REQUEST
        return Response(data, status=status_code)

