import json
import tkinter as tk

from websockets.sync.client import connect


class WebappDummy:
    def __init__(self):
        with connect("ws://localhost:8765") as self._websocket:
            self._gui()

    def _send_command(self, topic: str) -> None:
        command = {"topic": topic}
        self._websocket.send(json.dumps(command))
        message = self._websocket.recv()
        print(f"Received: {message}")

    def _gui(self):
        root = tk.Tk()
        root.title("Timer und Aktionen")

        shutdown_group = tk.LabelFrame(root, text="Shutdown")
        shutdown_group.pack(padx=10, pady=5, fill="both", expand=1)
        shutdown_pause_button = tk.Button(shutdown_group, text="Timer pausieren", command=lambda: self._send_command(topic="pause_shutdown_timer"))
        shutdown_pause_button.pack(padx=5, pady=5)
        shutdown_resume_button = tk.Button(shutdown_group, text="Timer fortsetzen", command=lambda: self._send_command(topic="resume_shutdown_timer"))
        shutdown_resume_button.pack(padx=5, pady=5)
        shutdown_now_button = tk.Button(shutdown_group, text="Shutdown sofort", command=lambda: self._send_command(topic="shutdown_now"))
        shutdown_now_button.pack(padx=5, pady=5)

        backup_group = tk.LabelFrame(root, text="Backup")
        backup_group.pack(padx=10, pady=5, fill="both", expand=1)
        backup_pause_button = tk.Button(backup_group, text="Timer pausieren", command=lambda: self._send_command(topic="pause_backup_timer"))
        backup_pause_button.pack(padx=5, pady=5)
        backup_resume_button = tk.Button(backup_group, text="Timer fortsetzen", command=lambda: self._send_command(topic="resume_backup_timer"))
        backup_resume_button.pack(padx=5, pady=5)
        backup_cancel_button = tk.Button(backup_group, text="Timer abbrechen", command=lambda: self._send_command(topic="cancel_backup_timer"))
        backup_cancel_button.pack(padx=5, pady=5)
        backup_now_button = tk.Button(backup_group, text="Backup jetzt", command=lambda: self._send_command(topic="backup_now"))
        backup_now_button.pack(padx=5, pady=5)

        root.mainloop()


if __name__ == "__main__":
    WebappDummy()
