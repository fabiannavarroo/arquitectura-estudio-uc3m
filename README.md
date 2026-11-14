# Arquitectura de Computadores · Cuaderno de estudio

Web de estudio en español basada en el material de Arquitectura de Computadores de la UC3M.

**[Abrir la web](https://fabiannavarroo.github.io/arquitectura-estudio-uc3m/)**

Incluye 24 lecciones, 16 ejercicios resueltos, 5 simuladores, 96 preguntas, flashcards, búsqueda y formulario imprimible. El progreso se guarda en el navegador.

## Uso y edición

Abre `index.html` o visita GitHub Pages. No necesita instalación ni compilación. El contenido editable está en el objeto JavaScript `DATA` del propio archivo. KaTeX y las tipografías se cargan desde sus CDN.

GitHub Pages publica la raíz de la rama `main`.

## Material docente

Los boletines originales son de David Expósito Singh, Arquitectura de Computadores, Universidad Carlos III de Madrid. Los facsímiles conservan sus créditos y avisos originales. La adaptación incluye notas sobre las erratas y ambigüedades detectadas; no es una web oficial de la universidad.

## Pruebas de regresión

Con Python, `playwright` y Chromium de Playwright instalados:

```sh
python -m unittest discover -s tests -v
```

Para probar el despliegue, define `ARQUI_TEST_URL` con la URL de la web. Las pruebas verifican los controles de caché, FIFO, reinicio de coherencia y renderizado de fórmulas al recalcular.
