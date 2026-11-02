# order_03

_A vende (restaurante), B es el cliente._

**Variacion / trampas:** Sin correccion. Total correcto 41 (18+14+9); el vendedor DICE 47 (error aritmetico del hablante).

**A:** Buenas tardes, El Sabor, le habla Mateo. ¿Cuál es su pedido?

**B:** Hola, buenas tardes. Es para almorzar hoy en la oficina. Quiero una hamburguesa, una ensalada y una porción de papas.

**A:** Muy bien. Una hamburguesa, una ensalada y unas papas. ¿La ensalada la desea con aderezo aparte?

**B:** Sí, por favor, el aderezo aparte. Gracias.

**A:** ¿Prefiere la hamburguesa con todas las cremas o alguna en especial?

**B:** Con mayonesa y ketchup nada más, sin picante, que no me cae bien a esta hora. Y que no la pasen mucho por la plancha, por favor.

**A:** Perfecto, punto medio entonces. ¿Quiere que le agreguemos alguna bebida para acompañar?

**B:** No, gracias, tengo agua en la oficina. Con eso estoy bien, hoy no quiero gastar de más.

**A:** Anotado. ¿Cuál es la dirección?

**B:** Jirón Huallaga 456, oficina cuatro, en el centro. Pregunte en recepción por Marcela.

**A:** Perfecto, jirón Huallaga 456. ¿Cómo va a pagar?

**B:** Con Yape, le envío la captura apenas me confirme el monto.

**A:** Una pregunta, ¿necesita cubiertos descartables o servilletas?

**B:** Sí, por favor, unas servilletas nada más, los cubiertos los tenemos aquí.

**A:** Perfecto, las incluimos. Le repito el pedido: una hamburguesa, una ensalada con aderezo aparte y unas papas. ¿Está bien?

**B:** Sí, está bien, gracias.

**A:** Claro. El total es cuarenta y siete soles.

**B:** Entendido. Le hago el Yape ahora mismo. ¿Está listo en media hora?

**A:** Sí, en unos veinticinco minutos le llega. Gracias por su preferencia.

**B:** Gracias, hasta luego.


## Valores correctos
```json
{
 "traps": {
  "autocorreccion": false,
  "total_incorrecto": true,
  "digitos": true
 },
 "items": [
  {
   "product": "hamburguesa",
   "quantity": 1,
   "unit_price": 18
  },
  {
   "product": "ensalada",
   "quantity": 1,
   "unit_price": 14
  },
  {
   "product": "papas",
   "quantity": 1,
   "unit_price": 9
  }
 ],
 "promocion": null,
 "direccion_entrega": "jirón huallaga 456",
 "metodo_pago": "yape",
 "total_dicho": 47
}
```