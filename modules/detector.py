import cv2
import numpy as np
from ultralytics import YOLO
import config

# ══════════════════════════════════════════════════════
# DETECTOR - YOLO
# ══════════════════════════════════════════════════════

class Detector:
    """
    Détection d'objets (joueurs, ballon, arbitres) avec YOLO.
    Extraction des couleurs de maillots.
    
    Attributes:
        model: Modèle YOLO chargé
    """
    
    def __init__(self, model_path):
        """
        Initialise le détecteur.
        
        Args:
            model_path: Chemin vers le modèle YOLO (.pt)
        """
        self.model = YOLO(model_path)

    def detect(self, frame, conf=None):
        """
        Détecte les objets dans le frame.
        
        Args:
            frame: Image numpy
            conf: Seuil de confiance (par défaut config.DETECTION_CONF)
            
        Returns:
            list: Détections avec 'box', 'class', 'conf'
        """
        if conf is None:
            conf = config.DETECTION_CONF
        
        results = self.model(frame, conf=conf, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            cls = int(box.cls[0])
            conf_v = float(box.conf[0])
            coords = box.xyxy[0].cpu().numpy()
            label = self.model.names[cls]
            
            detections.append({
                'box': coords,
                'class': label,
                'conf': conf_v,
                'team': 0,
                'team_prob': 0.0,
                'track_id': -1
            })
        
        return detections

    def get_jersey_color(self, frame, box):
        """
        Extrait la couleur du maillot depuis une région d'intérêt.
        
        Args:
            frame: Image BGR
            box: [x1, y1, x2, y2]
            
        Returns:
            np.array: Couleur HSV médiane ou None
        """
        x1, y1, x2, y2 = map(int, box)
        h = y2 - y1
        w = x2 - x1
        
        if h < 20 or w < 10:
            return None
        
        # ROI au centre du joueur (torso)
        y_start, y_end = config.JERSEY_COLOR_Y_RANGE
        x_start, x_end = config.JERSEY_COLOR_X_RANGE
        
        y1r = y1 + int(h * y_start)
        y2r = y1 + int(h * y_end)
        x1r = x1 + int(w * x_start)
        x2r = x2 - int(w * (1 - x_end))
        
        roi = frame[y1r:y2r, x1r:x2r]
        if roi.size == 0:
            return None
        
        # Conversion en HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        px = hsv.reshape(-1, 3).astype(np.float32)
        
        # Filtrage des pixels "non-couleur" (gris, noir)
        mask = (((px[:, 0] > 35) & (px[:, 0] < 85) & (px[:, 1] > 40))
                | (px[:, 1] < 25) | (px[:, 2] < 30))
        px = px[~mask]
        
        if len(px) < 15:
            return None
        
        return np.median(px, axis=0)