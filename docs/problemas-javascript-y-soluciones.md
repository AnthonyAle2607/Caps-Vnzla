# Problemas de JavaScript y soluciones

## Objetivo

Este documento describe los problemas encontrados en la interacción entre el JavaScript del catálogo, las plantillas Jinja2 y los datos enviados por Flask. No se modifica el código de la aplicación; se explica qué ocurre, por qué ocurre y qué debe cambiarse manualmente.

## 1. Datos inválidos en `window.catalogData`

### Síntoma

El catálogo puede aparecer vacío y la búsqueda, los filtros, el cambio de moneda y el carrito pueden dejar de funcionar.

### Causa

En la plantilla de inicio, el bloque actual aparece con esta estructura:

```html
window.catalogData = { products_json | safe  };
window.currencyRate = { currency_rate };
```

Las llaves no están formando una expresión Jinja válida. Después de renderizar la plantilla, el navegador puede recibir una expresión JavaScript inválida, por ejemplo:

```javascript
window.catalogData = { [{"id": 1}] };
window.currencyRate = { 35 };
```

En ese caso se produce un `SyntaxError` y el navegador deja de ejecutar el script inline. Como consecuencia, `window.catalogData` no se prepara correctamente antes de cargar `catalog.js`.

### Solución

Usar la sintaxis Jinja con dobles llaves para imprimir el valor:

```html
<script>
  window.catalogData = {{ products_json | safe }};
  window.currencyRate = {{ currency_rate }};
</script>
```

Después de guardar, abrir las herramientas del navegador con `F12`, entrar en **Console** y confirmar que no aparece `SyntaxError`.

## 2. Doble conversión de precios a BS

### Síntoma

Los precios mostrados en bolívares son mucho más altos de lo esperado, especialmente en las tarjetas de productos y en el carrito.

### Causa

El código convierte primero el precio con `convertPrice()` y luego vuelve a multiplicarlo dentro de `formatMoney()` cuando la moneda activa es `BS`.

Ejemplo del flujo actual:

```javascript
formatMoney(convertPrice(product.precio_usd));
```

`convertPrice()` ya multiplica por la tasa. Luego `formatMoney()` vuelve a multiplicar porque recibe la moneda BS mediante el estado global. Esto produce una conversión equivalente a:

$$precio\_usd \times tasa \times tasa$$

### Solución

Elegir una sola responsabilidad:

- O se pasa siempre el valor base en USD a `formatMoney()` y `formatMoney()` realiza la conversión.
- O `convertPrice()` realiza la conversión y `formatMoney()` recibe un valor ya convertido sin volver a multiplicarlo.

La primera opción es más sencilla y consistente. Las llamadas de tarjetas, artículos del carrito y subtotal deben enviar el precio base en USD a una única función de formateo.

### Verificación

Con una tasa de `35` y un producto de `$10`, el resultado correcto es `Bs 350`, nunca `Bs 12.250`.

## 3. Carrusel JavaScript no conectado al HTML actual

### Síntoma

El catálogo se renderiza, pero los controles del carrusel o el desplazamiento automático no tienen efecto.

### Causa

`catalog.js` busca estos elementos:

- `[data-carousel]`
- `.product-carousel__viewport`
- `[data-carousel-prev]`
- `[data-carousel-next]`

La plantilla actual renderiza un contenedor con `id="product-grid"` y clase `product-grid`, pero no contiene los atributos ni las clases que espera el carrusel.

La función `configureCarousel()` sale temprano cuando no encuentra el carrusel, así que no siempre se produce un error visible; simplemente la funcionalidad queda desconectada.

### Solución

Hay dos alternativas válidas:

1. Si se desea un carrusel, adaptar el HTML para incluir el contenedor, la vista desplazable, los botones y los atributos `data-*` que espera JavaScript.
2. Si se desea una cuadrícula normal, retirar del flujo las funciones de carrusel, el temporizador y las llamadas a `configureCarousel()` y `restartCarouselTimer()`.

No se debe mezclar una estructura de cuadrícula con lógica que espera una estructura de carrusel.

## 4. Riesgo al insertar datos con `innerHTML`

### Síntoma

Un nombre o descripción que contenga HTML puede alterar la interfaz. Si los datos proceden de una fuente no confiable, también puede ejecutarse contenido malicioso en el navegador.

### Causa

Las propiedades del producto se interpolan directamente dentro de plantillas asignadas a `innerHTML`:

```javascript
container.innerHTML = products.map((product) => `...`).join("");
```

Esto afecta especialmente a `nombre`, `descripcion` y `categoria`.

### Solución

Crear los nodos con `document.createElement()` y asignar el texto mediante `textContent`. Si se mantiene `innerHTML`, los valores dinámicos deben escaparse antes de insertarse. La solución preferida para datos provenientes de usuarios o administradores es no construir HTML con interpolación directa.

## 5. Errores posibles al guardar el carrito

### Síntoma

El carrito funciona durante la sesión, pero puede fallar al guardar en algunos navegadores, en modo privado o cuando el almacenamiento está lleno.

### Causa

`loadCart()` maneja excepciones, pero `saveCart()` llama directamente a `localStorage.setItem()` sin `try/catch`. Una excepción de almacenamiento puede interrumpir la ejecución de la acción de agregar o modificar un producto.

### Solución

Proteger `localStorage.setItem()` con `try/catch`, informar al usuario cuando no sea posible persistir el carrito y mantener el carrito en memoria como respaldo. También se debe validar que los datos recuperados sean un arreglo y que sus cantidades sean números positivos.

## 6. Validación insuficiente de datos recuperados

### Síntoma

Una entrada dañada en `localStorage` puede producir cantidades incorrectas, `NaN` o errores durante el cálculo del subtotal.

### Causa

El JSON se analiza, pero no se comprueba su forma. El código supone que cada elemento tiene `id`, `price_usd` y `quantity` con tipos válidos.

### Solución

Después de `JSON.parse()`, verificar que el resultado sea un arreglo. Para cada artículo, comprobar que el identificador sea válido, que el precio sea numérico y que la cantidad sea un entero mayor que cero. Descartar las entradas que no cumplan esas reglas.

## 7. El stock no limita la cantidad del carrito

### Síntoma

El usuario puede pulsar **Añadir** o `+` más veces que las unidades disponibles.

### Causa

`addToCart()` y `adjustCartItem()` incrementan la cantidad sin consultar `product.stock`.

### Solución

Buscar el producto original antes de incrementar y comparar la nueva cantidad con su stock. Si se alcanza el límite, desactivar el incremento y mostrar un mensaje claro. Esta validación también debe repetirse en el servidor antes de procesar un pedido, porque JavaScript puede modificarse o desactivarse.

## Orden recomendado para solventar los problemas

1. Corregir la impresión de `catalogData` y `currencyRate` en la plantilla.
2. Recargar la página y eliminar errores de la consola del navegador.
3. Corregir la doble conversión de precios y comprobar USD y BS con una tasa conocida.
4. Decidir si el catálogo será cuadrícula o carrusel y alinear HTML con JavaScript.
5. Fortalecer la lectura y escritura de `localStorage`.
6. Reemplazar la interpolación insegura de datos por creación segura de nodos.
7. Añadir la validación de stock en frontend y servidor.

## Cómo diagnosticarlo en el navegador

1. Abrir la aplicación y pulsar `F12`.
2. En **Console**, buscar `SyntaxError`, `TypeError` o errores de `localStorage`.
3. En **Console**, ejecutar:

```javascript
Array.isArray(window.catalogData)
window.currencyRate
```

El primer resultado debe ser `true` y el segundo debe ser un número positivo.

4. En **Application > Local Storage**, revisar la clave `caps_vnzla_cart`.
5. En **Network**, recargar y comprobar que `catalog.js` responde con estado `200`.
6. Probar una búsqueda, un filtro, el cambio a BS, agregar un producto y modificar su cantidad.

## Resultado esperado

Una vez aplicadas estas soluciones, el catálogo debe:

- cargar los productos sin errores de sintaxis;
- filtrar y buscar sin detener el script;
- mostrar precios correctos en USD y BS;
- mantener el carrito sin romperse cuando el almacenamiento no está disponible;
- respetar el stock disponible;
- renderizar datos del catálogo sin permitir inyección de HTML;
- usar una estructura de carrusel coherente o funcionar como cuadrícula, según la decisión de diseño.
