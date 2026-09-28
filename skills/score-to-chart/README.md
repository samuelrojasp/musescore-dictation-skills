# score-to-chart

Convierte una **partitura completa** (piano/voz/guitarra, lead sheet, partitura orquestal) en un **cifrado compacto con barras rítmicas** para la banda. Acepta un PDF escaneado o fotos de las páginas. El resultado se genera con [`slash-chart-musescore`](../slash-chart-musescore), así que necesitas tener ambas skills instaladas.

## Cómo trabaja

1. Convierte cada página en imagen y lee los acordes escritos sobre el pentagrama, compás por compás.
2. Ubica cada acorde en su tiempo según su posición dentro del compás. Los acordes anticipados (escritos en la última corchea y ligados al compás siguiente) pasan al primer tiempo del compás siguiente.
3. Usa los números de compás impresos para verificar que no se salte ni duplique ninguno.
4. Detecta las secciones por la letra y la textura (intro, verso, coro, solo, tag, final) y compacta los bloques que se repiten con signos de repetición.
5. Comprueba que los compases tocados del cifrado (contando repeticiones) sumen lo mismo que el original, genera el `.mscz` y te muestra la estructura encontrada y las dudas.

Si la partitura no trae acordes escritos, los deduce del bajo y el acompañamiento, y lo indica claramente porque es un análisis, no una lectura.

## Ejemplo

Una partitura de piano/voz/guitarra de 10 páginas (120 compases) queda en un cifrado de 70 compases escritos:

```
[Intro]
|: Gm7/D | Dadd9 :|
[Verso]
|: Gm7/D | Dadd9 | Gm7/D | Dadd9 |
| Bb | C | Am7 | Dm :|
[Coro]
|: Gm7 | C | Gm7 | C |
| Bb | C | Bb . C . | Dm :|
…
```

## Uso

> *"Te mando el PDF de la partitura, conviértela en cifrado para la banda"*
