from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
 
 
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
 
    if response is not None:
        response.data = {
            "error": True,
            "detail": response.data,
        }
        return response
 
    # Excepción no manejada por DRF (ej. un error de programación, un bug)
    return Response(
        {"error": True, "detail": "Error interno del servidor."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )