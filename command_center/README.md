# Centro de Comando (legado dev-v4)

## Español

Esta carpeta contiene la configuración del plano de control usada en **dev-v4** para prototipos de panel.
En v5, el control operativo real vive en `control_master/`, por lo que este directorio se conserva como
referencia histórica y para reglas heredadas.

### Contenido
- **master_switch.py**: interruptor global (kill-switch).
- **endpoints.py**: catálogo de endpoints para exponer en el panel de control.
- **rules_config.py**: primitivas de configuración de reglas.
- **settings.py**: objeto de nivel superior que agrega datos configurables.

### Próximos pasos (si se reactiva en el futuro)
- Conectar `CommandCenterSettings` con la capa API para que la UI lea los valores.
- Agregar persistencia (base de datos o archivo) si la configuración debe ser mutable.

---

## English

This folder contains the control-plane configuration used in **dev-v4** for control-panel prototypes.
In v5, the real operational control lives in `control_master/`, so this directory is kept as
historical reference and for inherited rules.

### Contents
- **master_switch.py**: global kill-switch.
- **endpoints.py**: catalog of endpoints to expose in the control panel.
- **rules_config.py**: rule configuration primitives.
- **settings.py**: top-level object aggregating configurable data.

### Next steps (if reactivated in the future)
- Wire `CommandCenterSettings` into the API layer so the UI can read the values.
- Add persistence (database or file-backed) if the settings need to be mutable.
