import cv2
import numpy as np

class ImageDeformer:
    def __init__(self):
        self.original = None
        self.deformed = None
        self.points = None
        self.selected_point = -1
        self.dragging = False
        self.window_name = "Image Deformer"

    def load_image(self, image_path):
        """Carga una imagen con soporte para transparencia"""
        self.original = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if self.original is None:
            return False

        # Convertir a BGRA si es necesario
        if self.original.shape[2] == 3:
            self.original = cv2.cvtColor(self.original, cv2.COLOR_BGR2BGRA)

        h, w = self.original.shape[:2]
        self.points = np.array([
            [0, 0],      # Top-left
            [w-1, 0],    # Top-right
            [w-1, h-1],  # Bottom-right
            [0, h-1]     # Bottom-left
        ], dtype=np.float32)

        return True

    def load_image_from_pil(self, pil_image):
        """Carga una imagen desde un objeto PIL.Image"""
        if pil_image is None:
            return False

        # Convertir PIL Image a numpy array
        self.original = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)

        h, w = self.original.shape[:2]
        self.points = np.array([
            [0, 0],      # Top-left
            [w-1, 0],    # Top-right
            [w-1, h-1],  # Bottom-right
            [0, h-1]     # Bottom-left
        ], dtype=np.float32)

        return True

    def load_pil_image(self, pil_image):
        """Carga una imagen PIL con soporte para transparencia"""
        if pil_image is None:
            return False

        # Convertir imagen PIL a formato OpenCV
        import numpy as np
        self.original = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)

        h, w = self.original.shape[:2]
        self.points = np.array([
            [0, 0],      # Top-left
            [w-1, 0],    # Top-right
            [w-1, h-1],  # Bottom-right
            [0, h-1]     # Bottom-left
        ], dtype=np.float32)

        return True

    def deform_image(self, custom_points=None):
        """Aplica la deformación perspectiva a la imagen"""
        if self.original is None:
            return None

        h, w = self.original.shape[:2]
        src_points = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype=np.float32)
        dst_points = self.points if custom_points is None else np.array(custom_points, dtype=np.float32)

        try:
            # Crear un lienzo más grande para evitar recortes
            border = int(max(w, h) * 0.5)  # 50% de margen
            canvas = np.zeros((h + 2*border, w + 2*border, 4), dtype=self.original.dtype)
            canvas[border:border+h, border:border+w] = self.original

            # Ajustar los puntos al nuevo lienzo
            src_points_adj = src_points + np.array([border, border], dtype=np.float32)
            dst_points_adj = dst_points + np.array([border, border], dtype=np.float32)

            # Aplicar la transformación
            matrix = cv2.getPerspectiveTransform(src_points_adj, dst_points_adj)
            warped = cv2.warpPerspective(
                canvas, matrix, (w + 2*border, h + 2*border),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0)  # Transparente
            )

            # Recortar al tamaño original más un margen
            margin = int(max(w, h) * 0.2)  # 20% de margen
            self.deformed = warped[border-margin:border+h+margin, border-margin:w+border+margin]

            return self.deformed.copy()
        except Exception as e:
            print(f"Error en deform_image: {e}")
            return self.original.copy()

    def get_deformed_image(self):
        """Obtiene la última imagen deformada generada"""
        return self.deformed.copy() if self.deformed is not None else None

    def get_deformed_pil_image(self):
        """Obtiene la última imagen deformada generada como imagen PIL"""
        if self.deformed is None:
            return None

        # Convertir de BGRA a RGBA para PIL
        from PIL import Image
        import numpy as np
        rgba_image = cv2.cvtColor(self.deformed, cv2.COLOR_BGRA2RGBA)
        return Image.fromarray(rgba_image)

    # Método eliminado para evitar duplicación

    def reset_deformation(self):
        """Restablece los puntos a la posición original"""
        if self.original is not None:
            h, w = self.original.shape[:2]
            self.points = np.array([
                [0, 0], [w-1, 0], [w-1, h-1], [0, h-1]
            ], dtype=np.float32)
            self.deform_image()

    def set_points(self, points):
        """Establece los puntos de deformación"""
        if len(points) == 4:
            self.points = np.array(points, dtype=np.float32)

    def get_points(self):
        """Obtiene los puntos de deformación actuales"""
        return self.points.copy() if self.points is not None else None

    def interactive_deform(self, callback=None):
        """Interfaz interactiva para deformar la imagen"""
        if self.original is None:
            return

        def mouse_handler(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.selected_point = -1
                min_dist = 20
                for i, (px, py) in enumerate(self.points):
                    dist = np.sqrt((x - px)**2 + (y - py)**2)
                    if dist < min_dist:
                        min_dist = dist
                        self.selected_point = i
                if self.selected_point != -1:
                    self.dragging = True

            elif event == cv2.EVENT_MOUSEMOVE:
                if self.dragging and self.selected_point != -1:
                    self.points[self.selected_point] = [x, y]
                    self.deform_image()
                    self._update_display(callback)

            elif event == cv2.EVENT_LBUTTONUP:
                self.dragging = False
                self.selected_point = -1

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, mouse_handler)
        self._update_display(callback)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyWindow(self.window_name)

    def _update_display(self, callback=None):
        """Actualiza la visualización de la imagen deformada"""
        display_img = cv2.cvtColor(self.deformed if self.deformed is not None else self.original, cv2.COLOR_BGRA2BGR)

        # Dibujar puntos y líneas
        for i, (x, y) in enumerate(self.points):
            cv2.circle(display_img, (int(x), int(y)), 5, (0, 0, 255), -1)
            next_i = (i + 1) % 4
            cv2.line(display_img,
                    (int(self.points[i][0]), int(self.points[i][1])),
                    (int(self.points[next_i][0]), int(self.points[next_i][1])),
                    (0, 255, 0), 2)

        cv2.imshow(self.window_name, display_img)
        if callback:
            callback(self.get_deformed_image())
