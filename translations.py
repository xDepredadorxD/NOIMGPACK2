#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Diccionario de traducciones
translations = {
    'en': {
        # Títulos y etiquetas generales
        'window_title': 'Image Editor',
        'ready': 'Ready',
        'tools': 'Tools',

        # Botones de carga y guardado
        'load_images': '📁 Load Images',
        'save_images': '💾 Save Images',

        # Resolución
        'output_resolution': '🖼️ Output Resolution:',

        # Navegación
        'prev_page': '◀️ Previous Page',
        'next_page': '▶️ Next Page',

        # Herramientas de edición
        'move': 'Move (Q)',
        'resize': 'Resize (W)',
        'rotate': 'Rotate (R)',
        'deform': 'Deform (D)',
        'undo': 'Undo (Ctrl+Z)',
        'redo': 'Redo (Ctrl+Y)',
        'reset': 'Reset (T)',
        'theme': 'Theme',

        # Mensajes de estado y atajos
        'shortcuts': 'Shortcuts: Move (Q), Resize (W), Rotate (R), Deform (D), Undo (Ctrl+Z), Redo (Ctrl+Y), Reset (T)',
        'deformation_applied': 'Deformation applied. You can continue deforming the image by dragging the points.',
        'images_loaded': 'Loaded',

        # Diálogos
        'load_dialog_title': 'Select Images',
        'save_dialog_title': 'Save Image',
        'save_directory_title': 'Select Directory to Save',
        'all_images': 'All Images',
        'all_files': 'All Files',
        'png_images': 'PNG Images',
        'save_success': 'Image saved successfully',
        'save_error': 'Error saving image: ',
        'warning': 'Warning',
        'no_images_to_save': 'No images to save.',

        # Botones de idioma
        'language': 'Language',
        'spanish': 'Spanish',
        'english': 'English'
    },
    'es': {
        # Títulos y etiquetas generales
        'window_title': 'Editor de Imágenes',
        'ready': 'Listo',
        'tools': 'Herramientas',

        # Botones de carga y guardado
        'load_images': '📁 Cargar Imágenes',
        'save_images': '💾 Guardar Imágenes',

        # Resolución
        'output_resolution': '🖼️ Resolución de salida:',

        # Navegación
        'prev_page': '◀️ Página Anterior',
        'next_page': 'Página Siguiente ▶️',

        # Herramientas de edición
        'move': 'Mover (Q)',
        'resize': 'Redimensionar (W)',
        'rotate': 'Rotar (R)',
        'deform': 'Deformar (D)',
        'undo': 'Deshacer (Ctrl+Z)',
        'redo': 'Rehacer (Ctrl+Y)',
        'reset': 'Restablecer (T)',
        'theme': 'Tema',

        # Mensajes de estado y atajos
        'shortcuts': 'Atajos: Mover (Q), Redimensionar (W), Rotar (R), Deformar (D), Deshacer (Ctrl+Z), Rehacer (Ctrl+Y), Restablecer (T)',
        'deformation_applied': 'Deformación aplicada. Puedes seguir deformando la imagen arrastrando los puntos.',
        'images_loaded': 'Cargadas',

        # Diálogos
        'load_dialog_title': 'Seleccionar Imágenes',
        'save_dialog_title': 'Guardar Imagen',
        'save_directory_title': 'Seleccionar Directorio para Guardar',
        'all_images': 'Todas las Imágenes',
        'all_files': 'Todos los archivos',
        'png_images': 'Imágenes PNG',
        'save_success': 'Imagen guardada correctamente',
        'save_error': 'Error al guardar la imagen: ',
        'warning': 'Advertencia',
        'no_images_to_save': 'No hay imágenes para guardar.',

        # Botones de idioma
        'language': 'Idioma',
        'spanish': 'Español',
        'english': 'Inglés'
    }
}

class Translator:
    def __init__(self, language='es'):
        self.language = language

    def set_language(self, language):
        """Cambia el idioma actual."""
        if language in translations:
            self.language = language
            return True
        return False

    def get_text(self, key):
        """Obtiene el texto traducido para la clave dada."""
        if key in translations[self.language]:
            return translations[self.language][key]
        # Si no se encuentra la clave, devolver la clave en inglés o la clave original
        if self.language != 'en' and key in translations['en']:
            return translations['en'][key]
        return key
