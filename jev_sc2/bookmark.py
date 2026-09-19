"""Opt-in infrastructure recovery using ordinary in-memory save/load, never tactics."""
import time
from s2clientprotocol import sc2api_pb2 as sc, data_pb2 as data


class BookmarkRecovery:
    def __init__(self, client, catalog, log, enabled=False):
        self.client, self.log, self.enabled = client, log, enabled
        self.structures = {u.unit_id for u in catalog.units if data.Structure in u.attributes}
        self.saved_loop = None
        self.saved_at = float('-inf')
        self.attempted = False

    async def maybe_save(self, observation):
        if not self.enabled or self.attempted or time.monotonic()-self.saved_at < 45:
            return
        if self.client.status != sc.in_game or observation.player_result:
            return
        if not any(u.alliance == 1 and u.health > 0 for u in observation.observation.raw_data.units):
            return
        try:
            await self.client.request('quick_save', sc.RequestQuickSave())
        except Exception as exc:
            self.enabled = False
            self.log('api_bookmark_unavailable', error=str(exc))
            return
        self.saved_at = time.monotonic()
        self.saved_loop = observation.observation.game_loop
        self.log('api_bookmark_saved', loop=self.saved_loop)

    async def recover(self, observation):
        results = observation.player_result
        # Narrow observed anomaly: every player loses while our buildings remain.
        # A victory, mixed result, empty force, or second failure is never restored.
        if (not self.enabled or self.attempted or self.saved_loop is None or
                self.client.status != sc.ended or len(results) < 2 or
                any(r.result != sc.Defeat for r in results) or
                not any(u.alliance == 1 and u.unit_type in self.structures and
                        u.health > 0 and u.build_progress >= 1
                        for u in observation.observation.raw_data.units)):
            return False
        self.attempted = True
        self.log('api_termination_before_restore', loop=observation.observation.game_loop,
                 bookmark_loop=self.saved_loop,
                 players=[{'player':r.player_id,'result':sc.Result.Name(r.result)} for r in results])
        try:
            await self.client.request('quick_load', sc.RequestQuickLoad())
            restored = await self.client.observe()
            if (self.client.status != sc.in_game or restored.player_result or
                    not any(u.alliance == 1 for u in restored.observation.raw_data.units)):
                raise RuntimeError('Bookmark did not restore an active owned force')
        except Exception as exc:
            self.log('api_bookmark_restore_failed', error=str(exc))
            return False
        self.log('api_bookmark_restored', loop=restored.observation.game_loop,
                 bookmark_loop=self.saved_loop)
        return True
