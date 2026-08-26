productos = [
    {"nombre": "Laptop", "precio": 1200, "stock": 15},
    {"nombre": "Mouse", "precio": 25, "stock": 5},
    {"nombre": "Teclado", "precio": 75, "stock": 25},
    {"nombre": "Monitor", "precio": 300, "stock": 8},
]

#esta linea hace...
# productos_bajo_stock = []
# for producto in productos:
#     print(f"Producto: {producto['nombre']}, Precio: ${producto['precio']}")
#     if producto['stock'] < 10:
#         productos_bajo_stock.append(producto)

# print("\nProductos con bajo stock:")
# print(productos_bajo_stock)


# def calcular_promedio_precio(lista):
#     if not lista:
#         return 0
#     total_precio = sum(p['precio'] for p in lista)
#     return total_precio / len(lista)

# precio_promedio = calcular_promedio_precio(productos)
# print(f"\nEl precio promedio de los productos es: ${precio_promedio:.2f}")

import csv

productos_desde_csv = []

with open('datos.csv', mode='r', encoding='utf-8') as archivo_csv:
    lector_diccionario = csv.DictReader(archivo_csv)
    for fila in lector_diccionario:
        fila['id'] = int(fila['id'])
        fila['precio'] = int(fila['precio'])
        fila['stock'] = int(fila['stock'])

        productos_desde_csv.append(fila)


print("\nLista de productos desde el archivo CSV:")
print(productos_desde_csv)

for datos in productos_desde_csv:
    print(f"Producto: {datos['nombre']}, Precio: ${datos['precio']}, Stock: {datos['stock']}")  

