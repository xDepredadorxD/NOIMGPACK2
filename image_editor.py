#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QFileDialog, QGridLayout,
                            QScrollArea, QSpinBox, QAction, QToolBar,
                            QStatusBar, QMessageBox, QTabWidget, QLineEdit,
                            QSlider, QStyleFactory, QMenu, QFrame, QDockWidget,
                            QShortcut)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt5.QtGui import QIcon, QKeySequence, QTransform, QPalette, QColor, QFont
from image_view import ImageView
from PIL import Image
import math

class ImageEditor(QMainWindow):
    """Aplicación principal para editar imágenes."""

    # Definir colores para los temas
    THEME_DARK = {
        'background': QColor(50, 50, 60),
        'foreground': QColor(255, 255, 0),  # Texto amarillo en tema oscuro
        'accent': QColor(0, 120, 215),
        'button': QColor(30, 30, 40),
        'button_text': QColor(255, 255, 0),  # Texto amarillo en botones
        'border': QColor(0, 0, 0),  # Bordes negros
        'tab_background': QColor(30, 30, 40),
        'tab_text': QColor(255, 255, 0)  # Texto amarillo en pestañas
    }

    THEME_LIGHT = {
        'background': QColor(255, 255, 255),  # Fondo completamente blanco
        'foreground': QColor(0, 0, 0),  # Texto negro en tema claro
        'accent': QColor(0, 120, 215),
        'button': QColor(255, 255, 255),
        'button_text': QColor(0, 0, 0),  # Texto negro en botones
        'border': QColor(200, 200, 200),
        'tab_background': QColor(255, 255, 255),  # Pestañas con fondo blanco
        'tab_text': QColor(0, 0, 0)  # Texto negro en pestañas
    }

    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.setWindowTitle("Editor de Imágenes")
        self.setMinimumSize(1200, 800)

        # Variables de estado
        self.loaded_images = []
        self.current_page = 0
        self.images_per_page = 8  # 4x2 grid
        self.grid_size = (4, 2)
        self.target_width = 1024
        self.target_height = 1024

        # Inicializar historial para deshacer/rehacer
        self.history = []
        self.history_index = -1

        # Configurar atajos de teclado
        self.setup_shortcuts()

        # Tema actual (0: oscuro, 1: claro)
        self.current_theme = 0

        # Inicializar UI
        self.init_ui()

        # Aplicar tema después de inicializar la UI
        self.apply_theme(self.current_theme)

        # Mostrar los atajos en la barra de estado
        if hasattr(self, 'shortcuts_message'):
            self.statusBar.showMessage(self.shortcuts_message)

    def setup_shortcuts(self):
        """Configura los atajos de teclado para las herramientas."""
        # Atajos para las herramientas de edición
        # Mover (Q)
        self.move_shortcut = QShortcut(QKeySequence("Q"), self)
        self.move_shortcut.activated.connect(lambda: self.set_edit_mode(ImageView.MODE_MOVE))

        # Redimensionar (W)
        self.resize_shortcut = QShortcut(QKeySequence("W"), self)
        self.resize_shortcut.activated.connect(lambda: self.set_edit_mode(ImageView.MODE_RESIZE))

        # Rotar (R)
        self.rotate_shortcut = QShortcut(QKeySequence("R"), self)
        self.rotate_shortcut.activated.connect(lambda: self.set_edit_mode(ImageView.MODE_ROTATE))

        # Deformar (D)
        self.deform_shortcut = QShortcut(QKeySequence("D"), self)
        self.deform_shortcut.activated.connect(lambda: self.set_edit_mode(ImageView.MODE_DEFORM))

        # Deshacer (Ctrl+Z)
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo)

        # Rehacer (Ctrl+Y)
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.redo)

        # Restablecer (T)
        self.reset_shortcut = QShortcut(QKeySequence("T"), self)
        self.reset_shortcut.activated.connect(self.reset_current_image)

        # Los atajos se mostrarán en la barra de estado después de inicializar la UI
        self.shortcuts_message = "Atajos: Mover (Q), Redimensionar (W), Rotar (R), Deformar (D), Deshacer (Ctrl+Z), Rehacer (Ctrl+Y), Restablecer (T)"

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Barra de herramientas
        self.create_toolbar()

        # Panel superior para controles
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # Botones de carga y guardado con estilo
        button_style = "QPushButton { font-size: 12pt; padding: 8px; border-radius: 8px; }"

        load_btn = QPushButton("📁 Cargar Imágenes")
        load_btn.setStyleSheet(button_style)
        load_btn.clicked.connect(self.load_images)

        save_btn = QPushButton("💾 Guardar Imágenes")
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(self.save_images)

        top_layout.addWidget(load_btn)
        top_layout.addWidget(save_btn)

        # Controles de resolución con estilo
        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(resolution_widget)

        resolution_label = QLabel("🖼️ Resolución de salida:")
        resolution_label.setStyleSheet("font-size: 12pt;")
        resolution_layout.addWidget(resolution_label)

        spinbox_style = "QSpinBox { font-size: 12pt; padding: 4px; border-radius: 4px; }"

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 8192)
        self.width_spinbox.setValue(self.target_width)
        self.width_spinbox.valueChanged.connect(self.update_target_size)
        self.width_spinbox.setStyleSheet(spinbox_style)
        self.width_spinbox.setMinimumWidth(100)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 8192)
        self.height_spinbox.setValue(self.target_height)
        self.height_spinbox.valueChanged.connect(self.update_target_size)
        self.height_spinbox.setStyleSheet(spinbox_style)
        self.height_spinbox.setMinimumWidth(100)

        x_label = QLabel("x")
        x_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        resolution_layout.addWidget(self.width_spinbox)
        resolution_layout.addWidget(x_label)
        resolution_layout.addWidget(self.height_spinbox)

        top_layout.addWidget(resolution_widget)

        # Se eliminaron los controles de estiramiento

        # Añadir panel superior al layout principal
        main_layout.addWidget(top_panel)

        # Crear pestañas para la galería
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Crear primera página de la galería
        self.create_gallery_page()

        # Panel inferior para navegación
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)

        # Se eliminaron los botones de zoom

        # Botones de navegación con estilo
        nav_button_style = "QPushButton { font-size: 14pt; padding: 10px; border-radius: 8px; }"

        prev_page_btn = QPushButton("◀️ Página Anterior")
        prev_page_btn.setStyleSheet(nav_button_style)
        prev_page_btn.setMinimumWidth(200)
        prev_page_btn.clicked.connect(self.prev_page)

        # Usar un emoji diferente para la flecha derecha
        next_page_btn = QPushButton("Página Siguiente ▶️")
        next_page_btn.setStyleSheet(nav_button_style)
        next_page_btn.setMinimumWidth(200)
        next_page_btn.clicked.connect(self.next_page)

        # Se eliminaron los botones de zoom
        bottom_layout.addStretch()
        bottom_layout.addWidget(prev_page_btn)
        bottom_layout.addWidget(next_page_btn)

        main_layout.addWidget(bottom_panel)

        # Barra de estado
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo")

    def apply_theme(self, theme_index):
        """Aplica el tema seleccionado a la aplicación."""
        # Seleccionar el tema
        theme = self.THEME_DARK if theme_index == 0 else self.THEME_LIGHT

        # Crear una paleta personalizada
        palette = QPalette()

        # Configurar colores de la paleta
        palette.setColor(QPalette.Window, theme['background'])
        palette.setColor(QPalette.WindowText, theme['foreground'])
        palette.setColor(QPalette.Base, theme['background'])
        palette.setColor(QPalette.AlternateBase, theme['background'].lighter(110))
        palette.setColor(QPalette.Text, theme['foreground'])
        palette.setColor(QPalette.Button, theme['button'])
        palette.setColor(QPalette.ButtonText, theme['button_text'])
        palette.setColor(QPalette.Highlight, theme['accent'])
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Aplicar la paleta a la aplicación
        self.setPalette(palette)

        # Aplicar estilo a las pestañas
        tab_style = f"""
        QTabWidget::pane {{ /* El panel que contiene el contenido de las pestañas */
            border: 1px solid {theme['border'].name()};
            background-color: {theme['background'].name()};
        }}

        QTabBar::tab {{ /* Estilo de las pestañas */
            background-color: {theme['tab_background'].name()};
            color: {theme['tab_text'].name()};
            border: 1px solid {theme['border'].name()};
            border-bottom-color: {theme['border'].name()};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 6ex;
            padding: 4px 8px;
            font-size: 9pt;
            margin-right: 2px;
        }}

        QTabBar::tab:selected, QTabBar::tab:hover {{
            background-color: {theme['accent'].name()};
            color: white;
        }}

        /* Estilo adicional para el contenedor de pestañas */
        QTabWidget {{
            background-color: {theme['background'].name()};
        }}

        /* Estilo para el widget que contiene las pestañas */
        QTabWidget::tab-bar {{
            background-color: {theme['background'].name()};
            alignment: center;
        }}
        """

        self.tab_widget.setStyleSheet(tab_style)

        # Aplicar estilo a los botones de navegación
        nav_button_style = f"""
        QPushButton {{
            font-size: 12pt;
            padding: 8px;
            border-radius: 8px;
            background-color: {theme['button'].name()};
            color: {theme['button_text'].name()};
            border: 1px solid {theme['border'].name()};
        }}

        QPushButton:hover {{
            background-color: {theme['accent'].name()};
            color: white;
        }}
        """

        # Actualizar estilo de los botones de navegación
        for widget in self.findChildren(QPushButton):
            widget.setStyleSheet(nav_button_style)

        # Aplicar estilo a los elementos del menú
        menu_style = f"""
        QMenuBar {{
            background-color: {theme['background'].name()};
            color: {theme['foreground'].name()};
        }}

        QMenuBar::item {{
            background-color: {theme['background'].name()};
            color: {theme['foreground'].name()};
        }}

        QMenuBar::item:selected {{
            background-color: {theme['accent'].name()};
            color: white;
        }}

        QMenu {{
            background-color: {theme['background'].name()};
            color: {theme['foreground'].name()};
            border: 1px solid {theme['border'].name()};
        }}

        QMenu::item:selected {{
            background-color: {theme['accent'].name()};
            color: white;
        }}

        QLabel {{
            color: {theme['foreground'].name()};
        }}

        QSpinBox {{
            background-color: {theme['button'].name()};
            color: {theme['button_text'].name()};
            border: 1px solid {theme['border'].name()};
            border-radius: 4px;
            padding: 2px;
        }}

        QToolBar {{
            background-color: {theme['background'].name()};
            border: 1px solid {theme['border'].name()};
            spacing: 3px;
        }}

        QToolButton {{
            font-size: 12pt;
            padding: 8px;
            border-radius: 8px;
            background-color: {theme['button'].name()};
            color: {theme['button_text'].name()};
            border: 1px solid {theme['border'].name()};
            min-width: 100px;
            min-height: 100px;
            max-width: 100px;
            max-height: 100px;
            margin: 5px;
            text-align: center;
        }}

        /* Permitir HTML en los botones */
        QToolButton {{
            qproperty-toolButtonStyle: 5; /* TextUnderIcon */
            qproperty-autoRaise: false;
        }}

        QToolButton:hover {{
            background-color: {theme['accent'].name()};
            color: white;
        }}

        QToolButton::menu-indicator {{
            image: none;
        }}

        QStatusBar {{
            background-color: {theme['background'].name()};
            color: {theme['foreground'].name()};
            border-top: 1px solid {theme['border'].name()};
        }}

        /* Estilo para todos los widgets para asegurar fondo consistente */
        QWidget {{
            background-color: {theme['background'].name()};
        }}

        /* Estilo para los paneles */
        QFrame, QGroupBox {{
            background-color: {theme['background'].name()};
            border: 1px solid {theme['border'].name()};
            border-radius: 4px;
        }}

        /* Estilo para la barra de título */
        QMainWindow::title {{
            background-color: black;
            color: white;
        }}
        """

        self.setStyleSheet(menu_style)

        # Configurar la barra de título (solo funciona en Windows)
        try:
            import ctypes
            from ctypes import windll, byref, sizeof, c_int

            # Constantes para la API de Windows
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36

            # Colores: negro para el fondo, blanco para el texto
            caption_color = 0x000000  # Negro
            text_color = 0xFFFFFF     # Blanco

            # Obtener el identificador de la ventana
            hwnd = self.winId().__int__()

            # Establecer el color de la barra de título
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR,
                byref(c_int(caption_color)), sizeof(c_int)
            )

            # Establecer el color del texto de la barra de título
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_TEXT_COLOR,
                byref(c_int(text_color)), sizeof(c_int)
            )
        except Exception as e:
            print(f"No se pudo cambiar el color de la barra de título: {e}")

        # Guardar el tema actual
        self.current_theme = theme_index

    def create_toolbar(self):
        """Crea la barra de herramientas vertical en el lado izquierdo."""
        # Crear un panel vertical para la barra de herramientas
        toolbar_widget = QWidget()
        toolbar_layout = QVBoxLayout(toolbar_widget)
        toolbar_layout.setSpacing(10)
        toolbar_layout.setContentsMargins(5, 10, 5, 10)

        # Crear botones personalizados con emojis grandes y texto pequeño debajo
        # Función para crear botones con emojis
        def create_tool_button(emoji, text, callback):
            button = QPushButton()
            button.setFixedSize(70, 70)  # Reducido en aproximadamente 30%
            layout = QVBoxLayout(button)
            layout.setContentsMargins(3, 3, 3, 3)  # Reducir márgenes
            layout.setSpacing(2)  # Reducir espaciado

            emoji_label = QLabel(emoji)
            emoji_label.setAlignment(Qt.AlignCenter)
            emoji_label.setStyleSheet("font-size: 24pt;")  # Reducido de 36pt a 24pt

            text_label = QLabel(text)
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setStyleSheet("font-size: 8pt;")  # Reducido de 10pt a 8pt
            text_label.setObjectName("marquee_text")  # Nombre para identificar en animación

            layout.addWidget(emoji_label)
            layout.addWidget(text_label)

            button.clicked.connect(callback)
            return button

        # Botones de edición con atajos de teclado
        move_btn = create_tool_button("Ⓜ️", "Mover (Q)", lambda: self.set_edit_mode(ImageView.MODE_MOVE))
        toolbar_layout.addWidget(move_btn)

        resize_btn = create_tool_button("🔛", "Redimensionar (W)", lambda: self.set_edit_mode(ImageView.MODE_RESIZE))
        toolbar_layout.addWidget(resize_btn)

        rotate_btn = create_tool_button("🔄️", "Rotar (R)", lambda: self.set_edit_mode(ImageView.MODE_ROTATE))
        toolbar_layout.addWidget(rotate_btn)

        deform_btn = create_tool_button("🅳", "Deformar (D)", lambda: self.set_edit_mode(ImageView.MODE_DEFORM))
        toolbar_layout.addWidget(deform_btn)

        # Separador
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator1)

        # Botones de deshacer/rehacer con atajos de teclado
        undo_btn = create_tool_button("↩️", "Deshacer (Ctrl+Z)", self.undo)
        toolbar_layout.addWidget(undo_btn)

        redo_btn = create_tool_button("↪️", "Rehacer (Ctrl+Y)", self.redo)
        toolbar_layout.addWidget(redo_btn)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator2)

        # Botón de reset con atajo de teclado
        reset_btn = create_tool_button("®️", "Restablecer (T)", self.reset_current_image)
        toolbar_layout.addWidget(reset_btn)

        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator3)

        # Botón para cambiar el tema
        theme_btn = create_tool_button("🌗", "Tema", self.toggle_theme)
        toolbar_layout.addWidget(theme_btn)

        # Añadir espacio al final
        toolbar_layout.addStretch()

        # Crear un dock widget para contener la barra de herramientas
        dock = QDockWidget("Herramientas", self)
        dock.setWidget(toolbar_widget)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)  # No permitir mover/cerrar
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)  # Solo permitir en el lado izquierdo
        dock.setFixedWidth(90)  # Ancho fijo reducido (30% menos que el original de ~130px)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # Guardar referencia a los botones
        self.tool_buttons = {
            'move': move_btn,
            'resize': resize_btn,
            'rotate': rotate_btn,
            'deform': deform_btn,
            'undo': undo_btn,
            'redo': redo_btn,
            'reset': reset_btn,
            'theme': theme_btn
        }

        # Iniciar la animación de desplazamiento para los textos
        self.start_marquee_animation()

    def create_gallery_page(self):
        """Crea una nueva página en la galería."""
        page = QWidget()
        layout = QGridLayout(page)

        # Crear una cuadrícula de vistas de imágenes
        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                image_view = ImageView()
                image_view.setMinimumSize(250, 250)
                image_view.imageModified.connect(self.on_image_modified)
                # Hacer que la vista sea seleccionable al hacer clic
                image_view.mousePressEvent = lambda event, view=image_view: self.on_image_view_clicked(event, view)
                layout.addWidget(image_view, row, col)

        # Añadir la página a las pestañas
        tab_index = self.tab_widget.count()
        self.tab_widget.addTab(page, f"P{tab_index + 1}")

        return page

    def load_images(self):
        """Carga imágenes desde archivos."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar Imágenes", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;Todos los archivos (*)"
        )

        if not file_paths:
            return

        # Añadir nuevas imágenes a la lista
        self.loaded_images.extend(file_paths)

        # Actualizar la galería
        self.update_gallery()

        self.statusBar.showMessage(f"Cargadas {len(file_paths)} imágenes")

    def update_gallery(self):
        """Actualiza la galería con las imágenes cargadas."""
        # Calcular número de páginas necesarias
        total_pages = math.ceil(len(self.loaded_images) / self.images_per_page)

        # Crear páginas adicionales si es necesario
        while self.tab_widget.count() < total_pages:
            self.create_gallery_page()

        # Actualizar cada página
        for page_idx in range(total_pages):
            page = self.tab_widget.widget(page_idx)
            layout = page.layout()

            # Índices de imágenes para esta página
            start_idx = page_idx * self.images_per_page
            end_idx = min(start_idx + self.images_per_page, len(self.loaded_images))

            # Actualizar cada vista de imagen en la página
            for i in range(self.images_per_page):
                idx = start_idx + i
                row = i // self.grid_size[0]
                col = i % self.grid_size[0]

                # Obtener el widget ImageView
                item = layout.itemAtPosition(row, col)
                if item:
                    image_view = item.widget()

                    # Establecer imagen si está disponible
                    if idx < end_idx:
                        image_view.set_image(self.loaded_images[idx])
                        image_view.set_target_size(self.target_width, self.target_height)

        # Mostrar la página actual
        if self.loaded_images and self.current_page < total_pages:
            self.tab_widget.setCurrentIndex(self.current_page)

    def save_images(self):
        """Guarda las imágenes editadas."""
        try:
            if not self.loaded_images:
                QMessageBox.warning(self, "Advertencia", "No hay imágenes para guardar.")
                return

            # Seleccionar directorio de destino
            save_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio para Guardar")

            if not save_dir:
                return

            # Guardar cada imagen
            saved_count = 0
            for page_idx in range(self.tab_widget.count()):
                page = self.tab_widget.widget(page_idx)
                layout = page.layout()

                # Índices de imágenes para esta página
                start_idx = page_idx * self.images_per_page
                end_idx = min(start_idx + self.images_per_page, len(self.loaded_images))

                # Procesar cada vista de imagen en la página
                for i in range(self.images_per_page):
                    idx = start_idx + i
                    if idx >= end_idx:
                        break

                    row = i // self.grid_size[0]
                    col = i % self.grid_size[0]

                    # Obtener el widget ImageView
                    item = layout.itemAtPosition(row, col)
                    if item:
                        image_view = item.widget()

                        try:
                            # Obtener imagen recortada
                            cropped_image = image_view.get_crop_image()
                            if cropped_image:
                                # Generar nombre de archivo
                                base_name = os.path.basename(self.loaded_images[idx])
                                name, ext = os.path.splitext(base_name)
                                # Asegurarse de que la extensión sea .png para mantener transparencia
                                save_path = os.path.join(save_dir, f"{name}_edited.png")

                                # Guardar imagen
                                cropped_image.save(save_path, format="PNG")
                                saved_count += 1
                                print(f"Guardada imagen en: {save_path}")
                        except Exception as e:
                            print(f"Error al guardar imagen {idx}: {e}")

            if saved_count > 0:
                QMessageBox.information(self, "Guardado completado", f"Guardadas {saved_count} imágenes en {save_dir}")
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudo guardar ninguna imagen.")

            self.statusBar.showMessage(f"Guardadas {saved_count} imágenes en {save_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar imágenes: {e}")
            print(f"Error en save_images: {e}")

    def update_target_size(self):
        """Actualiza el tamaño objetivo para el recorte."""
        self.target_width = self.width_spinbox.value()
        self.target_height = self.height_spinbox.value()

        # Actualizar todas las vistas de imágenes
        for page_idx in range(self.tab_widget.count()):
            page = self.tab_widget.widget(page_idx)
            layout = page.layout()

            for row in range(self.grid_size[1]):
                for col in range(self.grid_size[0]):
                    item = layout.itemAtPosition(row, col)
                    if item:
                        image_view = item.widget()
                        image_view.set_target_size(self.target_width, self.target_height)

    def start_marquee_animation(self):
        """Inicia la animación de desplazamiento para los textos de la barra de herramientas."""
        # Crear un temporizador para actualizar la animación
        self.marquee_timer = QTimer(self)
        self.marquee_timer.timeout.connect(self.update_marquee_text)
        self.marquee_timer.start(100)  # Actualizar cada 100ms para una animación más lenta

        # Inicializar variables para la animación
        self.marquee_offset = 0
        self.marquee_speed = 0.5  # Velocidad de desplazamiento reducida

    def update_marquee_text(self):
        """Actualiza la posición del texto en la animación de desplazamiento."""
        # Incrementar el offset para todas las etiquetas
        self.marquee_offset += self.marquee_speed

        # Buscar todas las etiquetas de texto en los botones de herramientas
        for button_name, button in self.tool_buttons.items():
            # Buscar la etiqueta de texto en el botón
            for child in button.findChildren(QLabel):
                if child.objectName() == "marquee_text":
                    # Obtener el texto actual
                    text = child.text()

                    # Guardar el texto original si no lo hemos guardado antes
                    if not hasattr(child, 'original_text'):
                        child.original_text = text
                    else:
                        # Usar el texto original guardado
                        text = child.original_text

                    # Calcular el ancho del texto y del contenedor
                    metrics = child.fontMetrics()
                    text_width = metrics.width(text)
                    label_width = child.width()

                    # Crear un texto más largo para la animación con espacios adicionales
                    # Añadir exactamente 4 espacios entre repeticiones como solicitó el usuario
                    padding = "    "  # 4 espacios
                    long_text = text + padding + text + padding

                    # Calcular la posición actual para un desplazamiento más lento
                    # El texto se desplaza de derecha a izquierda
                    total_width = len(long_text)
                    current_offset = int(self.marquee_offset) % total_width

                    # Crear el texto visible con un tamaño fijo para evitar saltos
                    # Mostrar una ventana de caracteres que se desplaza por el texto largo
                    window_size = min(20, len(long_text))  # Mostrar hasta 20 caracteres a la vez
                    start_pos = current_offset
                    end_pos = start_pos + window_size

                    # Asegurarse de que no nos pasamos del final del texto
                    if end_pos > len(long_text):
                        visible_text = long_text[start_pos:] + long_text[:end_pos - len(long_text)]
                    else:
                        visible_text = long_text[start_pos:end_pos]

                    # Actualizar el texto de la etiqueta
                    child.setText(visible_text)

    def toggle_theme(self):
        """Cambia entre los temas oscuro y claro."""
        # Cambiar al siguiente tema
        next_theme = 1 if self.current_theme == 0 else 0
        self.apply_theme(next_theme)

        # Mostrar mensaje
        theme_name = "Claro" if next_theme == 1 else "Oscuro"
        self.statusBar.showMessage(f"Tema cambiado a: {theme_name}")

    def set_edit_mode(self, mode):
        """Establece el modo de edición para la vista de imagen actual."""
        current_view = self.get_current_image_view()
        if current_view:
            current_view.set_mode(mode)

    def get_current_image_view(self):
        """Obtiene la vista de imagen actualmente seleccionada."""
        # Obtener la página actual
        current_page = self.tab_widget.currentWidget()
        if not current_page:
            return None

        # Obtener el widget que tiene el foco
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, ImageView):
            # Guardar referencia a la vista seleccionada
            self.last_selected_view = focused_widget
            return focused_widget

        # Si hay una vista seleccionada previamente, devolverla
        if hasattr(self, 'last_selected_view') and self.last_selected_view is not None:
            # Verificar que la vista seleccionada esté en la página actual
            layout = current_page.layout()
            for row in range(self.grid_size[1]):
                for col in range(self.grid_size[0]):
                    item = layout.itemAtPosition(row, col)
                    if item and item.widget() == self.last_selected_view:
                        return self.last_selected_view

        # Si no hay widget con foco ni vista seleccionada previamente, devolver el primer ImageView de la página
        layout = current_page.layout()
        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                item = layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), ImageView):
                    self.last_selected_view = item.widget()
                    return self.last_selected_view

        return None

    # Se eliminaron las funciones zoom_in_gallery y zoom_out_gallery

    def prev_page(self):
        """Navega a la página anterior."""
        if self.tab_widget.count() > 1:
            new_index = max(0, self.tab_widget.currentIndex() - 1)
            self.tab_widget.setCurrentIndex(new_index)
            self.current_page = new_index

    def next_page(self):
        """Navega a la página siguiente."""
        if self.tab_widget.count() > 1:
            new_index = min(self.tab_widget.count() - 1, self.tab_widget.currentIndex() + 1)
            self.tab_widget.setCurrentIndex(new_index)
            self.current_page = new_index

    def on_image_view_clicked(self, event, view):
        """Maneja el evento de clic en una vista de imagen."""
        # Guardar la vista seleccionada
        self.last_selected_view = view
        # Dar foco a la vista
        view.setFocus()
        # Mostrar un indicador visual de selección (opcional)
        self.highlight_selected_view(view)
        # Llamar al método original de mousePressEvent
        ImageView.mousePressEvent(view, event)

    def highlight_selected_view(self, selected_view):
        """Resalta visualmente la vista seleccionada."""
        # Obtener la página actual
        current_page = self.tab_widget.currentWidget()
        if not current_page:
            return

        # Recorrer todas las vistas de imagen en la página
        layout = current_page.layout()
        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                item = layout.itemAtPosition(row, col)
                if item:
                    view = item.widget()
                    if isinstance(view, ImageView):
                        # Aplicar estilo según si es la vista seleccionada o no
                        if view == selected_view:
                            view.setStyleSheet("border: 3px solid #3498db;")
                        else:
                            view.setStyleSheet("")

    def on_image_modified(self):
        """Maneja el evento de modificación de imagen."""
        sender = self.sender()
        if isinstance(sender, ImageView):
            # Guardar la vista seleccionada
            self.last_selected_view = sender
            # Obtener el estado actual de la imagen
            current_state = sender.get_state()
            if current_state:
                # Truncar la historia si estamos en medio de ella
                self.history = self.history[:self.history_index + 1]
                # Añadir el nuevo estado a la historia
                self.history.append({'view': sender, 'state': current_state})
                self.history_index = len(self.history) - 1
                print(f"Estado guardado: {self.history_index}")

    def undo(self):
        """Deshace la última acción."""
        try:
            if self.history_index > 0:
                self.history_index -= 1
                history_item = self.history[self.history_index]
                view = history_item['view']
                state = history_item['state']
                view.set_state(state)
                self.statusBar.showMessage(f"Deshacer (estado {self.history_index})")
                print(f"Deshacer: restaurado estado {self.history_index}")
            else:
                self.statusBar.showMessage("No hay más acciones para deshacer")
        except Exception as e:
            print(f"Error en undo: {e}")
            self.statusBar.showMessage(f"Error al deshacer: {e}")

    def redo(self):
        """Rehace la última acción deshecha."""
        try:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                history_item = self.history[self.history_index]
                view = history_item['view']
                state = history_item['state']
                view.set_state(state)
                self.statusBar.showMessage(f"Rehacer (estado {self.history_index})")
                print(f"Rehacer: restaurado estado {self.history_index}")
            else:
                self.statusBar.showMessage("No hay más acciones para rehacer")
        except Exception as e:
            print(f"Error en redo: {e}")
            self.statusBar.showMessage(f"Error al rehacer: {e}")

    def reset_current_image(self):
        """Restablece la imagen actual a su estado original."""
        current_view = self.get_current_image_view()
        if current_view:
            current_view.reset_image()
            self.statusBar.showMessage("Imagen restablecida")
