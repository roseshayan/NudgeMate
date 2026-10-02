import os
import json
import wave
import asyncio
import logging
import subprocess
import urllib.request
from pathlib import Path
import numpy as np

from nudgemate.config import settings

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    def _get_model(self):
        """Loads faster-whisper local model on-demand."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(
                    f"Loading local Whisper model: '{settings.WHISPER_MODEL_SIZE}' "
                    f"on {settings.WHISPER_DEVICE} ({settings.WHISPER_COMPUTE_TYPE})..."
                )
                self._model = WhisperModel(
                    model_size_or_path=settings.WHISPER_MODEL_SIZE,
                    device=settings.WHISPER_DEVICE,
                    compute_type=settings.WHISPER_COMPUTE_TYPE,
                )
                logger.info("Local Whisper model loaded successfully.")
            except ImportError:
                logger.error("faster-whisper is not installed. Please install faster-whisper.")
                raise RuntimeError("کتابخانه faster-whisper نصب نیست.")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
                raise
        return self._model

    def preload_model(self):
        """Pre-warms local model if local STT engine is explicitly enabled."""
        if settings.STT_ENGINE == "local":
            try:
                self._get_model()
                logger.info("Local Whisper model pre-warmed successfully.")
            except Exception as e:
                logger.warning(f"Could not preload local Whisper model: {e}")
        else:
            logger.info(
                f"STT Engine is configured in '{settings.STT_ENGINE}' mode "
                "(Cloud-first, 0% CPU & instant Persian recognition)."
            )

    async def transcribe_audio(self, audio_file_path: Path | str, language: str | None = "fa") -> str:
        """
        Transcribes an audio file using configured multi-engine hierarchy:
          1. Groq Cloud Whisper (if GROQ_API_KEY is configured)
          2. Google Speech Recognition (Default: Free, 0% CPU, high Persian accuracy)
          3. Local Faster-Whisper (Offline fallback)
        """
        file_str = str(audio_file_path)
        lang = language if language in ("fa", "en") else "fa"
        engine_mode = settings.STT_ENGINE.lower()

        # 1. Groq Whisper (Ultra-fast cloud)
        if engine_mode == "groq" or (engine_mode == "auto" and settings.GROQ_API_KEY):
            try:
                text = await self._transcribe_groq(file_str, lang)
                if text and len(text.strip()) > 1:
                    logger.info(f"Transcription completed via [Groq Whisper]: {text[:60]}...")
                    return text
            except Exception as e:
                logger.warning(f"Groq transcription error: {e}. Falling back...")
                if engine_mode == "groq":
                    raise

        # 2. OpenAI Whisper (Official cloud)
        if engine_mode == "openai" or (engine_mode == "auto" and settings.OPENAI_API_KEY and not settings.GROQ_API_KEY):
            try:
                text = await self._transcribe_openai(file_str, lang)
                if text and len(text.strip()) > 1:
                    logger.info(f"Transcription completed via [OpenAI Whisper]: {text[:60]}...")
                    return text
            except Exception as e:
                logger.warning(f"OpenAI transcription error: {e}. Falling back...")
                if engine_mode == "openai":
                    raise

        # 3. Google Speech Recognition (Default cloud engine: Free, accurate, 0% CPU)
        if engine_mode in ("auto", "google"):
            try:
                text = await self._transcribe_google(file_str, lang)
                if text and len(text.strip()) > 1:
                    logger.info(f"Transcription completed via [Google Speech]: {text[:60]}...")
                    return text
                logger.warning("Google Speech returned empty transcript. Falling back to local Whisper...")
            except Exception as e:
                logger.warning(f"Google Speech error: {e}. Falling back to local Whisper...")
                if engine_mode == "google":
                    raise

        # 4. Local Faster-Whisper (On-premise offline fallback)
        logger.info("Transcribing via [Local Faster-Whisper] (fallback)...")
        async with self._lock:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, self._transcribe_local_sync, file_str, lang)
            logger.info(f"Transcription completed via [Local Faster-Whisper]: {text[:60]}...")
            return text

    async def _transcribe_groq(self, file_path: str, language: str) -> str:
        """Transcribes audio using Groq cloud API (Whisper-large-v3-turbo)."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
        )
        with open(file_path, "rb") as f:
            resp = await client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3-turbo",
                language=language,
                response_format="text",
            )
            return str(resp).strip()

    async def _transcribe_openai(self, file_path: str, language: str) -> str:
        """Transcribes audio using OpenAI cloud API (whisper-1)."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            resp = await client.audio.transcriptions.create(
                file=f,
                model="whisper-1",
                language=language,
                response_format="text",
            )
            return str(resp).strip()

    async def _transcribe_google(self, file_path: str, language: str) -> str:
        """
        Transcribes audio using Google Speech Recognition API.
        Converts audio to 16kHz mono FLAC via FFmpeg and posts to Google Speech v2.
        Zero CPU usage, free, and highly accurate for colloquial Persian.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe_google_sync, file_path, language)

    def _transcribe_google_sync(self, file_path: str, language: str) -> str:
        flac_path = f"{file_path}.temp.flac"
        try:
            # Convert audio to 16kHz mono FLAC for Google Speech API
            cmd = [
                "ffmpeg",
                "-y",
                "-i", file_path,
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                flac_path,
            ]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            if res.returncode != 0 or not os.path.exists(flac_path):
                raise RuntimeError("Failed to convert audio to FLAC with ffmpeg")

            with open(flac_path, "rb") as f:
                flac_data = f.read()

            target_lang = "fa-IR" if language == "fa" else "en-US"
            url = (
                f"https://www.google.com/speech-api/v2/recognize?"
                f"client=chromium&lang={target_lang}&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw&pFilter=0"
            )
            req = urllib.request.Request(
                url,
                data=flac_data,
                headers={"Content-Type": "audio/x-flac; rate=16000"},
            )

            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read().decode("utf-8", errors="ignore")
                return self._parse_google_response(content)

        finally:
            if os.path.exists(flac_path):
                try:
                    os.unlink(flac_path)
                except Exception:
                    pass

    @staticmethod
    def _parse_google_response(raw_text: str) -> str:
        """Parses Google Speech API multi-line JSON response."""
        transcripts = []
        for line in raw_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                for res in obj.get("result", []):
                    alts = res.get("alternative", [])
                    if alts and "transcript" in alts[0]:
                        transcripts.append(alts[0]["transcript"])
            except Exception:
                pass
        return " ".join(transcripts).strip()

    def _convert_to_pcm16_array(self, input_file: str) -> np.ndarray | None:
        """
        Converts audio to 16kHz mono PCM 16-bit WAV via FFmpeg CLI,
        then reads into a float32 numpy array normalized to [-1.0, 1.0].
        This completely bypasses PyAV container bugs and version incompatibilities.
        """
        wav_path = f"{input_file}.converted.wav"
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_file,
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                wav_path,
            ]
            res = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            if res.returncode == 0 and os.path.exists(wav_path):
                with wave.open(wav_path, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    return samples
        except Exception as e:
            logger.warning(f"FFmpeg PCM conversion failed: {e}. Falling back to path.")
        finally:
            if os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass
        return None

    def _transcribe_local_sync(self, file_path: str, language: str = "fa") -> str:
        """Fallback local Faster-Whisper transcription."""
        model = self._get_model()

        audio_data = self._convert_to_pcm16_array(file_path)
        audio_target = audio_data if audio_data is not None else file_path

        initial_prompt = (
            "سلام، یادآوری کارهای روزمره، قرارها، ساعت‌ها، آشپزی، کارها و جلسات به زبان فارسی."
            if language == "fa"
            else "Voice notes, reminders, tasks, schedules, and daily briefings."
        )

        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
            "initial_prompt": initial_prompt,
        }
        if language:
            transcribe_kwargs["language"] = language

        segments, info = model.transcribe(audio_target, **transcribe_kwargs)

        transcript_parts = [segment.text.strip() for segment in segments]
        full_text = " ".join(transcript_parts).strip()
        return full_text


voice_service = VoiceService()
