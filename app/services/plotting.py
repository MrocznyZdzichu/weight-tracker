import io
from threading import RLock
from fastapi import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PLOT_LOCK = RLock()

def render_png(fig):
    buf = io.BytesIO()
    with PLOT_LOCK:
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    buf.seek(0)
    return Response(buf.read(), media_type="image/png")
