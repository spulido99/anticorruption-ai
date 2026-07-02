# core.contratos unificada con fuente escalar; duplicados cross-fuente marcados, no fusionados

`core.contratos` es **una sola tabla** para SECOP I y II con columna **`fuente` escalar**: una fila = un registro de una fuente, siempre trazable a su dataset de origen. Está verificado que un mismo contrato puede aparecer en ambas plataformas (entidades migradas, cargas retroactivas), pero **no se fusionan filas**: no existe llave dura entre SECOP I y II (el puente vía SECOP Integrado es indirecto y parcialmente confiable), y la fusión rompería la trazabilidad fila→expediente.

Cuando se ingiera SECOP I, un paso explícito y auditable de deduplicación usará el puente del Integrado para marcar la fila de SECOP I con `duplicado_de` → el `id_contrato` canónico de SECOP II (gana SECOP II por ser plataforma transaccional; SECOP I es digitación manual). Los análisis agregados consumen la vista `core.contratos_unicos` (`WHERE duplicado_de IS NULL`) para no contar doble. `core.procesos` es solo SECOP II — SECOP I no tiene equivalente estructurado; el cruce contrato↔proceso vía `notice_uid` materializado aplica solo a filas `fuente = 'SECOP_II'`.

## Considered Options

- **Fila única multi-fuente** (`fuente` como STRUCT o columnas booleanas por fuente): expresa lo mismo, pero exige resolver el match cross-fuente al ingerir y pierde los campos exclusivos de cada fuente y la trazabilidad por registro. Se descartó a favor del marcado explícito.
