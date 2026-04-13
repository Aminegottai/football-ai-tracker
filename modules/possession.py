import numpy as np
from collections import deque
import config

# ══════════════════════════════════════════════════════
# POSSESSION TRACKER
# ══════════════════════════════════════════════════════

class PossessionTracker:
    """
    Suivi de la possession du ballon basé sur les frames vid��o.
    Calcul des statistiques : temps de possession, passes, etc.
    
    Attributes:
        fps (float): Frames par seconde
        possession_frames (dict): Frames par équipe
        passes (dict): Nombre de passes par équipe
    """
    
    def __init__(self, fps=30.0):
        self.fps = fps
        self.spf = 1.0 / fps  # secondes par frame

        # Possession en frames
        self.possession_frames = {1: 0, 2: 0, 0: 0}

        # Stabilisation possession
        self.CONFIRM_FRAMES = config.POSSESSION_CONFIRM_FRAMES
        self.current_team = 0
        self.candidate_team = 0
        self.candidate_count = 0

        # Passes
        self.passes = {1: 0, 2: 0}
        self.MIN_HOLD_FRAMES = config.POSSESSION_MIN_HOLD_FRAMES
        self.hold_frames = {1: 0, 2: 0}

        # Dernier détenteur
        self.last_confirmed_team = 0
        self.last_confirmed_frame = 0

        # Distance ballon-joueur
        self.MAX_DIST_PX = config.POSSESSION_MAX_DIST_PX

        # Fenêtre glissante
        window_frames_count = int(fps * config.POSSESSION_WINDOW_SECONDS)
        self.window_frames = deque(maxlen=window_frames_count)

        # Historique
        self.hist_time_t1 = deque(maxlen=300)
        self.hist_time_t2 = deque(maxlen=300)
        self.hist_pass_t1 = deque(maxlen=300)
        self.hist_pass_t2 = deque(maxlen=300)

        self.total_frames = 0

    def _closest_player_team(self, ball_box, player_dets):
        """
        Retourne l'équipe du joueur le plus proche du ballon.
        
        Args:
            ball_box: Boîte englobante du ballon
            player_dets: Liste des détections de joueurs
            
        Returns:
            tuple: (team, distance)
        """
        if ball_box is None or not player_dets:
            return 0, float('inf')

        bx1, by1, bx2, by2 = ball_box
        bcx = (bx1 + bx2) / 2.0
        bcy = (by1 + by2) / 2.0

        min_dist = float('inf')
        best_team = 0

        for det in player_dets:
            team = det.get('team', 0)
            if team == 0:
                continue
            
            x1, y1, x2, y2 = det['box']
            px = (x1 + x2) / 2.0
            py = float(y2)
            dist = np.sqrt((bcx - px) ** 2 + (bcy - py) ** 2)
            
            if dist < min_dist:
                min_dist = dist
                best_team = team

        if min_dist > self.MAX_DIST_PX:
            return 0, min_dist
        
        return best_team, min_dist

    def _stabilize_team(self, raw_team):
        """
        Évite le flickering avec stabilisation temporelle.
        
        Args:
            raw_team: Équipe détectée brute
            
        Returns:
            int: Équipe confirmée
        """
        if raw_team == 0:
            self.candidate_team = 0
            self.candidate_count = 0
            return self.current_team

        if raw_team == self.current_team:
            self.candidate_team = 0
            self.candidate_count = 0
            return self.current_team

        if raw_team == self.candidate_team:
            self.candidate_count += 1
        else:
            self.candidate_team = raw_team
            self.candidate_count = 1

        if self.candidate_count >= self.CONFIRM_FRAMES:
            self.current_team = self.candidate_team
            self.candidate_team = 0
            self.candidate_count = 0

        return self.current_team

    def _update_passes(self, confirmed_team):
        """
        Détection des passes basée sur les changements d'équipe.
        
        Args:
            confirmed_team: Équipe confirmée actuellement en possession
        """
        if confirmed_team > 0:
            self.hold_frames[confirmed_team] += 1
            
            other = 2 if confirmed_team == 1 else 1
            self.hold_frames[other] = 0

            if (self.last_confirmed_team > 0 and
                    confirmed_team != self.last_confirmed_team):
                prev = self.last_confirmed_team
                frames_held = self.total_frames - self.last_confirmed_frame
                
                if frames_held >= self.MIN_HOLD_FRAMES:
                    self.passes[prev] += 1
                    if config.DEBUG_MODE:
                        print(f"  [PASSE] T{prev}→T{confirmed_team} "
                              f"({frames_held} frames tenues)")

            if confirmed_team != self.last_confirmed_team:
                self.last_confirmed_team = confirmed_team
                self.last_confirmed_frame = self.total_frames

    def update(self, ball_box, player_dets, frame_w, frame_h):
        """
        Mise à jour du tracker (appelée 1 fois par frame).
        
        Args:
            ball_box: Boîte englobante du ballon
            player_dets: Détections de joueurs
            frame_w: Largeur du frame
            frame_h: Hauteur du frame
        """
        self.total_frames += 1

        raw_team, dist = self._closest_player_team(ball_box, player_dets)
        confirmed_team = self._stabilize_team(raw_team)

        if confirmed_team > 0:
            self.possession_frames[confirmed_team] += 1
        else:
            self.possession_frames[0] += 1

        self.window_frames.append(confirmed_team)
        self._update_passes(confirmed_team)

        # Historique graphique
        if self.total_frames % 20 == 0:
            p1t, p2t = self.get_time_possession()
            p1p, p2p = self.get_pass_possession()
            self.hist_time_t1.append(p1t)
            self.hist_time_t2.append(p2t)
            self.hist_pass_t1.append(p1p)
            self.hist_pass_t2.append(p2p)

    def get_time_possession(self):
        """Possession en % de temps."""
        f1 = self.possession_frames[1]
        f2 = self.possession_frames[2]
        total = f1 + f2
        if total == 0:
            return 50.0, 50.0
        return round(f1 / total * 100, 1), round(f2 / total * 100, 1)

    def get_pass_possession(self):
        """Passes en % du total."""
        p1 = self.passes[1]
        p2 = self.passes[2]
        total = p1 + p2
        if total == 0:
            return 50.0, 50.0
        return round(p1 / total * 100, 1), round(p2 / total * 100, 1)

    def get_window_possession(self):
        """Possession sur fenêtre glissante (dernières 30s)."""
        data = list(self.window_frames)
        t1 = data.count(1)
        t2 = data.count(2)
        total = t1 + t2
        if total == 0:
            return 50.0, 50.0
        return round(t1 / total * 100, 1), round(t2 / total * 100, 1)

    def get_time_str(self):
        """Temps en format MM:SS."""
        s1 = self.possession_frames[1] * self.spf
        s2 = self.possession_frames[2] * self.spf
        
        def fmt(s):
            return f"{int(s // 60):02d}:{int(s % 60):02d}"
        
        return fmt(s1), fmt(s2)

    def get_video_elapsed(self):
        """Temps vidéo écoulé en secondes."""
        return self.total_frames * self.spf

    def get_possession_frames_raw(self):
        """Frames brutes (debug)."""
        return (self.possession_frames[1],
                self.possession_frames[2],
                self.possession_frames[0])