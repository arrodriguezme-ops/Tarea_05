# order_05

_A vende (restaurante), B es el cliente._

**Variacion / trampas:** Llamada de control: sin trampas salvo digitos. Correcto: 105+18+28=151, menos combo familiar 10 = 141.

**A:** Pizzería y hamburguesería El Sabor, buenas tardes. ¿Qué se le ofrece?

**B:** Buenas tardes. Es para el cumpleaños de mi hija, así que quiero tres pizzas, tres gaseosas y dos ensaladas.

**A:** Qué lindo. Tres pizzas, tres gaseosas y dos ensaladas. Con eso califica para el combo familiar, con diez soles de descuento. ¿Se lo aplico?

**B:** Sí, por favor, aplíquelo. Gracias.

**B:** Consulta: ¿pueden escribir un mensaje en la caja con salsa? Quiero que diga feliz cumpleaños.

**A:** Con gusto, se lo escribimos. ¿Es una fiesta grande?

**B:** Sí, vienen todos sus compañeros del colegio y los abuelos, así que seguro vamos a pedir de nuevo la próxima semana.

**A:** Hecho. ¿A qué dirección enviamos?

**B:** Calle Los Cedros 3306, en la urbanización Las Palmeras. Hay un globo grande en la puerta, no tiene pierde.

**A:** Le confirmo el pedido: tres pizzas, tres gaseosas y dos ensaladas, con el combo familiar. ¿Está bien así?

**B:** Está perfecto. Ah, una cosa, ¿podrían incluir una vela aparte? Es una sorpresa.

**A:** Claro que sí, con gusto. Se la enviamos en una bolsita para que la coloquen ustedes.

**B:** Qué amable, muchas gracias.

**A:** Perfecto. ¿Cómo desea pagar?

**B:** Con Yape, si me permite. Le mando el comprobante apenas me diga cuánto es.

**A:** Claro que sí. Hechas las cuentas, el total es ciento cuarenta y uno soles.

**B:** Perfecto, ciento cuarenta y uno. Lo envío en un momento. ¿A qué hora llegaría?

**A:** Antes de las cinco, calculo. Muchas felicidades a su hija.

**B:** Muchas gracias, hasta luego.


## Valores correctos
```json
{
 "traps": {
  "autocorreccion": false,
  "total_incorrecto": false,
  "digitos": true
 },
 "items": [
  {
   "product": "pizza",
   "quantity": 3,
   "unit_price": 35
  },
  {
   "product": "gaseosa",
   "quantity": 3,
   "unit_price": 6
  },
  {
   "product": "ensalada",
   "quantity": 2,
   "unit_price": 14
  }
 ],
 "promocion": "combo_familiar",
 "direccion_entrega": "calle los cedros 3306",
 "metodo_pago": "yape",
 "total_dicho": 141
}
```