import io
from threading import Lock
from fastapi import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PLOT_LOCK = Lock()

def render_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Response(buf.read(), media_type="image/png")
