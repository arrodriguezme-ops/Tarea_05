# order_04

_A vende (restaurante), B es el cliente._

**Variacion / trampas:** Cancelacion (quita la ensalada) + descuento de diez por ciento. Correcto: 70 - 10% = 63; el vendedor DICE 73. Ojo: 'setenta y tres' vs 'sesenta y tres' difiere en una palabra, la regla de diagnostico dira error_asr aunque fue error del hablante (limitacion a reportar).

**A:** Buenas noches, El Sabor, ¿en qué le ayudo?

**B:** Buenas noches. Quiero dos pizzas y una ensalada, por favor.

**A:** Claro. Dos pizzas y una ensalada. ¿Algo más?

**B:** Mmm, no, mejor quita la ensalada, que ya no la voy a necesitar. Solo las dos pizzas.

**A:** Listo, solo dos pizzas. Le comento que hoy tenemos un descuento de diez por ciento en pedidos de pizza.

**B:** Ah, qué bien, me lo aplica, entonces.

**B:** Pregunta: ¿las pizzas vienen con el borde relleno o eso se cobra aparte?

**A:** El borde relleno de queso es opcional, pero hoy se lo regalamos por ser cliente frecuente.

**B:** Qué amable, entonces sí, con borde relleno, por favor. Mi familia lo adora.

**A:** Por supuesto. ¿Dirección de entrega?

**B:** Avenida Arequipa 1204, cerca del parque, la puerta es azul.

**A:** Anotado. ¿Va a pagar en efectivo, con tarjeta o con Yape?

**B:** En efectivo, tengo justo billetes de cincuenta.

**A:** Le repito el pedido para confirmar: dos pizzas, con el descuento aplicado. ¿Correcto?

**B:** Correcto. Y por favor, que las corten en ocho pedazos, que mis sobrinos son muy exigentes.

**A:** Descuide, vienen cortadas de la forma tradicional, en ocho porciones cada una.

**B:** Perfecto, entonces.

**A:** Perfecto. Entonces el total es setenta y tres soles.

**B:** Está bien, gracias. ¿Cuánto tiempo?

**A:** Cerca de treinta y cinco minutos. Que tenga buena noche.

**B:** Igualmente, adiós.


## Valores correctos
```json
{
 "traps": {
  "autocorreccion": true,
  "total_incorrecto": true,
  "digitos": true
 },
 "items": [
  {
   "product": "pizza",
   "quantity": 2,
   "unit_price": 35
  }
 ],
 "promocion": "descuento_10",
 "direccion_entrega": "avenida arequipa 1204",
 "metodo_pago": "efectivo",
 "total_dicho": 73
}
```