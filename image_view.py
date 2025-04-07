#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPen, QColor, QPixmap, QTransform, QCursor, QPainter, QImage, QBrush
from PIL import Image
from image_processor import ImageProcessor
from image_deformer import ImageDeformer
import math
import numpy as np

class ImageView(QGraphicsView):
    """Widget personalizado para visualizar y editar imágenes."""

    # Señales
    imageModified = pyqtSignal()  # Emitida cuando la imagen es modificada

    # Estados de edición
    MODE_VIEW = 0
    MODE_MOVE = 1
    MODE_RESIZE = 2
    MODE_ROTATE = 3
    MODE_DEFORM = 4

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configuración de la vista
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)  # Modo de arrastre predeterminado
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # Configurar barras de desplazamiento para navegación
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setViewportMargins(0, 0, 0, 0)  # Eliminar márgenes para maximizar el área visible
        self.setBackgroundBrush(QColor(30, 30, 30))

        # Variables para el desplazamiento con el botón central del ratón
        self.middle_button_pressed = False
        self.last_pan_point = QPointF()

        # Escena
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Elementos gráficos
        self.pixmap_item = None
        self.selection_rect = None

        # Estado
        self.mode = self.MODE_VIEW
        self.original_image = None
        self.current_image = None
        self.last_mouse_pos = QPointF()
        self.is_dragging = False
        self.rotation_angle = 0
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.significant_change = False  # Indica si ha habido un cambio significativo que requiere guardar estado

        # Inicializar el deformador de imágenes
        self.deformer = ImageDeformer()

        # Puntos de control para deformación
        self.control_points = []
        self.active_control_point = None
        self.original_control_positions = {}
        self.current_control_positions = {}

        # Tamaño objetivo para recorte
        self.target_size = (1024, 1024)

    def set_image(self, image_path):
        """Establece una nueva imagen para editar."""
        try:
            # Cargar imagen con PIL
            pil_image = Image.open(image_path)

            # Convertir a formato PNG con transparencia
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Guardar copias de la imagen original y actual
            self.original_image = pil_image.copy()
            self.current_image = pil_image.copy()

            # Imprimir información sobre la imagen
            print(f"Imagen cargada: {image_path}")
            print(f"Dimensiones: {pil_image.width}x{pil_image.height}")
            print(f"Modo: {pil_image.mode}")

            # Convertir a QPixmap
            pixmap = ImageProcessor.pil_to_pixmap(pil_image)

            # Limpiar escena
            self.scene.clear()

            # Crear nuevo item de pixmap
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            self.scene.addItem(self.pixmap_item)
            self.pixmap_item.setZValue(1)  # Valor Z intermedio para que esté entre el marco y los puntos de control

            # Establecer un tamaño de escena más grande para permitir desplazamiento
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            # Hacer la escena 3 veces más grande que la imagen para permitir desplazamiento
            scene_rect = QRectF(-pixmap_width, -pixmap_height, pixmap_width * 3, pixmap_height * 3)
            self.scene.setSceneRect(scene_rect)

            # Crear rectángulo de selección
            self.create_selection_rect()

            # Ajustar vista
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

            # Reiniciar estado
            self.rotation_angle = 0
            self.scale_factor_x = 1.0
            self.scale_factor_y = 1.0

            # Inicializar el deformador con la imagen actual
            self.deformer.load_pil_image(self.current_image)

            # Crear puntos de control para deformación
            self.create_control_points()

            # Emitir señal de modificación para guardar el estado inicial
            self.imageModified.emit()

        except Exception as e:
            print(f"Error al cargar la imagen: {e}")

    def create_selection_rect(self):
        """Crea el rectángulo de selección basado en el tamaño objetivo."""
        if not self.pixmap_item:
            return

        # Obtener dimensiones de la imagen
        pixmap_width = self.pixmap_item.pixmap().width()
        pixmap_height = self.pixmap_item.pixmap().height()

        # Calcular tamaño del rectángulo de selección manteniendo la relación de aspecto del tamaño objetivo
        target_aspect = self.target_size[0] / self.target_size[1]

        if pixmap_width / pixmap_height > target_aspect:
            # La imagen es más ancha que el aspecto objetivo
            selection_height = pixmap_height
            selection_width = selection_height * target_aspect
        else:
            # La imagen es más alta que el aspecto objetivo
            selection_width = pixmap_width
            selection_height = selection_width / target_aspect

        # Centrar el rectángulo
        x = (pixmap_width - selection_width) / 2
        y = (pixmap_height - selection_height) / 2

        # Crear el rectángulo de selección
        self.selection_rect = QGraphicsRectItem(x, y, selection_width, selection_height)
        self.selection_rect.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))

        # Añadir el rectángulo de selección a la escena con un valor Z bajo para que esté debajo de la imagen
        self.scene.addItem(self.selection_rect)
        self.selection_rect.setZValue(-1)  # Valor Z negativo para que esté debajo de la imagen

    def create_control_points(self):
        """Crea puntos de control para la deformación de la imagen."""
        if not self.pixmap_item:
            return

        # Limpiar puntos existentes
        for point in self.control_points:
            self.scene.removeItem(point)
        self.control_points = []
        self.original_control_positions = {}
        self.current_control_positions = {}

        # Obtener dimensiones de la imagen
        rect = self.pixmap_item.boundingRect()

        # Obtener los puntos del deformador
        deformer_points = self.deformer.get_points()

        # Si no hay puntos en el deformador, usar las esquinas de la imagen
        if deformer_points is None:
            points = [
                (rect.topLeft(), "topleft"),
                (rect.topRight(), "topright"),
                (rect.bottomRight(), "bottomright"),
                (rect.bottomLeft(), "bottomleft")
            ]
        else:
            # Convertir los puntos del deformador a coordenadas de la imagen
            img_width = rect.width()
            img_height = rect.height()
            points = [
                (QPointF(deformer_points[0][0] / img_width * rect.width(),
                        deformer_points[0][1] / img_height * rect.height()), "topleft"),
                (QPointF(deformer_points[1][0] / img_width * rect.width(),
                        deformer_points[1][1] / img_height * rect.height()), "topright"),
                (QPointF(deformer_points[2][0] / img_width * rect.width(),
                        deformer_points[2][1] / img_height * rect.height()), "bottomright"),
                (QPointF(deformer_points[3][0] / img_width * rect.width(),
                        deformer_points[3][1] / img_height * rect.height()), "bottomleft")
            ]

        for pos, name in points:
            # Convertir a coordenadas de escena
            scene_pos = self.pixmap_item.mapToScene(pos)

            # Crear punto de control (más grande para facilitar la selección)
            point_size = 25  # Tamaño del punto de control (aumentado)
            point = QGraphicsRectItem(scene_pos.x() - point_size/2, scene_pos.y() - point_size/2, point_size, point_size)
            point.setPen(QPen(QColor(0, 255, 255), 4))  # Borde más grueso
            point.setBrush(QBrush(QColor(0, 255, 255, 100)))  # Color de relleno semitransparente
            point.setData(0, name)
            point.setData(1, pos)  # Guardar la posición relativa en el pixmap
            self.scene.addItem(point)
            point.setZValue(2)  # Valor Z positivo para que esté encima de la imagen
            self.control_points.append(point)

            # Guardar posición original y actual
            self.original_control_positions[name] = (scene_pos.x(), scene_pos.y())
            self.current_control_positions[name] = (scene_pos.x(), scene_pos.y())

    def set_target_size(self, width, height):
        """Establece el tamaño objetivo para el recorte."""
        self.target_size = (width, height)
        if self.pixmap_item:
            self.create_selection_rect()

    def clear_control_points(self):
        """Limpia todos los puntos de control."""
        # Limpiar puntos de control
        for point in self.control_points:
            self.scene.removeItem(point)
        self.control_points = []

    def set_mode(self, mode):
        """Establece el modo de edición."""
        self.mode = mode

        # Actualizar cursor según el modo
        if mode == self.MODE_MOVE:
            self.setCursor(Qt.OpenHandCursor)
        elif mode == self.MODE_RESIZE:
            self.setCursor(Qt.SizeAllCursor)
        elif mode == self.MODE_ROTATE:
            self.setCursor(Qt.CrossCursor)
        elif mode == self.MODE_DEFORM:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Maneja el evento de presionar el botón del ratón."""
        if not self.pixmap_item:
            return super().mousePressEvent(event)

        self.last_mouse_pos = self.mapToScene(event.pos())
        self.is_dragging = True

        if event.button() == Qt.LeftButton:
            if self.mode == self.MODE_MOVE:
                self.setCursor(Qt.ClosedHandCursor)
            elif self.mode == self.MODE_DEFORM:
                # Comprobar si se ha hecho clic en un punto de control
                for point in self.control_points:
                    if point.contains(self.last_mouse_pos):
                        self.active_control_point = point
                        break
        elif event.button() == Qt.MiddleButton:
            # Activar el modo de desplazamiento con el botón central
            self.middle_button_pressed = True
            self.last_pan_point = event.pos()  # Guardar la posición inicial para el desplazamiento
            self.viewport().setCursor(Qt.ClosedHandCursor)  # Cambiar el cursor a mano cerrada
            # Usar el modo de arrastre nativo para un desplazamiento más suave
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Capturar el ratón para asegurar que recibimos todos los eventos de movimiento
            self.viewport().grabMouse()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Maneja el evento de mover el ratón."""
        # Manejar el desplazamiento con el botón central
        if self.middle_button_pressed and event.buttons() & Qt.MiddleButton:
            # El modo ScrollHandDrag se encarga del desplazamiento automáticamente
            # Solo actualizamos la posición para cálculos futuros
            self.last_pan_point = event.pos()
            return  # No procesar más eventos

        if not self.pixmap_item or not self.is_dragging:
            return super().mouseMoveEvent(event)

        current_pos = self.mapToScene(event.pos())
        delta = current_pos - self.last_mouse_pos

        if self.mode == self.MODE_MOVE and event.buttons() & Qt.LeftButton:
            # Mover la imagen
            self.pixmap_item.moveBy(delta.x(), delta.y())

        elif self.mode == self.MODE_RESIZE and event.buttons() & Qt.LeftButton:
            # Escalar la imagen alrededor de su centro
            center = self.pixmap_item.boundingRect().center()

            if event.modifiers() & Qt.ShiftModifier:
                # Escalar uniformemente
                scale_factor = 1.0 + delta.x() / 100.0
                self.scale_factor_x *= scale_factor
                self.scale_factor_y *= scale_factor
            else:
                # Escalar en X e Y independientemente
                self.scale_factor_x *= (1.0 + delta.x() / 100.0)
                self.scale_factor_y *= (1.0 + delta.y() / 100.0)

            # Aplicar transformación alrededor del centro
            transform = QTransform()
            # Mover al origen, escalar y rotar, luego volver a la posición original
            transform.translate(center.x(), center.y())
            transform.rotate(self.rotation_angle)
            transform.scale(self.scale_factor_x, self.scale_factor_y)
            transform.translate(-center.x(), -center.y())

            self.pixmap_item.setTransform(transform)

            # Actualizar la posición de los puntos de control
            self.update_control_points_position()

        elif self.mode == self.MODE_ROTATE and event.buttons() & Qt.RightButton:
            # Rotar la imagen alrededor de su centro
            center = self.pixmap_item.boundingRect().center()
            center_scene = self.pixmap_item.mapToScene(center)

            # Calcular ángulos desde el centro a las posiciones del ratón
            angle1 = math.degrees(math.atan2(self.last_mouse_pos.y() - center_scene.y(),
                                            self.last_mouse_pos.x() - center_scene.x()))
            angle2 = math.degrees(math.atan2(current_pos.y() - center_scene.y(),
                                            current_pos.x() - center_scene.x()))
            angle_delta = angle2 - angle1

            # Actualizar ángulo de rotación
            self.rotation_angle += angle_delta

            # Aplicar transformación alrededor del centro
            transform = QTransform()
            # Mover al origen, rotar y escalar, luego volver a la posición original
            transform.translate(center.x(), center.y())
            transform.rotate(self.rotation_angle)
            transform.scale(self.scale_factor_x, self.scale_factor_y)
            transform.translate(-center.x(), -center.y())

            self.pixmap_item.setTransform(transform)

            # Actualizar la posición de los puntos de control
            self.update_control_points_position()

        elif self.mode == self.MODE_DEFORM and self.active_control_point:
            # Mover el punto de control
            point_size = 25  # Tamaño del punto de control (aumentado)
            self.active_control_point.setPos(current_pos - QPointF(point_size/2, point_size/2))  # Ajustar por el tamaño del punto

            # Actualizar la posición actual del punto de control
            name = self.active_control_point.data(0)
            self.current_control_positions[name] = (current_pos.x(), current_pos.y())

            # Aplicar deformación en tiempo real
            self.apply_deformation()

        self.last_mouse_pos = current_pos

        # Marcar que ha habido un cambio significativo
        self.significant_change = True

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Maneja el evento de soltar el botón del ratón."""
        self.is_dragging = False

        # Si estamos en modo deformación y había un punto activo
        if self.mode == self.MODE_DEFORM and self.active_control_point:
            # Aplicar la deformación final
            self.apply_deformation()

            # Emitir señal de que la imagen ha sido modificada
            self.imageModified.emit()

            # Recrear los puntos de control para seguir deformando la imagen con facilidad
            # Limpiar los puntos de control existentes
            self.clear_control_points()

            # Crear nuevos puntos de control
            self.create_control_points()

            # Mostrar mensaje informativo
            print("Deformación aplicada. Puedes seguir deformando la imagen arrastrando los puntos.")

        self.active_control_point = None

        if event.button() == Qt.MiddleButton:
            # Desactivar el modo de desplazamiento con el botón central
            self.middle_button_pressed = False
            # Restaurar el modo de arrastre
            self.setDragMode(QGraphicsView.NoDrag)
            # Liberar el ratón
            self.viewport().releaseMouse()
            # Restaurar el cursor según el modo actual
            if self.mode == self.MODE_MOVE:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.unsetCursor()
        elif self.mode == self.MODE_MOVE:
            self.setCursor(Qt.OpenHandCursor)

        # Emitir señal de modificación solo si ha habido un cambio significativo
        if self.significant_change and event.button() != Qt.MiddleButton:
            self.imageModified.emit()
            self.significant_change = False  # Reiniciar el indicador de cambio

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Maneja el evento de la rueda del ratón."""
        # Zoom con la rueda del ratón (sin necesidad de Ctrl)
        factor = 1.1
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor

        self.scale(factor, factor)

    def apply_deformation(self):
        """Aplica la deformación a la imagen según las posiciones de los puntos de control."""
        if not self.pixmap_item or not self.original_image:
            return

        try:
            # Obtener las dimensiones de la imagen
            rect = self.pixmap_item.boundingRect()
            img_width = rect.width()
            img_height = rect.height()

            # Convertir las posiciones de los puntos de control a coordenadas relativas (0-1)
            # para el deformador
            custom_points = []
            for name in ["topleft", "topright", "bottomright", "bottomleft"]:
                if name in self.current_control_positions:
                    # Convertir de coordenadas de escena a coordenadas de imagen
                    scene_x, scene_y = self.current_control_positions[name]
                    scene_pos = QPointF(scene_x, scene_y)
                    img_pos = self.pixmap_item.mapFromScene(scene_pos)

                    # Convertir a coordenadas relativas para el deformador
                    custom_points.append([img_pos.x(), img_pos.y()])

            # Verificar que tenemos 4 puntos
            if len(custom_points) != 4:
                print("Se requieren exactamente 4 puntos para la deformación")
                return

            # Actualizar los puntos en el deformador
            self.deformer.set_points(custom_points)

            # Aplicar la deformación usando el deformador
            self.deformer.deform_image()

            # Obtener la imagen deformada como imagen PIL
            deformed_image = self.deformer.get_deformed_pil_image()

            # Actualizar el pixmap con la imagen deformada
            pixmap = ImageProcessor.pil_to_pixmap(deformed_image)
            self.pixmap_item.setPixmap(pixmap)

            # Actualizar la imagen actual
            self.current_image = deformed_image

        except Exception as e:
            print(f"Error al aplicar deformación: {e}")

    def get_crop_image(self):
        """Obtiene la imagen recortada según el rectángulo de selección, sin incluir el marco."""
        if not self.pixmap_item or not self.selection_rect:
            return None

        # Obtener el rectángulo de selección en coordenadas de la escena
        selection_rect = self.selection_rect.rect()
        selection_width = int(selection_rect.width())
        selection_height = int(selection_rect.height())
        rect_in_scene = self.selection_rect.mapToScene(selection_rect).boundingRect()

        # Crear una nueva escena temporal que solo contenga la imagen
        temp_scene = QGraphicsScene()

        # Crear una copia del pixmap_item con todas sus transformaciones
        pixmap = self.pixmap_item.pixmap()
        temp_pixmap_item = QGraphicsPixmapItem(pixmap)
        temp_pixmap_item.setTransform(self.pixmap_item.transform())
        temp_pixmap_item.setPos(self.pixmap_item.pos())
        temp_scene.addItem(temp_pixmap_item)

        # Crear una imagen vacía con el tamaño del rectángulo de selección
        image = QImage(selection_width, selection_height, QImage.Format_RGBA8888)
        image.fill(Qt.transparent)  # Fondo transparente

        # Renderizar solo la imagen (sin el marco de selección ni los puntos de control)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        temp_scene.render(painter, QRectF(0, 0, selection_width, selection_height), rect_in_scene)
        painter.end()

        # Convertir QImage a PIL Image
        ptr = image.constBits()
        ptr.setsize(image.byteCount())
        arr = np.array(ptr).reshape(selection_height, selection_width, 4)  # 4 para RGBA
        pil_image = Image.fromarray(arr, 'RGBA')

        # Redimensionar al tamaño objetivo
        if (selection_width, selection_height) != self.target_size:
            pil_image = pil_image.resize(self.target_size, Image.LANCZOS)

        return pil_image

    def get_state(self):
        """Obtiene el estado actual de la imagen para deshacer/rehacer."""
        if not self.pixmap_item:
            return None

        state = {
            'pixmap': self.pixmap_item.pixmap(),
            'transform': self.pixmap_item.transform(),
            'position': self.pixmap_item.pos(),
            'rotation_angle': self.rotation_angle,
            'scale_factor_x': self.scale_factor_x,
            'scale_factor_y': self.scale_factor_y,
            'original_control_positions': self.original_control_positions.copy(),
            'current_control_positions': self.current_control_positions.copy()
        }
        return state

    def set_state(self, state):
        """Establece el estado de la imagen para deshacer/rehacer."""
        if not state or not self.pixmap_item:
            return

        self.pixmap_item.setPixmap(state['pixmap'])
        self.pixmap_item.setTransform(state['transform'])
        self.pixmap_item.setPos(state['position'])
        self.rotation_angle = state['rotation_angle']
        self.scale_factor_x = state['scale_factor_x']
        self.scale_factor_y = state['scale_factor_y']

        # Restaurar posiciones de los puntos de control
        if 'original_control_positions' in state:
            self.original_control_positions = state['original_control_positions'].copy()
        if 'current_control_positions' in state:
            self.current_control_positions = state['current_control_positions'].copy()

        # Recrear rectángulo de selección y puntos de control
        self.create_selection_rect()

        # Limpiar puntos existentes
        for point in self.control_points:
            self.scene.removeItem(point)
        self.control_points = []

        # Recrear puntos de control en sus posiciones actuales
        if self.current_control_positions:
            for name, pos in self.current_control_positions.items():
                point_size = 25  # Tamaño del punto de control (aumentado)
                point = QGraphicsRectItem(pos[0] - point_size/2, pos[1] - point_size/2, point_size, point_size)
                point.setPen(QPen(QColor(0, 255, 255), 4))  # Borde más grueso
                point.setBrush(QBrush(QColor(0, 255, 255, 100)))  # Color de relleno semitransparente
                point.setData(0, name)
                self.scene.addItem(point)
                point.setZValue(2)  # Valor Z positivo para que esté encima de la imagen
                self.control_points.append(point)

    def update_control_points_position(self):
        """Actualiza la posición de los puntos de control según la transformación actual de la imagen."""
        if not self.pixmap_item or not self.control_points:
            return

        # Obtener dimensiones de la imagen
        rect = self.pixmap_item.boundingRect()

        # Posiciones de las esquinas
        corners = {
            "topleft": rect.topLeft(),
            "topright": rect.topRight(),
            "bottomleft": rect.bottomLeft(),
            "bottomright": rect.bottomRight()
        }

        # Actualizar la posición de cada punto de control
        for point in self.control_points:
            name = point.data(0)
            if name in corners:
                # Convertir a coordenadas de escena
                scene_pos = self.pixmap_item.mapToScene(corners[name])

                # Actualizar posición del punto de control
                point_size = 25  # Tamaño del punto de control
                point.setPos(scene_pos.x() - point_size/2, scene_pos.y() - point_size/2)

                # Actualizar posición actual en el diccionario
                self.current_control_positions[name] = (scene_pos.x(), scene_pos.y())

    def reset_image(self):
        """Restablece la imagen a su estado original."""
        if self.original_image:
            self.current_image = self.original_image.copy()
            pixmap = ImageProcessor.pil_to_pixmap(self.current_image)
            self.pixmap_item.setPixmap(pixmap)

            # Restablecer transformaciones
            self.pixmap_item.setTransform(QTransform())
            self.pixmap_item.setPos(0, 0)  # Restablecer posición
            self.rotation_angle = 0
            self.scale_factor_x = 1.0
            self.scale_factor_y = 1.0

            # Limpiar diccionarios de posiciones de control
            self.original_control_positions = {}
            self.current_control_positions = {}

            # Recrear rectángulo de selección y puntos de control
            self.create_selection_rect()
            self.create_control_points()

            self.imageModified.emit()
