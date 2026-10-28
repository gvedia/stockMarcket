import pandas as pd

def cargar_datos(archivo):
    df = pd.read_csv(archivo)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    columnas_numericas = [
        "precio",
        "stock_inicial",
        "ingreso_mercaderia",
        "unidades_vendidas",
        "stock_final",
    ]
    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    return df


def limpiar_datos(df):
    df["unidades_vendidas"] = df.groupby("producto")[
        "unidades_vendidas"
    ].transform(lambda valores: valores.fillna(valores.median()))
    df["precio"] = df.groupby("producto")["precio"].transform(
        lambda valores: valores.fillna(valores.median())
    )

    for producto in df["producto"].unique():
        filtro = df["producto"] == producto
        ventas = df.loc[filtro, "unidades_vendidas"]
        primer_cuartil = ventas.quantile(0.25)
        tercer_cuartil = ventas.quantile(0.75)
        rango_intercuartil = tercer_cuartil - primer_cuartil
        limite_inferior = primer_cuartil - 1.5 * rango_intercuartil
        limite_superior = tercer_cuartil + 1.5 * rango_intercuartil
        df.loc[filtro, "unidades_vendidas"] = ventas.clip(
            limite_inferior, limite_superior
        )

    return df


def resumen_ventas(df):
    resumen = df.groupby("producto").agg(
        ventas_totales=("unidades_vendidas", "sum"),
        promedio_diario=("unidades_vendidas", "mean"),
        minimo=("unidades_vendidas", "min"),
        maximo=("unidades_vendidas", "max"),
        precio_promedio=("precio", "mean"),
    )
    return resumen.round(2)


def predecir_demanda(df, producto):
    datos_producto = df[df["producto"] == producto].sort_values("fecha")
    prediccion = datos_producto["unidades_vendidas"].tail(7).mean()
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
    df = limpiar_datos(cargar_datos(archivo))

    print("\n========== 1. RESUMEN DE VENTAS ==========\n")
    print(resumen_ventas(df))

    print("\n========== 2. PREDICCIÓN DE DEMANDA ==========\n")
    for producto in df["producto"].unique():
        demanda = predecir_demanda(df, producto)
        print(f"{producto}: {demanda} unidades/día")

    print("\n========== 3. RIESGO DE FALTANTE ==========\n")
    producto = "Leche 1L"
    demanda = predecir_demanda(df, producto)
    if riesgo_faltante(10, demanda):
        print(f"RIESGO DE FALTANTE para {producto}")
    else:
        print("Sin riesgo")

    print("\n========== 4. VENTA ==========\n")
    print(f"Stock final: {registrar_venta(10, 2)}")

    print("\n========== 5. VENTA INVÁLIDA ==========\n")
    try:
        registrar_venta(5, 7)
    except ValueError as error:
        print(error)

    print("\n========== 6. INGRESO ==========\n")
    print(f"Stock final: {ingresar_mercaderia(10, 20)}")


if __name__ == "__main__":
    main()
