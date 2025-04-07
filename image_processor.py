#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QPointF, QRectF
import numpy as np
import io
import cv2  # Necesitamos OpenCV para la deformación

class ImageProcessor:
    @staticmethod
    def pil_to_pixmap(pil_image):
        """Convierte una imagen PIL a QPixmap."""
        # Asegurarse de que la imagen esté en modo RGBA
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")

        # Convertir PIL Image a QPixmap usando buffer
        data = pil_image.tobytes("raw", "RGBA")
        qim = QImage(data, pil_image.size[0], pil_image.size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qim)

    @staticmethod
    def pixmap_to_pil(pixmap):
        """Convierte un QPixmap a imagen PIL."""
        qimage = pixmap.toImage()

        # Convertir a RGBA si es necesario
        if qimage.format() != QImage.Format_RGBA8888:
            qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

        # Obtener los datos de la imagen
        width, height = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # 4 para RGBA

        # Crear imagen PIL
        pil_image = Image.fromarray(arr, 'RGBA')

        return pil_image

    @staticmethod
    def crop_image(image, crop_rect, target_size):
        """
        Recorta una imagen según el rectángulo de selección y la redimensiona al tamaño objetivo.

        Args:
            image: PIL.Image - Imagen original
            crop_rect: QRectF - Rectángulo de selección
            target_size: tuple - (ancho, alto) del tamaño objetivo

        Returns:
            PIL.Image - Imagen recortada y redimensionada
        """
        # Convertir QRectF a coordenadas enteras
        x, y, width, height = int(crop_rect.x()), int(crop_rect.y()), int(crop_rect.width()), int(crop_rect.height())

        # Recortar la imagen
        cropped = image.crop((x, y, x + width, y + height))

        # Redimensionar al tamaño objetivo
        resized = cropped.resize(target_size, Image.LANCZOS)

        return resized

    @staticmethod
    def rotate_image(image, angle):
        """Rota una imagen PIL por el ángulo especificado."""
        return image.rotate(angle, resample=Image.BICUBIC, expand=True)

    @staticmethod
    def resize_image(image, width_factor, height_factor):
        """Redimensiona una imagen PIL según los factores de ancho y alto."""
        width, height = image.size
        new_width = int(width * width_factor)
        new_height = int(height * height_factor)
        return image.resize((new_width, new_height), Image.LANCZOS)

    @staticmethod
    def deform_image(image, source_points, target_points):
        """
        Deforma una imagen según los puntos de origen y destino.
        Utiliza OpenCV para aplicar una transformación de perspectiva.

        Args:
            image: PIL.Image - Imagen original
            source_points: list - Lista de 4 puntos (x,y) de origen (esquinas)
            target_points: list - Lista de 4 puntos (x,y) de destino (esquinas deformadas)

        Returns:
            PIL.Image - Imagen deformada
        """
        try:
            # Asegurarse de que tenemos 4 puntos
            if len(source_points) != 4 or len(target_points) != 4:
                print("Se requieren exactamente 4 puntos para la deformación")
                return image

            # Convertir la imagen PIL a formato OpenCV (numpy array)
            img_cv = np.array(image)

            # Convertir a BGR si es RGB (OpenCV usa BGR)
            if img_cv.shape[2] == 3:  # Si tiene 3 canales (RGB)
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
            elif img_cv.shape[2] == 4:  # Si tiene 4 canales (RGBA)
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGRA)

            # Convertir los puntos a formato numpy
            src_points = np.array(source_points, dtype=np.float32)
            dst_points = np.array(target_points, dtype=np.float32)

            # Calcular la matriz de transformación de perspectiva
            matrix, _ = cv2.findHomography(src_points, dst_points)

            # Aplicar la transformación
            height, width = img_cv.shape[:2]
            warped = cv2.warpPerspective(img_cv, matrix, (width, height))

            # Convertir de nuevo a formato RGB/RGBA para PIL
            if warped.shape[2] == 3:  # Si tiene 3 canales (BGR)
                warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
            elif warped.shape[2] == 4:  # Si tiene 4 canales (BGRA)
                warped = cv2.cvtColor(warped, cv2.COLOR_BGRA2RGBA)

            # Convertir de nuevo a imagen PIL
            return Image.fromarray(warped)
        except Exception as e:
            print(f"Error en deform_image: {e}")
            return image
