import cv2
import time
from .detector import Detector
from .tracker import SimpleTracker
from .team_classifier import TeamClassifierGMM
from .possession import PossessionTracker
from .dashboard import FootballDashboard
import config

# ══════════════════════════════════════════════════════
# FOOTBALL ANALYZER - ORCHESTRATION
# ══════════════════════════════════════════════════════

class FootballAnalyzer:
    """
    Orchestrateur principal du système d'analyse footballistique.
    Combine détection, suivi, classification et possession.
    
    Attributes:
        model: Détecteur YOLO
        classifier: Classifieur d'équipes GMM
        tracker: Tracker IOU
        possession: Tracker de possession
        dashboard: Dashboard de visualisation
    """
    
    def __init__(self, model_path, fps=30.0):
        """
        Initialise l'analyseur.
        
        Args:
            model_path: Chemin du modèle YOLO
            fps: Frames par seconde de la vidéo
        """
        self.detector = Detector(model_path)
        self.classifier = TeamClassifierGMM()
        self.tracker = SimpleTracker(
            max_lost=config.TRACKER_MAX_LOST,
            min_iou=config.TRACKER_MIN_IOU
        )
        self.possession = PossessionTracker(fps=fps)
        self.dashboard = FootballDashboard()
        
        self.frame_count = 0
        self.calib_frames = 0
        self.MAX_CALIB = config.CALIB_MAX_FRAMES
        self.calib_colors = []
        self.fps_calc = fps
        self._t = time.time()

    def process_frame(self, frame, conf=None):
        """
        Traite un frame complet.
        
        Args:
            frame: Image BGR
            conf: Seuil de confiance pour YOLO
            
        Returns:
            tuple: (detections, ball_box)
        """
        h, w = frame.shape[:2]
        
        # 1. Détection YOLO
        detections = self.detector.detect(frame, conf=conf)
        
        # Séparation joueurs / autres
        players = [d for d in detections if d['class'].lower() == 'player']
        others = [d for d in detections if d['class'].lower() != 'player']
        ball_box = next((d['box'] for d in others
                        if d['class'].lower() == 'ball'), None)

        # 2. Suivi
        if players:
            players = self.tracker.update(players)

        # 3. Classification des équipes
        for det in players:
            color = self.detector.get_jersey_color(frame, det['box'])
            if color is None:
                continue
            
            if not self.classifier.calibrated:
                self.calib_colors.append(color)
            else:
                t, p = self.classifier.predict_stable(
                    det['track_id'], color)
                det['team'] = t
                det['team_prob'] = p

        # 4. Calibration
        if not self.classifier.calibrated:
            self.calib_frames += 1
            if (self.calib_frames >= self.MAX_CALIB and
                    len(self.calib_colors) >= config.CALIB_MIN_COLORS):
                self.classifier.all_colors = self.calib_colors
                if self.classifier.fit():
                    self.calib_colors.clear()

        # 5. Possession
        all_dets = players + others
        self.possession.update(ball_box, players, w, h)

        # 6. FPS
        now = time.time()
        self.fps_calc = 1.0 / max(now - self._t, 1e-6)
        self._t = now
        self.frame_count += 1
        
        return all_dets, ball_box

    def draw_camera(self, frame, detections, ball_box):
        """
        Dessine les détections sur le frame caméra.
        
        Args:
            frame: Image BGR
            detections: Liste des détections
            ball_box: Boîte du ballon
            
        Returns:
            frame: Image avec annotations
        """
        t_bgr = self.classifier.team_colors_bgr
        cls_c = {
            'ball': (0, 165, 255),
            'referee': (0, 0, 255),
            'goalkeeper': (0, 255, 255)
        }

        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            label = det['class'].lower()
            team = det.get('team', 0)
            tid = det.get('track_id', -1)
            locked = tid in self.classifier.id_team_locked

            if label == 'player':
                color = t_bgr.get(team, (160, 160, 160))
                text = (f"T{team}" if team > 0 else "?")
            else:
                color = cls_c.get(label, (255, 255, 255))
                text = label[:4]

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(frame, (x1, y1 - 18), (x1 + 30, y1), color, -1)
            cv2.putText(frame, text, (x1 + 2, y1 - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0),
                       1, cv2.LINE_AA)
            if label == 'player' and locked:
                cv2.circle(frame, (x2 - 4, y1 + 4), 4, (0, 255, 0), -1)

        # Ballon avec couleur équipe actuelle
        curr = self.possession.current_team
        if curr > 0 and ball_box is not None:
            bx1, by1, bx2, by2 = map(int, ball_box)
            cv2.circle(frame, ((bx1 + bx2) // 2, (by1 + by2) // 2),
                      26, t_bgr.get(curr, (255, 255, 0)), 3)

        # Indicateur calibration
        if self.classifier.calibrated:
            for tid in [1, 2]:
                c = t_bgr.get(tid, (160, 160, 160))
                y = 20 + (tid - 1) * 22
                cv2.circle(frame, (15, y), 7, c, -1)
                cv2.putText(frame, f"T{tid}", (26, y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                           (255, 255, 255), 1, cv2.LINE_AA)
        else:
            pct = min(1., self.calib_frames / self.MAX_CALIB)
            h_f, w_f = frame.shape[:2]
            bw = 200
            bx = w_f - bw - 10
            by = 10
            cv2.rectangle(frame, (bx, by), (bx + bw, by + 18),
                         (40, 40, 40), -1)
            cv2.rectangle(frame, (bx, by),
                         (bx + int(bw * pct), by + 18), (0, 200, 255), -1)
            cv2.putText(frame, f"Calib {int(pct * 100)}%",
                       (bx + 40, by + 13), cv2.FONT_HERSHEY_SIMPLEX,
                       0.42, (0, 0, 0), 1)

        return frame

    def get_dashboard(self):
        """
        Génère le dashboard.
        
        Returns:
            np.array: Image du dashboard
        """
        t_bgr = self.classifier.team_colors_bgr
        n_locked = len(self.classifier.id_team_locked)
        calib_pct = min(1., self.calib_frames / self.MAX_CALIB)
        
        return self.dashboard.render(
            self.possession, t_bgr, self.fps_calc,
            self.classifier.calibrated,
            n_locked, calib_pct
        )

    def get_stats(self):
        """
        Retourne les statistiques finales.
        
        Returns:
            dict: Statistiques complètes
        """
        p1t, p2t = self.possession.get_time_possession()
        p1p, p2p = self.possession.get_pass_possession()
        t1s, t2s = self.possession.get_time_str()
        f1, f2, f0 = self.possession.get_possession_frames_raw()
        
        return {
            'time_possession': (p1t, p2t),
            'pass_possession': (p1p, p2p),
            'time_str': (t1s, t2s),
            'frames': (f1, f2, f0),
            'passes': (self.possession.passes[1], 
                      self.possession.passes[2]),
            'total_frames': self.possession.total_frames,
            'video_elapsed': self.possession.get_video_elapsed()
        }