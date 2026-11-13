"""PCA pose in image coordinates (x, y)."""
import numpy as np

def pca_pose(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 80:
        return None
    pts = np.column_stack([xs, ys]).astype(np.float64)      # (x, y)，见底注
    centre = pts.mean(axis=0)
    q = pts - centre
    vals, vecs = np.linalg.eigh(np.cov(q.T))
    order = vals.argsort()[::-1]
    v_long, v_short = vecs[:, order[0]], vecs[:, order[1]]
    if v_long[1] < 0:
        v_long = -v_long
    angle = np.degrees(np.arctan2(v_long[1], v_long[0]))
    if angle > 90:
        angle -= 180
    return dict(centre=centre, v_long=v_long, v_short=v_short,
                length=np.ptp(q @ v_long), width=np.ptp(q @ v_short), angle=angle)

