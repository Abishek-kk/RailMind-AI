"""Extract features from poses for ML model"""

import numpy as np

class FeatureExtractor:
    """Extracts features from pose keypoints"""
    
    def __init__(self):
        """Initialize feature extractor"""
        self.joint_indices = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (5, 6), (6, 7), (7, 8), (8, 9)
        ]
    
    def extract_features(self, pose_keypoints):
        """Extract numerical features from pose"""
        if pose_keypoints is None:
            return np.zeros(16, dtype=float)

        arr = np.asarray(pose_keypoints, dtype=float)
        if arr.ndim == 1 and arr.size % 2 == 0:
            arr = arr.reshape(-1, 2)
        elif arr.ndim == 1 and arr.size % 3 == 0:
            arr = arr.reshape(-1, 3)
        elif arr.ndim > 2:
            arr = arr.reshape(arr.shape[0], -1)

        if arr.size == 0:
            return np.zeros(16, dtype=float)

        coordinates = arr[:, :2]
        mean_x, mean_y = np.nanmean(coordinates, axis=0)
        std_x, std_y = np.nanstd(coordinates, axis=0)
        distances = self.compute_distances(coordinates)
        angles = self.compute_skeleton_angles(coordinates)

        features = np.concatenate(
            [np.array([mean_x, mean_y, std_x, std_y], dtype=float), distances, angles]
        )
        return self.normalize_features(features)
    
    def normalize_features(self, features):
        """Normalize features to standard range"""
        if features.size == 0:
            return features
        max_val = np.nanmax(np.abs(features))
        if max_val == 0:
            return features
        return features / max_val
    
    def compute_skeleton_angles(self, keypoints):
        """Compute angles between body joints"""
        angles = []
        for i, j in self.joint_indices:
            if i >= keypoints.shape[0] or j >= keypoints.shape[0]:
                angles.append(0.0)
                continue
            p1 = keypoints[i]
            p2 = keypoints[j]
            vector = p2 - p1
            if np.linalg.norm(vector) == 0:
                angles.append(0.0)
                continue
            angle = np.degrees(np.arctan2(vector[1], vector[0]))
            angles.append(angle / 180.0)
        return np.array(angles, dtype=float)
    
    def compute_distances(self, keypoints):
        """Compute distances between key points"""
        if keypoints.shape[0] < 2:
            return np.zeros(4, dtype=float)
        distances = np.linalg.norm(keypoints - np.mean(keypoints, axis=0), axis=1)
        return np.array(
            [np.nanmean(distances), np.nanstd(distances), np.nanmin(distances), np.nanmax(distances)],
            dtype=float,
        )
