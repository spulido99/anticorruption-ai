# CONTEXT — anticorruption-ai

Agentes, skills y procesos de IA para que múltiples stakeholders analicen la contratación pública colombiana y detecten corrupción e ineficiencias. Inspirado en la tesis de *Why Nations Fail*: las instituciones inclusivas requieren que muchos ojos puedan vigilar el poder.

El mapa del proyecto vive en el issue [Mapa: IA anticorrupción para contratación pública en Colombia](https://github.com/spulido99/anticorruption-ai/issues/1).

## Glosario

- **Entidad (compradora)**: organismo público (municipal, departamental o nacional) que contrata. Identificada por NIT.
- **Contratista**: persona natural o jurídica que recibe un contrato. Su identidad es la pareja tipo de documento + número normalizado (cédulas, NITs y documentos extranjeros son espacios distintos). *Evitar*: "proveedor" (es el nombre del campo en SECOP II, no el término del dominio).
- **Contratista no resuelto**: contrato cuyo documento de contratista es un placeholder (`'No Definido'`, `0`, vacío). Se cuenta, no se descarta: la opacidad es en sí una señal.
- **Proceso**: el proceso de contratación (licitación, contratación directa, etc.) que puede resultar en uno o más contratos.
- **Contrato**: el acuerdo adjudicado — la unidad central de análisis.
- **Red flag**: indicador computable sobre los datos de contratación que señala riesgo de corrupción o ineficiencia. Un red flag NO es prueba de corrupción; es una señal que requiere verificación humana.
- **Hallazgo**: resultado de análisis verificado por un humano, con metodología reproducible y trazabilidad a la fuente, listo para publicarse o accionarse. El norte de la v1 es producir uno real.
- **Aliado**: el periodista de datos u ONG de transparencia que usa la v1 para perseguir el primer hallazgo.
- **Stakeholder**: cualquier tipo de usuario de la visión completa — prensa, ONGs, gobierno, oposición, ciudadanía. La v1 optimiza solo para el aliado.
- **Ámbito piloto**: el departamento/municipio/sector donde se enfoca el primer análisis. Por definir con datos en la mano (issue #7).

## Decisiones vigentes

Las decisiones de arquitectura se registran como ADRs en [`docs/adr/`](docs/adr/). Las decisiones de producto viven en el mapa (issue #1, "Decisions so far").
