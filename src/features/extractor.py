"""
特征提取模块 - Feature Extraction Module
对 MediaPipe 输出的21个关键点进行归一化、距离特征和角度特征提取
"""

import math
import numpy as np
from typing import List, Tuple


class FeatureExtractor:
    """
    手势特征提取器

    提取三类特征:
    1. 归一化关键点坐标（相对手腕）
    2. 指尖间距离特征
    3. 关节弯曲角度特征
    """

    # 手指关节定义: (指尖, 远端指间关节, 近端指间关节, 掌指关节)
    FINGER_JOINTS = {
        "thumb":   [4, 3, 2, 1],    # 拇指: TIP, IP, MCP, CMC
        "index":   [8, 7, 6, 5],    # 食指
        "middle":  [12, 11, 10, 9], # 中指
        "ring":    [16, 15, 14, 13],# 无名指
        "pinky":   [20, 19, 18, 17],# 小指
    }

    # 指尖索引
    FINGERTIPS = [4, 8, 12, 16, 20]

    def __init__(self):
        pass

    # ---------- 归一化 ----------

    def normalize(self, landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        以手腕为原点进行归一化，消除手部位置影响

        Args:
            landmarks: 21个关键点 [(x, y, z), ...]

        Returns:
            归一化后的 (21, 3) 数组
        """
        wrist = np.array(landmarks[0])
        normalized = np.array(landmarks) - wrist
        return normalized

    def normalize_scale(self, landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        以手腕为原点，并以手腕到中指MCP距离进行尺度归一化

        Args:
            landmarks: 21个关键点

        Returns:
            归一化后的 (21, 3) 数组
        """
        wrist = np.array(landmarks[0])
        middle_mcp = np.array(landmarks[9])
        scale = np.linalg.norm(middle_mcp - wrist)
        if scale < 1e-6:
            scale = 1.0
        normalized = (np.array(landmarks) - wrist) / scale
        return normalized

    # ---------- 距离特征 ----------

    def fingertip_distances(self, landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        计算五指指尖两两之间的距离

        Args:
            landmarks: 21个关键点

        Returns:
            10个距离值 (C(5,2) = 10)
        """
        tips = [landmarks[i] for i in self.FINGERTIPS]
        distances = []
        for i in range(len(tips)):
            for j in range(i + 1, len(tips)):
                d = math.dist(tips[i], tips[j])
                distances.append(d)
        return np.array(distances)

    def fingertip_to_wrist_distances(self, landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        计算各指尖到手腕的距离

        Returns:
            5个距离值
        """
        wrist = landmarks[0]
        distances = []
        for i in self.FINGERTIPS:
            d = math.dist(landmarks[i], wrist)
            distances.append(d)
        return np.array(distances)

    # ---------- 角度特征 ----------

    def joint_angle(self, a: Tuple[float, float, float],
                     b: Tuple[float, float, float],
                     c: Tuple[float, float, float]) -> float:
        """
        计算以b为顶点的三点夹角 (a-b-c)

        Returns:
            角度（度）
        """
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return math.degrees(math.acos(cos_angle))

    def finger_angles(self, landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
        """
        计算各手指的关节弯曲角度

        每根手指计算2个角度:
        - PIP角度 (指尖-DIP关节-PIP关节)
        - MCP角度 (DIP关节-PIP关节-MCP关节)

        Returns:
            10个角度值 (5根手指 x 2个关节)
        """
        angles = []
        for finger_name, joints in self.FINGER_JOINTS.items():
            # PIP角度: joints[0] - joints[1] - joints[2]
            ang_pip = self.joint_angle(
                landmarks[joints[0]],  # 指尖
                landmarks[joints[1]],  # DIP
                landmarks[joints[2]],  # PIP
            )
            # MCP角度: joints[1] - joints[2] - joints[3]
            ang_mcp = self.joint_angle(
                landmarks[joints[1]],  # DIP
                landmarks[joints[2]],  # PIP
                landmarks[joints[3]],  # MCP
            )
            angles.extend([ang_pip, ang_mcp])
        return np.array(angles)

    # ---------- 综合特征 ----------

    def extract(self, landmarks: List[Tuple[float, float, float]],
                feature_set: str = "all") -> np.ndarray:
        """
        提取综合特征向量

        Args:
            landmarks: 21个关键点
            feature_set: 特征集类型
                - "distance": 仅距离特征 (15维)
                - "angle":    仅角度特征 (10维)
                - "all":      全部特征 (25维)

        Returns:
            特征向量
        """
        normalized = self.normalize_scale(landmarks)
        features = []

        if feature_set in ("distance", "all"):
            tip_dist = self.fingertip_distances(landmarks)          # 10维
            wrist_dist = self.fingertip_to_wrist_distances(landmarks) # 5维
            features.extend(tip_dist.tolist())
            features.extend(wrist_dist.tolist())

        if feature_set in ("angle", "all"):
            angles = self.finger_angles(landmarks)  # 10维
            features.extend(angles.tolist())

        return np.array(features, dtype=np.float32)
