# order_02

_A vende (restaurante), B es el cliente._

**Variacion / trampas:** Autocorreccion (1->2 pizzas). Con combo familiar el total correcto es 96; el vendedor DICE 106 (olvido la promocion = error del hablante).

**A:** Pizzería y hamburguesería El Sabor, buenas noches. ¿Qué desea ordenar?

**B:** Buenas noches. Quisiera una pizza, dos papas fritas y tres gaseosas. No, perdón, mejor dos pizzas, porque somos seis en la reunión.

**A:** De acuerdo, dos pizzas, dos papas y tres gaseosas. Ese pedido califica para el combo familiar, que tiene diez soles de descuento. ¿Lo aplicamos?

**B:** Sí, claro, aplíquelo, el combo familiar. ¿Hay que hacer algo más?

**B:** Consulta: ¿las papas vienen con salsas?

**A:** Sí, incluyen salsas de la casa, tártara y ají, sin costo adicional.

**B:** Perfecto, muchas gracias, a los chicos les encantan.

**A:** No, ya lo registré. ¿Cuál es la dirección de entrega?

**B:** Calle Las Begonias 1780, en el segundo piso. Es un edificio gris, hay un taller mecánico en la planta baja.

**A:** Le recuerdo que el repartidor no puede subir a pisos altos si no hay portero, por una cuestión de seguridad. ¿Alguien podría bajar a recibir?

**B:** Sí, no hay problema, mi hermana bajará a la puerta cuando él llame por teléfono. Le dejo mi celular para eso.

**A:** Perfecto, lo anotamos junto con la dirección.

**A:** Perfecto. ¿Y el método de pago?

**B:** Voy a pagar con tarjeta. ¿Pasan con el aparato?

**A:** Confirmo entonces: dos pizzas, dos papas y tres gaseosas, con el combo familiar, para la calle Las Begonias, y pago con tarjeta. ¿Todo bien?

**B:** Todo bien, gracias. Es que tenemos invitados y no queremos que falte nada.

**A:** Entendido, le preparamos todo con mucho cuidado.

**A:** Sí, el repartidor lleva el POS. Déjeme hacer el cálculo. El total es ciento seis soles.

**B:** Está bien, gracias. ¿Cuánto tarda?

**A:** Aproximadamente cuarenta minutos, porque hoy hay bastante pedido. Gracias por llamar.

**B:** A usted, buenas noches.


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
  },
  {
   "product": "papas",
   "quantity": 2,
   "unit_price": 9
  },
  {
   "product": "gaseosa",
   "quantity": 3,
   "unit_price": 6
  }
 ],
 "promocion": "combo_familiar",
 "direccion_entrega": "calle las begonias 1780",
 "metodo_pago": "tarjeta",
 "total_dicho": 106
}
```