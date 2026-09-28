# brass-dictation

Convierte líneas para vientos **dictadas por voz** o **fotografiadas** (nombres de notas escritos a mano o en una app de notas) al formato de [`brass-score-musescore`](../brass-score-musescore). Siempre en sonido real, como en el piano; la transposición la hace el script.

## Qué entiende

- Instrumentos: *trompetas, saxo alto, saxo tenor, saxo barítono, trombón*.
- Notas en solfeo o letras, con alteraciones; octava del primer sonido (*"fa cinco"*), *"sube"*, *"baja"*.
- Ritmos, silencios y *"descansa ocho compases"*.
- Articulaciones: *acento, picado/staccato, legato, calderón*; dinámicas.
- Atajos:
  - *"el alto hace la trompeta una tercera abajo"*
  - *"los saxos igual que las trompetas una octava abajo"*
  - *"mismo ritmo que la trompeta: fa, sol, la…"*
  - *"el trombón descansa en el verso"*
- En las fotos, lo que no se lee bien queda marcado como duda con su ubicación.

## Ejemplo

> título mambo en si bemol cuatro cuartos tempo 110 intro trompetas forte fa cinco corchea picado fa picado silencio de negra re corchea con acento do si bemol negra…

```
[Intro]
TP: f F5:8! F! R:4 D:8> C Bb:4 | C:2 R:2 ||
AS: f D5:8! D! R:4 Bb:8> A G:4 | A:2 R:2 ||
```

Requiere tener instalada también `brass-score-musescore`.
