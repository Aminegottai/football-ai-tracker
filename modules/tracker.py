import numpy as np

# ══════════════════════════════════════════════════════
# SIMPLE TRACKER IOU
# ══════════════════════════════════════════════════════

class SimpleTracker:
    """
    Suivi d'objets basé sur l'Intersection over Union (IOU).
    
    Attributes:
        next_id (int): Prochain ID à assigner
        tracks (dict): Dictionnaire des pistes actives
        max_lost (int): Nombre max de frames avant suppression
        min_iou (float): Seuil IOU minimum pour la correspondance
    """
    
    def __init__(self, max_lost=30, min_iou=0.20):
        self.next_id = 1
        self.tracks = {}
        self.max_lost = max_lost
        self.min_iou = min_iou

    def _iou(self, b1, b2):
        """
        Calcule l'Intersection over Union entre deux boîtes.
        
        Args:
            b1: [x1, y1, x2, y2]
            b2: [x1, y1, x2, y2]
            
        Returns:
            float: Valeur IOU (0-1)
        """
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        if inter == 0:
            return 0.0
        
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        
        return inter / (a1 + a2 - inter + 1e-6)

    def update(self, detections):
        """
        Mise à jour du tracker avec les nouvelles détections.
        
        Args:
            detections (list): Liste des détections avec 'box' et 'class'
            
        Returns:
            list: Détections mises à jour avec 'track_id'
        """
        # Pas de détections
        if not detections:
            for tid in list(self.tracks):
                self.tracks[tid]['lost'] += 1
                if self.tracks[tid]['lost'] > self.max_lost:
                    del self.tracks[tid]
            return detections

        # Pas de pistes existantes
        if not self.tracks:
            for det in detections:
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = {'box': det['box'], 'lost': 0}
                det['track_id'] = tid
            return detections

        # Matching entre détections et pistes
        track_ids = list(self.tracks.keys())
        scores = np.zeros((len(detections), len(track_ids)))
        
        for di, det in enumerate(detections):
            for ti, tid in enumerate(track_ids):
                scores[di, ti] = self._iou(det['box'], 
                                          self.tracks[tid]['box'])

        matched_d = set()
        matched_t = set()
        
        # Greedy matching
        while True:
            if scores.size == 0:
                break
            idx = np.unravel_index(np.argmax(scores), scores.shape)
            di, ti = idx
            if scores[di, ti] < self.min_iou:
                break
            
            matched_d.add(di)
            matched_t.add(ti)
            tid = track_ids[ti]
            detections[di]['track_id'] = tid
            self.tracks[tid]['box'] = detections[di]['box']
            self.tracks[tid]['lost'] = 0
            scores[di, :] = -1
            scores[:, ti] = -1

        # Nouvelles détections
        for di, det in enumerate(detections):
            if di not in matched_d:
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = {'box': det['box'], 'lost': 0}
                det['track_id'] = tid

        # Pistes perdues
        for ti, tid in enumerate(track_ids):
            if ti not in matched_t:
                self.tracks[tid]['lost'] += 1
                if self.tracks[tid]['lost'] > self.max_lost:
                    del self.tracks[tid]
        
        return detections