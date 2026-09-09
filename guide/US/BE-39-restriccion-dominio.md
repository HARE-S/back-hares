# Historia de Usuario

## ID
[BE-39]

## Título
Restricción del acceso al dominio corporativo

## Descripción
**Como** responsable pedagógico
**Quiero** que solo puedan entrar cuentas `@grupopenascal.com`

**Para** garantizar que ninguna cuenta personal accede a datos de alumnado menor de edad.

## Criterios de Aceptación

### Escenario 1: Cuenta del dominio corporativo
```gherkin
Dado un ID token válido cuyo claim hd es "grupopenascal.com"
Y cuyo claim email_verified es verdadero
Cuando el sistema valida el dominio
Entonces acepta el acceso
Y continúa con la creación de la sesión
```

### Escenario 2: Cuenta personal de Gmail
```gherkin
Dado un ID token válido emitido para una cuenta @gmail.com
Y que ese token no contiene claim hd
Cuando el sistema valida el dominio
Entonces deniega el acceso con 401 Unauthorized
Y el mensaje indica que la cuenta no está autorizada, no que haya un error del sistema
```

### Escenario 3: Cuenta de otro dominio de Workspace
```gherkin
Dado un ID token válido cuyo claim hd es "otrocentro.com"
Cuando el sistema valida el dominio
Entonces deniega el acceso con 401 Unauthorized
```

### Escenario 4: Flujo iniciado sin el parámetro hd
```gherkin
Dado un atacante que construye la URL de autorización omitiendo el parámetro hd
Y que completa el flujo con una cuenta personal
Cuando el backend valida el ID token recibido
Entonces deniega el acceso igualmente con 401 Unauthorized
```

### Escenario 5: Correo sin verificar
```gherkin
Dado un ID token cuyo claim email_verified es falso
Cuando el sistema valida el dominio
Entonces deniega el acceso con 401 Unauthorized
```

### Escenario 6: Dominio configurable
```gherkin
Dado que la variable de entorno ALLOWED_HD contiene otro valor
Cuando se valida un ID token
Entonces se exige ese dominio y no uno escrito en el código
Y si ALLOWED_HD está vacía la aplicación se niega a arrancar
```

## Notas
* **El fallo clásico que esta historia evita.** El parámetro `hd` que se envía a Google es **solo una sugerencia de interfaz**: filtra el selector de cuentas y nada más. Un atacante puede lanzar el flujo sin él y entrar con su cuenta personal. **La restricción real es comprobar el claim `hd` del ID token en el servidor.** El escenario 4 existe para demostrarlo.
* **Por qué el claim y no el sufijo del correo.** Una cuenta personal de Gmail **no lleva claim `hd` en absoluto**: solo lo emiten las cuentas gestionadas por un dominio de Workspace. Comprobar `hd == grupopenascal.com` rechaza toda cuenta personal sin listas negras ni análisis de cadenas.
* **Confirmado (08/09/2026):** `grupopenascal.com` es Google Workspace. MX en `aspmx.l.google.com`, SPF con `_spf.google.com`.
* **Defensa en profundidad:** la pantalla de consentimiento debe ser **interna** al dominio (BE-46). Si una barrera falla, la otra sigue en pie.
* **Consecuencia operativa:** quien use una cuenta personal para asuntos del centro se quedará fuera. Conviene avisar al cliente antes del despliegue.
* **Testing:** escenarios 2, 3 y 4 son pruebas obligatorias. **No se simula la función de validación**, o se estaría eliminando de las pruebas justo lo que protege el sistema.

## Estimación
5 Puntos de Historia (La comprobación son pocas líneas; el valor está en las pruebas que impiden eliminarla sin enterarse)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE39-01 | **Variable ALLOWED_HD** Lectura del entorno y comprobación al arrancar. | - | Pendiente |
| T-BE39-02 | **Parámetro hd en la autorización** Como filtro del selector, documentando que no es la restricción real. | - | Pendiente |
| T-BE39-03 | **Validación del claim hd** Token sin `hd` o con otro valor → denegado. | - | Pendiente |
| T-BE39-04 | **Comprobación de email_verified** Rechazo si es falso. | - | Pendiente |
| T-BE39-05 | **Mensaje de cuenta no autorizada** Distinguible de un error del sistema. | - | Pendiente |
| T-BE39-06 | **Tests de rechazo de dominio** Escenarios 2 a 5 con tokens firmados en local. | - | Pendiente |
