"""Minimal ordered Protobuf/WebSocket client. No debug or observer commands."""
import asyncio
import os
import subprocess
import socket
import tempfile
from pathlib import Path
from s2clientprotocol import sc2api_pb2 as sc, common_pb2 as common
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidHandshake


def find_executable(root):
    choices = list(Path(root).expanduser().glob('Versions/Base*/SC2.app/Contents/MacOS/SC2'))
    if not choices:
        raise FileNotFoundError(f'No SC2 binary under {root}/Versions; finish Battle.net installation')
    return max(choices, key=lambda p: int(p.parts[-5][4:]))


def launch(root, port, logfile, window_size=(1280, 800), window_position=None):
    executable = find_executable(root)
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', port))
        except OSError as exc:
            raise RuntimeError(f'Port {port} is already occupied. Use --attach for an existing SC2 instance.') from exc
    args = [str(executable), '-listen', '127.0.0.1', '-port', str(port),
            '-dataDir', str(Path(root).expanduser().resolve()) + os.sep,
            '-tempDir', tempfile.mkdtemp(prefix='jev-sc2-') + os.sep,
            '-displayMode', '0', '-windowwidth', str(window_size[0]),
            '-windowheight', str(window_size[1])]
    if window_position is not None:
        args += ['-windowx', str(window_position[0]), '-windowy', str(window_position[1])]
    return subprocess.Popen(args,
                            cwd=str(Path(root).expanduser()), stdout=logfile, stderr=logfile)


class SC2:
    def __init__(self, ws):
        self.ws, self.counter = ws, 0
        self.status = None
        self.lock = asyncio.Lock()

    @classmethod
    async def connect(cls, port, timeout=90, process=None):
        deadline = asyncio.get_running_loop().time()+timeout
        while True:
            if process is not None and process.poll() is not None:
                raise RuntimeError(f'SC2 exited before API connection (code {process.returncode}); inspect sc2.log and Blizzard crash report')
            try:
                return cls(await connect(f'ws://127.0.0.1:{port}/sc2api', max_size=32*1024*1024,
                                         ping_interval=None, open_timeout=2, proxy=None))
            except (OSError, TimeoutError, InvalidHandshake):
                if asyncio.get_running_loop().time() >= deadline:
                    raise TimeoutError(f'SC2 API not available on localhost:{port}')
                await asyncio.sleep(0.5)

    async def request(self, name, body):
        allowed = {'ping', 'create_game', 'join_game', 'game_info', 'data', 'observation',
                   'query', 'action', 'save_replay', 'available_maps', 'leave_game', 'quit'}
        if name not in allowed:
            raise ValueError(f'Forbidden SC2 request: {name}')
        async with self.lock:
            self.counter += 1
            req = sc.Request(id=self.counter, **{name: body})
            await self.ws.send(req.SerializeToString())
            reply = sc.Response.FromString(await asyncio.wait_for(self.ws.recv(), 120))
            self.status = reply.status
            if reply.error:
                raise RuntimeError('; '.join(reply.error))
            if reply.HasField('id') and reply.id != req.id:
                raise RuntimeError('SC2 response ID mismatch')
            result = getattr(reply, name)
            if 'error' in result.DESCRIPTOR.fields_by_name and result.HasField('error'):
                raise RuntimeError(f'{name}: {result}')
            return result

    async def start(self, map_path, opponent=False):
        if self.status == sc.in_game:
            await self.request('leave_game', sc.RequestLeaveGame())
        players = [sc.PlayerSetup(type=sc.Participant)]
        if opponent:
            players.append(sc.PlayerSetup(type=sc.Computer, race=common.Zerg, difficulty=sc.VeryEasy))
        await self.request('create_game', sc.RequestCreateGame(
            local_map=sc.LocalMap(map_path=Path(map_path).name,
                                 map_data=Path(map_path).expanduser().read_bytes()),
            player_setup=players, disable_fog=False, realtime=True))
        return await self.request('join_game', sc.RequestJoinGame(
            race=common.Terran, player_name='Jev', options=sc.InterfaceOptions(
                raw=True, score=True, show_cloaked=False, show_burrowed_shadows=False,
                show_placeholders=False, raw_crop_to_playable_area=True)))

    async def observe(self):
        return await self.request('observation', sc.RequestObservation(disable_fog=False))
