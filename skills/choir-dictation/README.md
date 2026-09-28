# choir-dictation

Convierte un arreglo de coro **dictado por voz** al formato de texto de [`choir-score-musescore`](../choir-score-musescore): voces, notas, ritmos, letra y secciones. Claude valida el resultado con el script, te muestra el texto con las dudas y genera la partitura cuando lo apruebas.

## Qué entiende

- Notas en solfeo (*do, re, mi…*) con *sostenido*, *bemol*, *becuadro*; *"do central"*, *"sube a"*, *"baja a"*.
- Ritmos: *redonda, blanca, negra, corchea, semicorchea, con puntillo, silencio de negra, ligada, calderón*.
- Dinámicas: *piano, mezzo forte, forte…*
- Atajos:
  - *"contralto, mismo ritmo que la soprano: re, re, mi…"*
  - *"la contralto hace la soprano una tercera abajo"* (armonía generada, marcada para revisar)
  - *"el tenor descansa en esta parte"*
  - *"igual que el verso"*
- Letra: se dicta una vez para todas las voces; *"se alarga"* → melisma; sinalefas cuando las notas lo piden.
- Se puede dictar por partes (una voz o una sección a la vez); Claude va armando el texto completo.

## Ejemplo

> título santo en sol tres cuartos negra a 72 solemne sección A soprano empieza en re cuatro anacrusa de negra re luego sol la si do blanca si negra…

Ver el resultado en [`ejemplos/coro`](../../ejemplos/coro).

Requiere tener instalada también `choir-score-musescore`.
