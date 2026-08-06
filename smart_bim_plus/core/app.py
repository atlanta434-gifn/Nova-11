import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from core.database import DatabaseManager
from core.ai_engine import AIEngine
from core.drone_handler import DroneHandler
from ui.main_window import SmartBIMMainWindow


def patch_matplotlib_arabic():
    try:
        import matplotlib.axes
        import arabic_reshaper
        from bidi.algorithm import get_display

        original_text = matplotlib.axes.Axes.text
        original_set_title = matplotlib.axes.Axes.set_title

        def patched_text(self, x, y, s, fontdict=None, **kwargs):
            if isinstance(s, str):
                s = get_display(arabic_reshaper.reshape(s))
            return original_text(self, x, y, s, fontdict=fontdict, **kwargs)

        def patched_set_title(self, label, fontdict=None, loc=None, pad=None, *, y=None, **kwargs):
            if isinstance(label, str):
                label = get_display(arabic_reshaper.reshape(label))
            return original_set_title(self, label, fontdict=fontdict, loc=loc, pad=pad, y=y, **kwargs)

        matplotlib.axes.Axes.text = patched_text
        matplotlib.axes.Axes.set_title = patched_set_title
        logging.getLogger("SmartBIM.App").info("Matplotlib Arabic patch applied successfully.")
    except ImportError:
        logging.getLogger("SmartBIM.App").warning("arabic-reshaper or python-bidi not installed. Arabic text may not render correctly in Matplotlib.")

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "smart_bim.log"), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_stylesheet(app):
    style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "themes", "dark.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        logging.warning("Stylesheet not found at %s", style_path)


def main():
    setup_logging()
    logger = logging.getLogger("SmartBIM.App")
    logger.info("Starting NOVA...")

    patch_matplotlib_arabic()

    app = QApplication(sys.argv)
    app.setApplicationName("NOVA")
    app.setOrganizationName("DSBA")

    load_stylesheet(app)

    # splash = QSplashScreen(QPixmap("assets/splash.png"))
    # splash.show()
    # app.processEvents()

    logger.info("Initializing core modules...")
    db = DatabaseManager("smart_bim.db")
    ai = AIEngine("ai_models")
    drone = DroneHandler()

    main_window = SmartBIMMainWindow(db, ai, drone)
    main_window.show()

    # splash.finish(main_window)
    logger.info("NOVA is ready")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
