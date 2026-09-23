import os
import time


class DiscordRPC:
    def __init__(self):
        self.client_id = os.environ.get("ANICLI_DISCORD_CLIENT_ID", "1221769634938683402")
        self.rpc = None
        self.start_time = None

    def connect(self):
        try:
            from pypresence import Presence
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.start_time = int(time.time())
            self.set_idle()
        except Exception:
            self.rpc = None

    def set_idle(self):
        self._update("Memilih anime", "anicli-id")

    def set_searching(self, query):
        self._update("Mencari anime", query[:128])

    def set_watching(self, anime_title, episode_num, source=""):
        state = f"Episode {episode_num}"
        if source:
            state = f"Episode {episode_num} · {source}"
        self._update(state, anime_title[:128])

    def _update(self, state, details):
        if not self.rpc:
            return
        try:
            self.rpc.update(state=state[:128], details=details[:128], start=self.start_time)
        except Exception:
            pass

    def close(self):
        if not self.rpc:
            return
        try:
            self.rpc.close()
        except Exception:
            pass


discord_rpc = DiscordRPC()
