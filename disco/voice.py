from disco.gateway.packets import OPCode
from disco.types.channel import Channel
from telecom import TelecomConnection, AvConvPlayable


class VoiceConnection(object):
    def __init__(self, client, guild_id):
        self.client = client
        self.guild_id = guild_id
        self.channel_id = None
        self._conn = None
        self._voice_server_update_listener = self.client.events.on(
            'VoiceServerUpdate',
            self._on_voice_server_update,
        )

        self._mute = False
        self._deaf = False

    @property
    def mute(self):
        return self._mute

    @property
    def deaf(self):
        return self._deaf

    @mute.setter
    def mute(self, value):
        if value is self._mute:
            return

        self._mute = value
        self._send_voice_state_update()

    @deaf.setter
    def deaf(self, value):
        if value is self._deaf:
            return

        self._deaf = value
        self._send_voice_state_update()

    @classmethod
    def from_channel(self, channel):
        assert channel.is_voice, 'Cannot connect to a non voice channel'
        conn = VoiceConnection(channel.client, channel.guild_id)
        conn.connect(channel.id)
        return conn

    def set_channel(self, channel_or_id):
        if channel_or_id and isinstance(channel_or_id, Channel):
            channel_or_id = channel_or_id.id

        self.channel_id = channel_or_id
        self._send_voice_state_update()

    def connect(self, channel_id):
        assert self._conn is None, 'Already connected'

        self.set_channel(channel_id)

        self._conn = TelecomConnection(
            self.client.state.me.id,
            self.guild_id,
            self.client.gw.session_id,
        )

    def disconnect(self):
        assert self._conn is not None, 'Not connected'

        # Send disconnection
        self.set_channel(None)

        # Delete our connection so it will get GC'd
        del self._conn
        self._conn = None

    def play_file(self, url):
        self._conn.play(AvConvPlayable(url))

    def _on_voice_server_update(self, event):
        if not self._conn or event.guild_id != self.guild_id:
            return

        self._conn.update_server_info(event.endpoint, event.token)

    def _send_voice_state_update(self):
        self.client.gw.send(OPCode.VOICE_STATE_UPDATE, {
            'self_mute': self._mute,
            'self_deaf': self._deaf,
            'self_video': False,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
        })
