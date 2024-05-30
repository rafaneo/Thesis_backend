import requests
import asyncio

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from api.models import (Order, UserProfile)
from hashids import Hashids
from django.db import IntegrityError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.conf import settings
import environ
from api.contract_abi import Contract
from web3 import Web3
from enum import Enum
env = environ.Env(
    DEBUG=(bool, False)
)

class ErrorCode(Enum):
    INVALID_REQUEST = 1000
    INVALID_TOKEN_ID = 1001
    INVALID_ADDRESS = 1002
    INVALID_EMAIL = 1003
    INVALID_PHONE = 1004
    INVALID_COUNTRY = 1005
    INVALID_CITY = 1006
    INVALID_POSTAL_CODE = 1007
    INVALID_PRODUCT_COST = 1008
    INVALID_TOTAL = 1009
    INVALID_DELIVERY = 1010
    INVALID_SELLER = 1013
    INVALID_BUYER = 1014
    ORDER_EXISTS = 1015
    MISSING_REQUIRED_FIELDS = 1016

def validate_address(address, city, country, postalCode):
    address = address.strip()
    city = city.strip()
    country = country.strip()
    postalCode = postalCode.strip()

    if not address:
        return False
    return True

def validate_phone(phone):
    phone = phone.strip()
    


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

        try:
            validate_email(email)
        except DjangoValidationError:
            data = {
                "message": "Invalid email",
                "error": ErrorCode.INVALID_EMAIL.value
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(data, status=status_code)

        if not tokenId:
            data = {
                "message": "Invalid tokenId",
                "error": ErrorCode.INVALID_TOKEN_ID.value
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(data, status=status_code)

        try :
            validate_address(address)
        except DjangoValidationError as e:
            data = {
                "message": "Invalid address",
                "error": ErrorCode.INVALID_ADDRESS.value
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

            # w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/2bsr75GEPZGZ5I8C7KYtiDpmCDTgQZk4'))

            # if w3.is_connected():
            #     contract_address = env('CONTRACT_ADDRESS')
            #     contract_owner = env('CONTRACT_OWNER')
            #     wallet_private_key = env('WALLET_PRIVATE_KEY')
                 
            #     contract_abi = Contract.abi
            #     contract = w3.eth.contract(address=contract_address, abi=contract_abi)
                
            #     txn = contract.functions.updateOrderNumber( int(order.tokenId), order.order_number)
            #     estimate_gas = txn.estimate_gas({'from': w3.to_checksum_address(contract_owner)})
            #     gas_price = w3.eth.gas_price

            #     txn = txn.build_transaction({
            #         'chainId': 11155111,
            #         'gas': estimate_gas,
            #         'gasPrice': w3.to_wei('100', 'gwei'),
            #         'nonce': w3.eth.get_transaction_count(w3.to_checksum_address(contract_owner)),
            #         'from': w3.to_checksum_address(contract_owner),
            #     })

            #     sign_txn = w3.eth.account.sign_transaction(txn, wallet_private_key)
            #     txn_hash = w3.eth.send_raw_transaction(sign_txn.rawTransaction)
            #     txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
            #     print(txn_receipt)

            #     get_token_data = contract.functions.getTokenData(int(order.tokenId)).call()
            #     print(get_token_data)
            
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

        except IntegrityError as e: 
            print("here")
            print(e.args[0])
            if 'UNIQUE constraint' in e.args[0]:
                data = {
                    "error": "Order already exists"
                }
            else: 
                data = {
                    "error": "An error occurred"
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
        storename = request.data.get("storename")
        wallet_address = request.data.get("wallet_address")

        if not wallet_address or not name or not surname:
            data = {
                "message": "Missing required fields",
                "response": False,
                "error": ErrorCode.INVALID_REQUEST.value
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(data, status=status_code)
        try:
            user = UserProfile.objects.get(wallet_address__exact=wallet_address)
            user.name = name
            user.surname = surname
            user.storename = storename
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
                        storename = storename,
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

class GetAccountDetails(APIView):
    def get(self, request):
        wallet_address = request.headers.get("Wallet-Address")
        try:
            user = UserProfile.objects.get(wallet_address__exact=wallet_address)
            data = {
                "name": user.name,
                "surname": user.surname,
                "storename": user.storename,
                "wallet_address": user.wallet_address
            }
            status_code = status.HTTP_200_OK
        except:
            data = {
                "message": "Account not found"
            }
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(data, status=status_code)