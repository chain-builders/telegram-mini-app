from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from .bot import TelegramBot

@api_view(['GET'])
# @permission_classes([IsAdminUser])  
def transfer_funds(request):   
    print("Funds transfer initiated")
    # Initialize the TelegramBot instance
    bot_instance = TelegramBot()
    bot_instance.initialize_web3_connections()
    bot_instance.setup_app()
    # Call the transferFunds method
    bot_instance.transferFunds()
    return Response({"message": "Funds transferred successfully!"}, status=200)
