"""Audio commands cog for core audio playback features."""

import discord
import os
import asyncio
import time
import subprocess
import json
from discord import app_commands
from discord.ext import commands
from collections import deque
from checks import interaction_has_allowed_role

# ----------- Classes for interactions -----------
class ChooseTrackView(discord.ui.View):
    """Ephemeral view to pick one track when multiple files share the same name"""

    def __init__(self, cog, paths, start_at, guild, channel, user, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.paths = paths
        self.start_at = start_at
        self.guild = guild
        self.channel = channel
        self.user = user
        for i, path in enumerate(paths[:25]):
            label = path if len(path) <= 80 else path[:77] + "..."
            self.add_item(ChooseTrackButton(label=label, path=path, row=i // 5))

    async def on_timeout(self):
        self.stop()


class ChooseTrackButton(discord.ui.Button):
    def __init__(self, label, path, row=0):
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=row)
        self._path = path

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user != view.user:
            await interaction.response.send_message("Only the person who requested play can choose.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        # Validate start_at if provided
        if view.start_at is not None:
            parsed = view.cog.parse_timestamp(view.start_at)
            if parsed is None or parsed < 0:
                await interaction.followup.send(
                    "Invalid timestamp. Use e.g. `1:15`, `1:15:30`, or `75` (seconds).",
                    ephemeral=True,
                )
                return
        success, msg = await view.cog._queue_single_track(
            view.guild, view.channel, view.user, self._path, view.start_at
        )
        await interaction.followup.send(msg)
        view.stop()


class FolderError(Exception):
    """Raised for invalid/out-of-bounds folder requests in the audio browser"""
    pass


class AudioBrowserView(discord.ui.LayoutView):
    """
    Generates the folder browser for the /audio command.
    Every interaction builds a brand new AudioBrowserView scoped to the new location
    """

    # Longer folder names are truncated when they exceed this # of characters
    FOLDER_NAME_MAX = 20
    # How many seconds until the bot removes the audio viewer
    AUDIO_BROWSER_TIMEOUT = 60

    def __init__(self, cog: "AudioCog", opt_dir: str | None, page: int, page_size: int, *, timeout: float = AUDIO_BROWSER_TIMEOUT):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.opt_dir = opt_dir
        self.page = page
        self.page_size = page_size
        self.message: discord.Message | None = None

        self.folders, self.files = cog.scan_audio_folder(opt_dir)
        self.pages = [self.files[i:i + page_size] for i in range(0, len(self.files), page_size)] or [[]]
        self.total_pages = len(self.pages)
        # Clamps in case of a stale page index
        self.page = max(0, min(self.page, self.total_pages - 1))

        self._build()

    @classmethod
    def _truncate(cls, name: str) -> str:
        limit = cls.FOLDER_NAME_MAX
        return name if len(name) <= limit else name[: limit - 3] + "..."

    # Layout build
    def _build(self):
        display = (lambda p: os.path.basename(p)) if self.opt_dir else (lambda p: p)
        start_index = self.page * self.page_size

        lines = [
            f"{start_index + i + 1}. `{display(name)}`"
            for i, name in enumerate(self.pages[self.page])
        ]

        title_prefix = f'Audio files in "{self.opt_dir}"' if self.opt_dir else "Audio files"

        # Folder buttons
        max_folder_slots = 20
        overflow = len(self.folders) > max_folder_slots
        shown_folders = self.folders[:max_folder_slots]

        # Header, body, footer definitions
        header = f"## {title_prefix}\n-# Page {self.page + 1}/{self.total_pages}"

        if lines:
            body = "\n".join(lines)
        elif not shown_folders:
            body = "*No audio files were found in this folder.*"
        else:
            body = ""

        footer = "-# Tap a folder button to view contents | ⬆️ to go back | ⬅️ and ➡️ to switch pages"

        # Audio files as components list
        components: list = [discord.ui.TextDisplay(f"{header}\n\n{body}")]

        for i in range(0, len(shown_folders), 5):
            row_folders = shown_folders[i:i + 5]
            buttons = []
            for folder_path in row_folders:
                name = self._truncate(f"📁 {os.path.basename(folder_path)}")
                btn = discord.ui.Button(label=name, style=discord.ButtonStyle.primary)
                btn.callback = self._folder_callback(folder_path)
                buttons.append(btn)
            components.append(discord.ui.ActionRow(*buttons))

        if overflow:
            components.append(discord.ui.TextDisplay("-# …more folders not shown"))

        # Navigation row
        nav_buttons = []
        if self.opt_dir:
            parent = os.path.dirname(self.opt_dir) or None
            up_btn = discord.ui.Button(label="⬆️", style=discord.ButtonStyle.secondary)
            up_btn.callback = self._folder_callback(parent)
            nav_buttons.append(up_btn)

        if self.total_pages > 1:
            prev_btn = discord.ui.Button(
                label="⬅️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page == 0)
            )
            next_btn = discord.ui.Button(
                label="➡️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page >= self.total_pages - 1)
            )
            prev_btn.callback = self._page_callback(self.page - 1)
            next_btn.callback = self._page_callback(self.page + 1)
            nav_buttons.extend([prev_btn, next_btn])

        if nav_buttons:
            components.append(discord.ui.ActionRow(*nav_buttons))

        components.append(discord.ui.TextDisplay(footer))

        container = discord.ui.Container(
            *components,
            accent_color=discord.Color(0x5865F2)
        )
        self.add_item(container)

    # ---------- Callbacks ----------
    def _folder_callback(self, target_dir: str | None):
        async def callback(interaction: discord.Interaction):
            if not interaction_has_allowed_role(interaction):
                await interaction.response.send_message("You don't have permission to use this.", ephemeral=True)
                return
            try:
                new_view = AudioBrowserView(self.cog, target_dir, 0, self.page_size)
            except FolderError as e:
                await interaction.response.send_message(str(e), ephemeral=True)
                return
            self.stop() # kill the original
            await interaction.response.edit_message(view=new_view)
            new_view.message = await interaction.original_response()
        return callback

    def _page_callback(self, target_page: int):
        async def callback(interaction: discord.Interaction):
            if not interaction_has_allowed_role(interaction):
                await interaction.response.send_message("You don't have permission to use this.", ephemeral=True)
                return
            new_view = AudioBrowserView(self.cog, self.opt_dir, target_page, self.page_size)
            self.stop() # kill the original
            await interaction.response.edit_message(view=new_view)
            new_view.message = await interaction.original_response()
        return callback

    async def on_timeout(self):
        if self.message is None:
            return
        try:
            await self.message.edit(view=AudioSmallView())
        except discord.NotFound:
            print("[DEBUG] ERROR: Message no longer exists.")
        except discord.HTTPException as e:
            print(f"[DEBUG] ERROR: Couldn't replace timed-out message: {e}")


class AudioSmallView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "This audio browser has timed out. To continue using the audio browser, please use `/audio`."
                ),
                accent_color=discord.Color(0x5865F2)
            )
        )

# ----------- Cog for audio commands -----------
class AudioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audio_queues = {}
        self.looping = {}
        self.current_track = {}
        self.skip_requested = {}
        self.audio_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio")
        self.next_play_start_offset = {}
        self.playback_start_time = {}
        self.total_duration_seconds = {}
        self.accumulated_pause_seconds = {}
        self.pause_start_time = {}
        self.start_offset_seconds = {}
        self.skipto_in_progress = {}
        print("Cog 'audio' loaded.")
        self.__cog_name__ = "Audio"

    def get_queue(self, guild_id):
        if guild_id not in self.audio_queues:
            self.audio_queues[guild_id] = deque()
            self.skip_requested[guild_id] = False

        if guild_id not in self.looping:
            self.looping[guild_id] = False

        return self.audio_queues[guild_id]

    def resolve_audio_path(self, filename):
        return os.path.join(self.audio_folder, filename)

    def get_audio_duration(self, file_path):
        """Return duration in seconds (float) or None if unknown."""
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if out.returncode == 0 and out.stdout.strip():
                return float(out.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return None

    @staticmethod
    def parse_timestamp(s):
        """Parse '1:15', '1:15:30', or '75' into seconds. Returns None if invalid."""
        if not s or not s.strip():
            return None
        s = s.strip()
        parts = s.split(":")
        if len(parts) == 1:
            try:
                return int(parts[0])
            except ValueError:
                return None
        if len(parts) == 2:
            try:
                m, sec = int(parts[0]), int(parts[1])
                return m * 60 + sec
            except ValueError:
                return None
        if len(parts) == 3:
            try:
                h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
                return h * 3600 + m * 60 + sec
            except ValueError:
                return None
        return None

    @staticmethod
    def format_timestamp(seconds):
        """Format seconds as M:SS or H:MM:SS."""
        if seconds is None or seconds < 0:
            return "0:00"
        secs = int(seconds)
        if secs >= 3600:
            h = secs // 3600
            rem = secs % 3600
            return f"{h}:{rem // 60:02d}:{rem % 60:02d}"
        return f"{secs // 60}:{secs % 60:02d}"

    def get_current_elapsed(self, guild_id):
        """Return current playback position in seconds (including start_offset), or None."""
        if guild_id not in self.playback_start_time:
            return None
        start = self.playback_start_time[guild_id]
        acc_pause = self.accumulated_pause_seconds.get(guild_id, 0)
        pause_start = self.pause_start_time.get(guild_id)
        if pause_start is not None:
            elapsed = pause_start - start - acc_pause
        else:
            elapsed = time.monotonic() - start - acc_pause
        offset = self.start_offset_seconds.get(guild_id, 0)
        return offset + elapsed

    def clear_timestamp_state(self, guild_id):
        """Clear timestamp tracking for a guild."""
        self.playback_start_time.pop(guild_id, None)
        self.total_duration_seconds.pop(guild_id, None)
        self.accumulated_pause_seconds.pop(guild_id, None)
        self.pause_start_time.pop(guild_id, None)
        self.start_offset_seconds.pop(guild_id, None)
        self.next_play_start_offset.pop(guild_id, None)
        self.skipto_in_progress.pop(guild_id, None)

    def collect_audio_from_folder(self, folder_path):
        audio_folder_real = os.path.realpath(self.audio_folder)
        folder_real = os.path.realpath(folder_path)
        if not folder_real.startswith(audio_folder_real):
            return
        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
        for root, _dirs, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(valid_extensions):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, self.audio_folder)
                    yield rel.replace(os.sep, '/')

    def find_audio_by_basename(self, basename, under_path=None):
        """Return list of relative paths (forward slashes) under audio_folder with this basename"""
        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
        if not basename.lower().endswith(valid_extensions):
            return []
        path_prefix = None
        if under_path:
            path_prefix = under_path.replace("\\", "/").strip("/") + "/"
        matches = []
        for root, _dirs, files in os.walk(self.audio_folder):
            for f in files:
                if f.lower() == basename.lower():
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, self.audio_folder)
                    rel_norm = rel.replace(os.sep, "/")
                    if path_prefix is not None and not rel_norm.startswith(path_prefix):
                        continue
                    matches.append(rel_norm)
        return matches

    # ---------- /audio helpers ----------
    def scan_audio_folder(self, opt_dir: str | None) -> tuple[list[str], list[str]]:
        """
        Validates opt_dir and returns (folders, files) as display paths, sorted
        Raises FolderError with a user-facing message on invalid input
        """
        search_folder = os.path.join(self.audio_folder, opt_dir) if opt_dir else self.audio_folder
        audio_folder_real = os.path.realpath(self.audio_folder)
        search_folder_real = os.path.realpath(search_folder)

        if not os.path.isdir(search_folder):
            raise FolderError("That folder couldn't be found. Please check your spelling and try again.")
        if not search_folder_real.startswith(audio_folder_real):
            raise FolderError("That folder path is not valid.")

        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
        folders, files = [], []
        with os.scandir(search_folder) as entries:
            for entry in entries:
                path = f"{opt_dir}/{entry.name}" if opt_dir else entry.name
                if entry.is_dir():
                    folders.append(path)
                elif entry.is_file() and entry.name.lower().endswith(valid_extensions):
                    files.append(path)

        folders.sort()
        files.sort()
        return folders, files

    def resolve_page_size(self, results: int | None) -> int:
        if results is None:
            try:
                with open("./settings.json", "r") as f:
                    settings = json.load(f)
                return settings.get("results_default", 12)
            except Exception as e:
                print(f"[WARN] Failed to load settings.json during audio command. Defaulting to 12: {e}")
                return 12
        if results < 5:
            return 5
        if results < 101:
            return results
        return 100

    def _make_after_callback(self, channel, guild_id, voice_client):
        """Return the after_playing callback used when a track ends (loop, skip, or next)"""
        def after_playing(error):
            if self.skipto_in_progress.pop(guild_id, False):
                return
            if error:
                print(f"[ERROR] Playback error: {error}")
            if self.skip_requested.get(guild_id):
                print(f"[DEBUG] Skip was requested; ignoring current loop.")
                self.skip_requested[guild_id] = False
                asyncio.run_coroutine_threadsafe(
                    self._safe_play_next(channel, guild_id), self.bot.loop
                )
                return
            if self.looping.get(guild_id):
                print(f"[DEBUG] Looping track: {self.current_track[guild_id]}")
                self.start_offset_seconds[guild_id] = 0
                self.playback_start_time[guild_id] = time.monotonic()
                self.accumulated_pause_seconds[guild_id] = 0
                self.pause_start_time[guild_id] = None
                new_source = discord.FFmpegPCMAudio(self.current_track[guild_id], executable="ffmpeg")
                if voice_client:
                    voice_client.play(new_source, after=after_playing)
                return
            asyncio.run_coroutine_threadsafe(
                self._safe_play_next(channel, guild_id), self.bot.loop
            )
        return after_playing

    def play_next(self, channel, guild_id):
        """Queue consumer; sends status to channel"""
        queue = self.get_queue(guild_id)
        guild = self.bot.get_guild(guild_id)
        voice_client = guild.voice_client if guild else None

        async def _play():
            if not queue:
                self.current_track.pop(guild_id, None)
                self.clear_timestamp_state(guild_id)
                return
            filename = queue.popleft()
            file_path = self.resolve_audio_path(filename)
            if not os.path.exists(file_path):
                await channel.send(f"Couldn't find `{filename}`; please check your spelling and try again.")
                self.play_next(channel, guild_id)
                return

            self.current_track[guild_id] = self.resolve_audio_path(filename)
            start_offset = self.next_play_start_offset.pop(guild_id, 0)
            duration = await asyncio.to_thread(self.get_audio_duration, file_path)
            self.total_duration_seconds[guild_id] = duration
            self.start_offset_seconds[guild_id] = start_offset
            self.playback_start_time[guild_id] = time.monotonic()
            self.accumulated_pause_seconds[guild_id] = 0
            self.pause_start_time[guild_id] = None

            before_options = f"-ss {int(start_offset)}" if start_offset else None
            source = discord.FFmpegPCMAudio(file_path, executable="ffmpeg", before_options=before_options)
            after_playing = self._make_after_callback(channel, guild_id, voice_client)

            print(f"[DEBUG] Now playing: {filename}")
            await channel.send(f"Now playing `{filename}`.")
            if voice_client:
                voice_client.play(source, after=after_playing)

        asyncio.create_task(_play())

    async def _safe_play_next(self, channel, guild_id):
        await asyncio.sleep(1)
        self.play_next(channel, guild_id)

    async def _queue_single_track(self, guild, channel, user, path, start_at):
        """Connect to voice if needed, queue one track, start playback if idle. Returns (success, message)."""
        voice_client = guild.voice_client
        just_connected = False
        if not voice_client:
            author_voice = getattr(user, "voice", None)
            if not author_voice or not author_voice.channel:
                return False, "You must be in a voice channel to play audio."
            await author_voice.channel.connect()
            voice_client = guild.voice_client
            just_connected = True
        guild_id = guild.id
        queue = self.get_queue(guild_id)
        queue_was_empty = (not queue) and not voice_client.is_playing()
        queue.append(path)
        if start_at is not None and queue_was_empty:
            parsed = self.parse_timestamp(start_at)
            if parsed is not None and parsed >= 0:
                self.next_play_start_offset[guild_id] = parsed
        if not voice_client.is_playing():
            self.play_next(channel, guild_id)
        if just_connected:
            msg = f"Joined {voice_client.channel.name}, queued track: `{path}`."
        else:
            msg = f"Queued the following track: `{path}`."
        return True, msg

    def cleanup_guild(self, guild_id: int):
        self.audio_queues.pop(guild_id, None)
        self.looping.pop(guild_id, None)
        self.current_track.pop(guild_id, None)
        self.skip_requested.pop(guild_id, None)

        self.clear_timestamp_state(guild_id)

        print(f"[DEBUG] Cleaned audio state for guild {guild_id}")

    @app_commands.command(name="play", description="Queue audio from the audio folder. Use /audio to list files.")
    @app_commands.describe(
        filename="Filename with extension, e.g. song.mp3 or subfolder/song.mp3 or folder path to queue all tracks",
        start_at="Optional. Start playback from this time (e.g. 1:15 or 75). Only used when queue is empty and a single file is played.",
    )
    async def play(self, interaction: discord.Interaction, filename: str, start_at: str = None):
        """Queue audio from the audio folder. Use /audio to list files."""
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Hey, this command only works in servers! What are you doing?", ephemeral=True)
            return
        guild_id = interaction.guild.id
        print(f"[DEBUG] Play command received with filename: {filename!r}")
        file_path = self.resolve_audio_path(filename)
        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')

        # Determine if single file or folder
        to_queue = []
        if filename.lower().endswith(valid_extensions):
            # Resolve by basename; scope to path prefix if user provided one
            basename_only = os.path.basename(filename)
            has_path = "/" in filename or "\\" in filename
            under_path = os.path.dirname(filename).replace("\\", "/").strip("/") or None if has_path else None
            matches = self.find_audio_by_basename(basename_only, under_path=under_path)
            if not matches:
                await interaction.response.send_message(
                    f"Couldn't find `{filename}`; please check your spelling and try again.",
                    ephemeral=True,
                )
                return
            if len(matches) == 1:
                to_queue = [matches[0]]
            else:
                # Multiple matches -> let user choose (ephemeral for requester only)
                view = ChooseTrackView(
                    self, matches, start_at,
                    interaction.guild, interaction.channel, interaction.user,
                )
                await interaction.response.send_message(
                    f"Found **{len(matches)}** tracks named `{os.path.basename(filename)}`. Choose one:",
                    view=view,
                    ephemeral=True,
                )
                return
        else:
            if not os.path.isdir(file_path):
                await interaction.response.send_message(f"Couldn't find folder or file `{filename}`. Use a supported audio file or a folder path under the audio folder.", ephemeral=True)
                return
            audio_folder_real = os.path.realpath(self.audio_folder)
            folder_real = os.path.realpath(file_path)
            if not folder_real.startswith(audio_folder_real):
                await interaction.response.send_message("That folder path is not valid.", ephemeral=True)
                return
            to_queue = list(self.collect_audio_from_folder(file_path))
            if not to_queue:
                await interaction.response.send_message(f"No audio files found in folder `{filename}`.", ephemeral=True)
                return

        if start_at is not None:
            parsed = self.parse_timestamp(start_at)
            if parsed is None or parsed < 0:
                await interaction.response.send_message("Invalid timestamp. Use e.g. `1:15`, `1:15:30`, or `75` (seconds).", ephemeral=True)
                return
            # Only used when single file and queue empty and nothing playing (set below)

        # Connect to voice client
        voice_client = interaction.guild.voice_client
        just_connected = False
        if not voice_client:
            author_voice = getattr(interaction.user, "voice", None)
            if not author_voice or not author_voice.channel:
                await interaction.response.send_message("You must be in a voice channel to play audio.", ephemeral=True)
                return
            await author_voice.channel.connect()
            voice_client = interaction.guild.voice_client
            just_connected = True

        queue = self.get_queue(guild_id)
        queue_was_empty = (not queue) and not voice_client.is_playing()
        for entry in to_queue:
            queue.append(entry)

        if start_at is not None and len(to_queue) == 1 and queue_was_empty:
            self.next_play_start_offset[guild_id] = self.parse_timestamp(start_at)

        if just_connected:
            if len(to_queue) == 1:
                await interaction.response.send_message(f"Joined {voice_client.channel.name}, queued track: `{to_queue[0]}`.")
            else:
                await interaction.response.send_message(f"Joined {voice_client.channel.name}, queued **{len(to_queue)}** tracks from `{filename}`.")
        else:
            if len(to_queue) == 1:
                await interaction.response.send_message(f"Queued the following track: `{to_queue[0]}`.")
            else:
                await interaction.response.send_message(f"Queued **{len(to_queue)}** tracks from `{filename}`.")

        if not voice_client.is_playing():
            self.play_next(interaction.channel, guild_id)

    
    @app_commands.command(name="skip", description="Skip the currently playing track.")
    async def skip(self, interaction: discord.Interaction):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Not currently in a voice channel.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("Not currently in a voice channel.")
            return
        if voice_client.is_playing():
            self.skip_requested[guild_id] = True
            voice_client.stop()
            await asyncio.sleep(1)
            queue = self.get_queue(guild_id)
            if not queue:
                await interaction.response.send_message("The end of the queue has been reached. Use /play (file) to continue audio playback.")
            else:
                await interaction.response.send_message("Skipped to the next track.")
        else:
            await interaction.response.send_message("There's no audio playing to skip!")

    @app_commands.command(name="skipto", description="Skip to a timestamp in the currently playing track.")
    @app_commands.describe(
        timestamp="Time to skip to (e.g. 1:15, 1:15:30, or 75 for seconds).",
    )
    async def skipto(self, interaction: discord.Interaction, timestamp: str):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("This command only works in servers.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("Not currently in a voice channel.", ephemeral=True)
            return
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message("No audio is currently playing to skip within.", ephemeral=True)
            return
        if guild_id not in self.current_track:
            await interaction.response.send_message("No track is currently focused.", ephemeral=True)
            return

        parsed = self.parse_timestamp(timestamp)
        if parsed is None or parsed < 0:
            await interaction.response.send_message(
                "Invalid timestamp. Use e.g. `1:15`, `1:15:30`, or `75` (seconds).",
                ephemeral=True,
            )
            return

        total_duration = self.total_duration_seconds.get(guild_id)
        if total_duration is not None and parsed >= total_duration:
            await interaction.response.send_message(
                "This timestamp exceeds the total runtime of the focused audio track.",
                ephemeral=True,
            )
            return

        file_path = self.current_track[guild_id]
        self.skipto_in_progress[guild_id] = True
        voice_client.stop()
        self.start_offset_seconds[guild_id] = parsed
        self.playback_start_time[guild_id] = time.monotonic()
        self.accumulated_pause_seconds[guild_id] = 0
        self.pause_start_time[guild_id] = None

        before_options = f"-ss {int(parsed)}"
        source = discord.FFmpegPCMAudio(file_path, executable="ffmpeg", before_options=before_options)
        after_playing = self._make_after_callback(interaction.channel, guild_id, voice_client)
        voice_client.play(source, after=after_playing)

        await interaction.response.send_message(f"Skipped to **{self.format_timestamp(parsed)}**.")


    @app_commands.command(name="stop", description="Stop playing and clear the queue.")
    async def stop(self, interaction: discord.Interaction):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Not currently in a voice channel.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client:
            voice_client.stop()
            queue = self.get_queue(guild_id)
            self.looping[guild_id] = False
            self.clear_timestamp_state(guild_id)
            self.current_track.pop(guild_id, None)
            queue.clear()
            await interaction.response.send_message("Audio has been stopped and the queue has been erased.")
        else:
            await interaction.response.send_message("Not currently in a voice channel.")


    @app_commands.command(name="clearqueue", description="Clear the rest of the song queue.")
    async def clearqueue(self, interaction: discord.Interaction):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Not currently in a voice channel to clear the queue.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if voice_client:
            queue = self.get_queue(guild_id)
            if not not queue:
                queue.clear()
                await interaction.response.send_message("The queue has been cleared.")
            else:
                await interaction.response.send_message("The queue is already empty.")
        else:
            await interaction.response.send_message("Not currently in a voice channel to clear the queue.")


    @app_commands.command(name="jump", description="Jump to a different part in the currently playing track.")
    @app_commands.describe(
        timestamp="Time to jump to (e.g. 1:15, 1:15:30, or 75 for seconds).",
    )
    async def jump(self, interaction: discord.Interaction, timestamp: str):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("This command only works in servers.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("Not currently in a voice channel.", ephemeral=True)
            return
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message("No audio is currently playing to jump within.", ephemeral=True)
            return
        if guild_id not in self.current_track:
            await interaction.response.send_message("No track is currently focused.", ephemeral=True)
            return

        parsed = self.parse_timestamp(timestamp)
        if parsed is None or parsed < 0:
            await interaction.response.send_message(
                "Invalid timestamp. Use e.g. `1:15`, `1:15:30`, or `75` (seconds).",
                ephemeral=True,
            )
            return

        total_duration = self.total_duration_seconds.get(guild_id)
        if total_duration is not None and parsed >= total_duration:
            await interaction.response.send_message(
                "This timestamp exceeds the total runtime of the focused audio track! Please try again, this time in the bounds of the track length.",
                ephemeral=True,
            )
            return

        file_path = self.current_track[guild_id]
        self.skipto_in_progress[guild_id] = True
        voice_client.stop()
        self.start_offset_seconds[guild_id] = parsed
        self.playback_start_time[guild_id] = time.monotonic()
        self.accumulated_pause_seconds[guild_id] = 0
        self.pause_start_time[guild_id] = None

        before_options = f"-ss {int(parsed)}"
        source = discord.FFmpegPCMAudio(file_path, executable="ffmpeg", before_options=before_options)
        after_playing = self._make_after_callback(interaction.channel, guild_id, voice_client)
        voice_client.play(source, after=after_playing)

        await interaction.response.send_message(f"Jumped to **{self.format_timestamp(parsed)}**.")


    @app_commands.command(name="loop", description="Toggle looping for the current track.")
    async def loop(self, interaction: discord.Interaction):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Please use this command in a server.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        if self.looping.get(guild_id, False):
            self.looping[guild_id] = False
            await interaction.response.send_message("Looping is now disabled.")
        else:
            self.looping[guild_id] = True
            await interaction.response.send_message("Looping is now enabled.")


    @app_commands.command(name="pause", description="Pause the currently playing track (or unpause it, if already paused).")
    async def pause(self, interaction: discord.Interaction):
        
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("No audio is currently playing.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("No audio is currently playing.")
            return

        if voice_client.is_paused():
            voice_client.resume()
            pause_started = self.pause_start_time.get(guild_id)
            if pause_started is not None:
                self.accumulated_pause_seconds[guild_id] = self.accumulated_pause_seconds.get(guild_id, 0) + (time.monotonic() - pause_started)
                self.pause_start_time[guild_id] = None
            await interaction.response.send_message("Continuing playback.")
            return

        if voice_client.is_playing():
            self.accumulated_pause_seconds.setdefault(guild_id, 0)
            voice_client.pause()
            self.pause_start_time[guild_id] = time.monotonic()
            await interaction.response.send_message("Pausing playback.")
            return

        await interaction.response.send_message("No audio is currently playing.")
        

    @app_commands.command(name="queue", description="View the current queue and now playing.")
    async def queue(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("The queue is empty.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        current = self.current_track.get(guild_id)
        queue = self.audio_queues.get(guild_id, [])

        if not current and not queue:
            embed = discord.Embed(
                title="Queue",
                description="The queue is currently empty.",
                color=0x5865F2,
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="Queue", color=0x5865F2)

        if current:
            current_filename = os.path.basename(current)
            total_sec = self.total_duration_seconds.get(guild_id)
            elapsed_sec = self.get_current_elapsed(guild_id)
            if total_sec is not None and elapsed_sec is not None:
                # clamp elapsed to total for display
                display_elapsed = min(int(elapsed_sec), int(total_sec))
                now_playing_value = f"`{current_filename}` — {self.format_timestamp(display_elapsed)}/{self.format_timestamp(total_sec)}"
            else:
                now_playing_value = f"`{current_filename}`"
            embed.add_field(name="Now playing", value=now_playing_value, inline=False)

        if queue:
            # show up to 20 tracks or truncate
            lines = [f"{i}. `{track}`" for i, track in enumerate(list(queue)[:20], start=1)]
            queue_text = "\n".join(lines)
            if len(queue) > 20:
                queue_text += f"\n*...and {len(queue) - 20} more*"
            embed.add_field(name="Up next", value=queue_text or "—", inline=False)

        loop_status = "Looping is enabled." if self.looping.get(guild_id) else "Looping is disabled."
        embed.set_footer(text=loop_status)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="audio", description="List available audio.")
    @app_commands.describe(subfolder="Optional subfolder path, e.g. 'wip', 'soundtrack', 'sfx', etc.")
    @app_commands.describe(results="Optional; customize the number of returned results per page.")
    async def audio(self, interaction: discord.Interaction, subfolder: str = None, results: int = None):
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            try:
                page_size = self.resolve_page_size(results)
                view = AudioBrowserView(self, subfolder, 0, page_size)
            except FolderError as e:
                await interaction.response.send_message(str(e), ephemeral=True)
                return

            await interaction.response.send_message(view=view)
            view.message = await interaction.original_response()

        except Exception as e:
            print(f"[ERROR] Error reading audio folder in audio command: {e}")
            try:
                await interaction.response.send_message("There was an error attempting to read the audio folder.", ephemeral=True)
            except Exception:
                await interaction.followup.send("There was an error attempting to read the audio folder.", ephemeral=True)

    # Handle unexpected disconnect
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id != self.bot.user.id:
            return
        guild = member.guild
        if before.channel and after.channel is None:
            self.cleanup_guild(guild.id)


async def setup(bot):
    await bot.add_cog(AudioCog(bot))