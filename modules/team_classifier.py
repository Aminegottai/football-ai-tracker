import cv2
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, deque
import config

# ══════════════════════════════════════════════════════
# TEAM CLASSIFIER - GMM
# ══════════════════════════════════════════════════════

class TeamClassifierGMM:
    """
    Classification des équipes basée sur les couleurs de maillots.
    Utilise un modèle Gaussian Mixture Model (GMM).
    
    Attributes:
        gmm: Modèle GMM
        scaler: StandardScaler pour normalisation
        calibrated (bool): Flag de calibration
        id_team_locked (dict): Teams confirmées pour chaque ID
    """
    
    def __init__(self):
        self.gmm = None
        self.scaler = StandardScaler()
        self.calibrated = False
        self.all_colors = []
        self.id_votes = defaultdict(lambda: deque(maxlen=60))
        self.id_team_locked = {}
        self.LOCK_THRESHOLD = config.GMM_LOCK_THRESHOLD
        self.MIN_VOTES = config.GMM_MIN_VOTES
        self.team_colors_hsv = {}
        self.team_colors_bgr = {}

    def collect_color(self, color):
        """Collecte une couleur pour la calibration."""
        self.all_colors.append(color)

    def fit(self):
        """
        Entraîne le modèle GMM sur les couleurs collectées.
        
        Returns:
            bool: True si calibration réussie
        """
        if len(self.all_colors) < config.CALIB_MIN_COLORS:
            return False
        
        colors = np.array(self.all_colors, dtype=np.float32)
        colors_norm = self.scaler.fit_transform(colors)
        
        self.gmm = GaussianMixture(
            n_components=config.GMM_N_COMPONENTS,
            covariance_type=config.GMM_COVARIANCE_TYPE,
            n_init=config.GMM_N_INIT,
            max_iter=config.GMM_MAX_ITER,
            random_state=42,
            reg_covar=config.GMM_REG_COVAR
        )
        self.gmm.fit(colors_norm)
        
        centers = self.scaler.inverse_transform(self.gmm.means_)
        self.team_colors_hsv = {1: centers[0], 2: centers[1]}
        
        for tid, hsv in self.team_colors_hsv.items():
            px = np.array([[[int(np.clip(hsv[0], 0, 179)),
                             int(np.clip(hsv[1], 0, 255)),
                             int(np.clip(hsv[2], 0, 255))]]], 
                          dtype=np.uint8)
            bgr = cv2.cvtColor(px, cv2.COLOR_HSV2BGR)[0][0]
            self.team_colors_bgr[tid] = tuple(map(int, bgr))
        
        self.calibrated = True
        
        if config.VERBOSE:
            print(f"\n✅ GMM Calibré!")
            for tid in [1, 2]:
                print(f"  Equipe {tid}: BGR={self.team_colors_bgr[tid]}")
        
        return True

    def predict_stable(self, track_id, color):
        """
        Prédiction stable d'équipe avec lissage temporel.
        
        Args:
            track_id: ID du joueur
            color: Couleur HSV du maillot
            
        Returns:
            tuple: (team, confidence)
        """
        if track_id in self.id_team_locked:
            return self.id_team_locked[track_id], 1.0
        
        if not self.calibrated:
            return 0, 0.0
        
        norm = self.scaler.transform([color])
        probs = self.gmm.predict_proba(norm)[0]
        team = int(np.argmax(probs)) + 1
        
        self.id_votes[track_id].append(team)
        votes = list(self.id_votes[track_id])
        c1, c2 = votes.count(1), votes.count(2)
        total = len(votes)
        team_v = 1 if c1 >= c2 else 2
        conf_v = max(c1, c2) / total
        
        if total >= self.MIN_VOTES and conf_v >= self.LOCK_THRESHOLD:
            self.id_team_locked[track_id] = team_v
        
        return team_v, conf_v