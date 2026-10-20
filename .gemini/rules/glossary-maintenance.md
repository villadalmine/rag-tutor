# Regla de Mantenimiento de GLOSSARY.md

Siempre que como agente realices alguna de las siguientes acciones en este repositorio:
1. Agregues, elimines o actualices librerías en `requirements.txt` o `pyproject.toml`.
2. Introduzcas un nuevo servicio, base de datos, motor de búsqueda o protocolo de comunicación.
3. Modifiques o agregues un modelo de lenguaje (LLM), modelo de embedding o re-clasificador en `src/config.py` o en Ollama.

**DEBES actualizar inmediatamente el archivo [`GLOSSARY.md`](../../GLOSSARY.md)** asegurando:
- **Analogía cotidiana**: Una comparación accesible del mundo real para personas que no saben de tecnología.
- **Definición técnica precisa**: Qué hace la herramienta a nivel de ingeniería.
- **Enlace oficial**: Link a la web o repositorio oficial.
- **¿Por qué se usa en este proyecto?**: Explicación del beneficio concreto para la soberanía de datos, el rendimiento o la mitigación de alucinaciones.
