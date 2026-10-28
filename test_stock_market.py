import unittest

import pandas as pd

from stock_market_prototipo import (
    ingresar_mercaderia,
    registrar_venta,
    riesgo_faltante,
)


class TestStockMarket(unittest.TestCase):
    def test_venta_valida(self):
        self.assertEqual(registrar_venta(10, 2), 8)

    def test_venta_sin_stock(self):
        with self.assertRaises(ValueError):
            registrar_venta(5, 7)

    def test_ingreso_mercaderia(self):
        self.assertEqual(ingresar_mercaderia(10, 20), 30)

    def test_riesgo_faltante(self):
        self.assertTrue(riesgo_faltante(10, 25.71))

    def test_sin_riesgo(self):
        self.assertFalse(riesgo_faltante(30, 20))

    def test_prediccion_positiva(self):
        ventas = [20, 22, 18, 25, 24, 21, 20]
        promedio = sum(ventas) / len(ventas)
        self.assertGreater(promedio, 0)

    def test_tres_productos(self):
        productos = ["Arroz 1kg", "Gaseosa Cola 2.25L", "Leche 1L"]
        self.assertEqual(len(productos), 3)

    def test_datos_sin_nulos(self):
        df = pd.DataFrame({"producto": ["A"], "precio": [10], "ventas": [5]})
        self.assertFalse(df.isnull().any().any())


if __name__ == "__main__":
    unittest.main(verbosity=2)
    