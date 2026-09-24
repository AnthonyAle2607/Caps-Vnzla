# Planificación del proyecto CAPS VNZLA

## 1. Objetivo

Diseñar, desarrollar y documentar una tienda de gorras con enfoque premium, estilo urbano y flujo de compra intuitivo.

## 2. Alcance funcional

- catálogo de productos con imágenes,
- filtros por categoría,
- búsqueda por texto,
- selector de moneda USD/BS,
- carrito lateral con conteo y cantidades,
- detalle de producto con información relevante,
- base de datos inicial con catalogación de productos.

## 3. Cronograma sugerido

### Fase 1: Investigación y maquetación
- definir paleta y tipografía,
- estructurar home page y catálogo,
- validar estilo premium blanco + amarillo.

### Fase 2: lógica de negocio
- poblar base de datos con productos iniciales,
- conectar templates y endpoints,
- preparar serialización de productos para frontend.

### Fase 3: interactividad comercial
- completar filtros y búsqueda,
- integrar carrito con almacenamiento local,
- validar conversión de precios y total.

### Fase 4: documentación y refinamiento
- revisar comentarios y docstrings,
- preparar documentación técnica,
- planificar mejoras para checkout y gestión administrativa.

## 4. Riesgos y mitigaciones

### Riesgo: visual poco premium
Mitigación: mantener fondo blanco, cards con bordes suaves y buenas proporciones de imagen.

### Riesgo: moneda inconsistente
Mitigación: centralizar tasa cambiaria en configuración del backend y mostrar siempre valores calculados.

### Riesgo: mantenibilidad baja
Mitigación: documentar funciones, usar modelos claros y separar responsabilidades por módulo.

## 5. Siguientes mejoras recomendadas

- panel administrativo con CRUD de productos,
- manejo de pedidos con validación,
- notificaciones de stock bajo,
- optimización de imágenes y lazy-loading,
- integración con pasarela de pago.

## 6. Criterios de éxito

- interfaz visual clara y premium,
- navegación fluida para el usuario,
- experiencia de compra intuitiva,
- documentación suficiente para continuar el proyecto sin pérdida de contexto.
