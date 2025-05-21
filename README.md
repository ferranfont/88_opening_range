Tras comprobar que la entrada a la rotura del rango y cerrar al final de la sesión tiene tan sólo un 50% de éxito.
Nos proponemos lo contrario, 
validar la hipótesis de que en los primeros momentos de la sesión, va a haber una generación de volatilidad sin tendencia
y por lo tanto compramos la reversión a la media
Le pedimos para entrar a la contra que la vela esté por encima del máximo o mínimo del cuadradito de la apertura.
Le pedimos además que la vela tenga un volumen climático
Tras estos eventos el sistema se activará y entrará tan pronto encuentre una vela de signo contrario al buscadomain

Main, hace la gestión de todos los módulos.
estadisticas.py hace los cálculos estadísticos de los movimientos de los precios.
chart_volume.py  grafica las entradas.
fin high volume candles es un script auxiliar, no se usa en este código.
summary.py analiza el fichero creado por estadisticas  summary_stats y saca ratios 