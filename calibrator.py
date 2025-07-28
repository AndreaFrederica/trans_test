# ------ calibrator.py ------
"""
Module to compute true mapping and homography for calibration,
and apply user-adjusted rotation axis offsets.
"""
import numpy as np
import cv2

def true_mapping(x: float, y: float,
                 screen_w: int, screen_h: int,
                 pan_range: tuple[float,float],
                 tilt_range: tuple[float,float],
                 pan_offset: float = 0.0,
                 tilt_offset: float = 0.0) -> tuple[float,float]:
    """
    Simulated mapping from image pixel (x,y) to gimbal angles (pan, tilt),
    with axis orientation offsets applied.
    """
    pan_min, pan_max = pan_range
    tilt_min, tilt_max = tilt_range
    # Linear base mapping
    pan = pan_min + (x / screen_w) * (pan_max - pan_min)
    tilt = tilt_min + ((screen_h - y) / screen_h) * (tilt_max - tilt_min)
    # Apply user-defined axis offsets
    pan += pan_offset
    tilt += tilt_offset
    return pan, tilt


def compute_homography(img_pts: list[tuple[float,float]],
                       pan_tilt_pts: list[tuple[float,float]]) -> np.ndarray:
    """
    Compute homography matrix H such that [pan, tilt, 1].T ~ H * [x, y, 1].T
    """
    src = np.array(img_pts, dtype=np.float32)
    dst = np.array(pan_tilt_pts, dtype=np.float32)
    H, _ = cv2.findHomography(src, dst)
    return H