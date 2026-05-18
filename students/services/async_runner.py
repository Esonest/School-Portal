import threading


def run_async(func, *args, **kwargs):
    """
    Lightweight background task runner for Render free tier
    """

    thread = threading.Thread(
        target=func,
        args=args,
        kwargs=kwargs,
        daemon=True
    )

    thread.start()