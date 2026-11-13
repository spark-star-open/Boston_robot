"""Draw an illustrative parallel-jaw gripper."""
import cv2
import numpy as np

def draw(img, pose, clearance=5, colour=(60, 200, 60)):
    c, vl, vs = pose["centre"], pose["v_long"], pose["v_short"]
    L, W = pose["length"], pose["width"]

    def pt(a, b):
        return tuple(np.round(c + vl * a + vs * b).astype(int))

    cv2.line(img, pt(-L / 2, 0), pt(L / 2, 0), (255, 170, 60), 2)
    cv2.line(img, pt(0, -W / 2), pt(0, W / 2), (90, 90, 240), 2)
    half, reach = W / 2 + clearance, L / 2 * 0.60
    for s in (-1, 1):
        cv2.line(img, pt(-reach, s * half), pt(reach, s * half), colour, 4)
    wrist = -reach - 22
    cv2.line(img, pt(wrist, -half), pt(wrist, half), colour, 4)
    cv2.line(img, pt(wrist, 0), pt(-reach, 0), colour, 4)
    cv2.circle(img, tuple(np.round(c).astype(int)), 6, (0, 0, 255), -1)
    return img

