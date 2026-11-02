# order_01

_A vende (restaurante), B es el cliente._

**Variacion / trampas:** Autocorreccion de cantidades (2->3 hamburguesas, 1->2 gaseosas). Total CORRECTO (3*18+2*6=66). Direccion con digitos.

**A:** Hamburguesería El Sabor, buenas tardes, ¿en qué puedo ayudarle?

**B:** Buenas tardes. Quisiera hacer un pedido para delivery, por favor.

**A:** Claro que sí, dígame qué desea ordenar.

**B:** Quiero dos hamburguesas y una gaseosa. Ah, espera, mejor tres hamburguesas, que viene mi primo a la casa. Y las gaseosas, que sean dos en vez de una.

**A:** Perfecto. Entonces tres hamburguesas y dos gaseosas. ¿Desea agregar algo más?

**B:** No, así está bien, gracias. Con eso alcanza.

**A:** ¿Tiene alguna duda sobre el pedido o el delivery?

**B:** Una consulta: ¿tienen alguna promoción hoy? Mi primo siempre me pide que pregunte.

**A:** Hoy no tenemos promociones, lamentablemente. Pero el delivery a su zona no tiene costo adicional.

**B:** Ah, qué bien, eso ayuda bastante. Entonces seguimos con el pedido tal como está.

**A:** ¿A qué dirección enviamos el pedido?

**B:** A la avenida Los Olivos 245. Es una casa de dos pisos con portón verde, toque el timbre porque el perro ladra pero no muerde.

**A:** Anotado. ¿Cómo va a pagar, en efectivo o con tarjeta?

**B:** En efectivo. Tengo billetes de cien, ¿tendrá vuelto el repartidor?

**A:** Le confirmo el pedido: tres hamburguesas y dos gaseosas, para entregar en la avenida Los Olivos, y pago en efectivo. ¿Es correcto?

**B:** Sí, correcto. Ojalá llegue caliente, que ya tenemos hambre todos.

**A:** No se preocupe, empacamos todo en bolsas térmicas para que llegue en buen estado.

**A:** Sí, no se preocupe, el repartidor lleva sencillo. Entonces, el total es sesenta y seis soles.

**B:** Perfecto, sesenta y seis. ¿Cuánto demora más o menos?

**A:** Unos treinta minutos. Gracias por su pedido, que lo disfrute.

**B:** Gracias a ustedes, hasta luego.


## Valores correctos
```json
{
 "traps": {
  "autocorreccion": true,
  "total_incorrecto": false,
  "digitos": true
 },
 "items": [
  {
   "product": "hamburguesa",
   "quantity": 3,
   "unit_price": 18
  },
  {
   "product": "gaseosa",
   "quantity": 2,
   "unit_price": 6
  }
 ],
 "promocion": null,
 "direccion_entrega": "avenida los olivos 245",
 "metodo_pago": "efectivo",
 "total_dicho": 66
}
```