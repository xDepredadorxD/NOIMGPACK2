# Editor de Imágenes en Lote (protege tu privacidad)

Un editor de imágenes en lote con interfaz gráfica desarrollado en Python que permite cargar, editar y guardar múltiples imágenes a una resolución directo al OUTPAINTING.

Guarda tu lote de imagnes sin subirlas a un servidor, protegiendo tu privacidad.

## Características

- Carga múltiple de imágenes
- Visualización en cuadrícula 4x2 con múltiples páginas
- Edición de imágenes:
  - Mover imágenes
  - Redimensionar (escalar)
  - Rotar
  - Deformar (manipulación de puntos de control)
  - Estirar en ejes X e Y
- Marco de selección para recorte
- Resolución de salida personalizable
- Navegación entre páginas
- Deshacer/Rehacer (Ctrl+Z/Ctrl+Y)

## Capturas de pantalla

### Interfaz del editor
![Interfaz principal](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/Captura_de_pantalla_2025-04-07_131955.png)

![Edición de imágenes](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/Captura_de_pantalla_2025-04-07_132425.png)

### Ejemplos de edición

| Mover | Redimensionar |
|-------|---------------|
| ![Mover](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/M.png) | ![Redimensionar](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/W.png) |

| Rotar | Deformar |
|-------|----------|
| ![Rotar](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/R.png) | ![Deformar](https://raw.githubusercontent.com/xDepredadorxD/NOIMGPACK2/refs/heads/main/ejemplos/D.png) |

## Requisitos

- Python 3.6+
- PyQt5
- Pillow (PIL)
- NumPy

## Instalación

1. Clona este repositorio o descarga los archivos
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Ejecuta el programa con:

```bash
python main.py
```

### Controles

- **Cargar Imágenes**: Abre una ventana para seleccionar múltiples imágenes
- **Guardar Imágenes**: Guarda las imágenes editadas con los recortes aplicados en una carpeta a elección.
- **Resolución de salida**: Define el tamaño de las imágenes guardadas
- **Estirar**: Permite estirar la imagen seleccionada en los ejes X e Y

#### Modos de edición

- **Mover**: Click izquierdo y arrastrar para mover la imagen
- **Redimensionar**: Click izquierdo y arrastrar para escalar la imagen
  - Con Shift: Escala uniforme
  - Sin Shift: Escala independiente en X e Y
- **Rotar**: Click derecho y arrastrar para rotar la imagen
- **Deformar**: Click en los puntos de control y arrastrar para deformar la imagen

#### Zoom y navegación

- **Zoom en área de trabajo**: Ctrl + Rueda del ratón
- **Navegación en cada área de trabajo**: barras de desplazamiento
- **Navegación**: Botones "Página Anterior" y "Página Siguiente"

## Estructura del proyecto

- `main.py`: Punto de entrada de la aplicación
- `image_editor.py`: Clase principal para la aplicación
- `image_view.py`: Widget personalizado para visualizar y editar imágenes
- `image_processor.py`: Funciones para procesar imágenes
- `image_deformer.py`: Funciones deformar las imágenes
- `requirements.txt`: Dependencias del proyecto
