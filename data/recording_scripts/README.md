# Guiones de grabacion (escribir ANTES de grabar)

Escriba aqui sus propios guiones con datos inventados (no use el apendice tal cual).
Variar: posicion de cada dato, forma de decir las cifras ("seis mil quinientos" / "6500" / "seis y medio mil"),
muletillas y correcciones. Cada guion = transcripcion de referencia + valores correctos de los campos.

Formato sugerido por clip (`interview_01.md`, `order_01.md`): texto completo del dialogo y, al final, la fila
que va en `data/ground_truth/interviews.csv` o la entrada de `data/ground_truth/orders.json`:

```json
{"clip": "order_01", "reference_transcript": "...",
 "traps": {"autocorreccion": true, "total_incorrecto": true, "digitos": true},
 "record": {"items": [{"product": "hamburguesa", "quantity": 3, "unit_price": 18}],
            "promocion": null, "direccion_entrega": "avenida lima 1234",
            "metodo_pago": "efectivo", "total_dicho": 100}}
```
Nombre los audios igual que `clip`: `data/audio/interview/interview_01.m4a`, `data/audio/order/order_01.m4a`.
Nota: `total_dicho` es lo que se DICE en voz alta, aunque sea incorrecto (esa es la trampa).
