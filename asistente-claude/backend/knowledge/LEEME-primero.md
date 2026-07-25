# Base de conocimiento del asistente

Todo lo que pongas en esta carpeta como archivo **`.txt`** o **`.md`** se convierte
en el "conocimiento" del asistente. Cuando alguien pregunta algo, el servidor busca
los fragmentos más relevantes y el asistente responde **basándose en ellos** (y avisa
si la respuesta no está).

## Cómo añadir el contenido de GNP

1. Reúne los documentos **oficiales que tengas autorización de usar**: folletos de
   producto, guías de proceso, preguntas frecuentes, condiciones, manuales, etc.
2. Conviértelos a texto:
   - Si es un **PDF o Word**: ábrelo y usa *Archivo → Guardar como / Exportar → Texto sin formato (.txt)*,
     o copia el texto y pégalo en un archivo `.txt`.
   - Si es una **página web** que puedes usar: selecciona el texto, cópialo y pégalo en un `.txt`.
3. Guarda cada documento aquí, con un nombre claro. Ejemplos:
   `auto-coberturas.txt`, `gastos-medicos-proceso-siniestro.txt`, `vida-preguntas-frecuentes.md`.
4. **Reinicia el servidor** (Ctrl+C y `node server.mjs`). Al arrancar dirá cuántos
   documentos y fragmentos cargó.

## Recomendaciones

- **Un tema por archivo** y párrafos cortos: así el asistente encuentra mejor la respuesta.
- Pon la información **actualizada**; si algo cambia, actualiza el archivo y reinicia.
- Los archivos que empiezan por `LEEME` (como este) se ignoran a propósito.

## Importante (legal)

Usa solo documentos que tengas **permiso** de utilizar. Lo ideal para producción es
que **GNP entregue su contenido oficial** — es más completo, correcto y actualizado
que cualquier cosa tomada de la web pública, y evita problemas de derechos.

Los archivos `ejemplo-*.md` de esta carpeta son **contenido genérico de demostración**
(conceptos generales de seguros, no datos específicos de GNP). Reemplázalos por el
material oficial.
