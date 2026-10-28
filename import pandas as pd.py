import pandas as pd


def cargar_datos(archivo):
    df = pd.read_csv(archivo)

    # Conversión de fecha
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # Variables numéricas
    columnas_numericas = [
        "precio",
        "stock_inicial",
        "ingreso_mercaderia",
        "unidades_vendidas",
        "stock_final"
    ]

    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def limpiar_datos(df):
    # Imputación por mediana para valores faltantes
    df["unidades_vendidas"] = df.groupby("producto")[
        "unidades_vendidas"
    ].transform(lambda x: x.fillna(x.median()))

    df["precio"] = df.groupby("producto")[
        "precio"
    ].transform(lambda x: x.fillna(x.median()))

    # Control básico de atípicos mediante IQR
    for producto in df["producto"].unique():

        filtro = df["producto"] == producto

        q1 = df.loc[filtro, "unidades_vendidas"].quantile(0.25)
        q3 = df.loc[filtro, "unidades_vendidas"].quantile(0.75)

        iqr = q3 - q1

        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr

        df.loc[filtro, "unidades_vendidas"] = (
            df.loc[filtro, "unidades_vendidas"]
            .clip(limite_inferior, limite_superior)
        )

    return df


def resumen_ventas(df):
    resumen = df.groupby("producto").agg(
        ventas_totales=("unidades_vendidas", "sum"),
        promedio_diario=("unidades_vendidas", "mean"),
        minimo=("unidades_vendidas", "min"),
        maximo=("unidades_vendidas", "max"),
        precio_promedio=("precio", "mean")
    )

    return resumen.round(2)


def predecir_demanda(df, producto):
    datos = df[df["producto"] == producto]

    datos = datos.sort_values("fecha")

    prediccion = datos["unidades_vendidas"].tail(7).mean()

    return round(prediccion, 2)


def riesgo_faltante(stock_actual, demanda_estimada):
    return stock_actual < demanda_estimada


def registrar_venta(stock_actual, cantidad):

    if cantidad > stock_actual:
        raise ValueError("Stock insuficiente")

    return stock_actual - cantidad


def ingresar_mercaderia(stock_actual, cantidad):
    return stock_actual + cantidad


def main():

    archivo = "dataset_stock_market_academico.csv"

    df = cargar_datos(archivo)
    df = limpiar_datos(df)

    print("\n========== 1. RESUMEN DE VENTAS ==========\n")
    print(resumen_ventas(df))

    print("\n========== 2. PREDICCIÓN DE DEMANDA ==========\n")

    for producto in df["producto"].unique():

        demanda = predecir_demanda(df, producto)

        print(
            f"{producto}: {demanda} unidades/día"
        )

    print("\n========== 3. RIESGO DE FALTANTE ==========\n")

    producto = "Leche 1L"
    demanda = predecir_demanda(df, producto)

    stock_actual = 10

    if riesgo_faltante(stock_actual, demanda):
        print(
            f"RIESGO DE FALTANTE para {producto}"
        )
    else:
        print("Sin riesgo")

    print("\n========== 4. VENTA ==========\n")

    stock = registrar_venta(10, 2)
    print(f"Stock final: {stock}")

    print("\n========== 5. VENTA INVÁLIDA ==========\n")

    try:
        registrar_venta(5, 7)
    except ValueError as e:
        print(e)

    print("\n========== 6. INGRESO ==========\n")

    stock = ingresar_mercaderia(10, 20)
    print(f"Stock final: {stock}")


if __name__ == "__main__":
    main()
    