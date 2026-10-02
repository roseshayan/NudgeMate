import os
import asyncio
import logging
from pathlib import Path
from nudgemate.config import settings

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    def _get_model(self):
        """Lazy loader for faster-whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(
                    f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE} "
                    f"on {settings.WHISPER_DEVICE} ({settings.WHISPER_COMPUTE_TYPE})..."
                )
                self._model = WhisperModel(
                    model_size_or_path=settings.WHISPER_MODEL_SIZE,
                    device=settings.WHISPER_DEVICE,
                    compute_type=settings.WHISPER_COMPUTE_TYPE,
                )
                logger.info("Whisper model loaded successfully.")
            except ImportError:
                logger.error("faster-whisper is not installed. Please install faster-whisper.")
                raise RuntimeError("کتابخانه faster-whisper نصب نیست.")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
                raise
        return self._model

    async def transcribe_audio(self, audio_file_path: Path | str) -> str:
        """
        Transcribes an audio file (e.g. Telegram .ogg voice note) to Persian text.
        Executes in an executor to avoid blocking the asyncio event loop.
        """
        async with self._lock:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._transcribe_sync, str(audio_file_path))

    def _transcribe_sync(self, file_path: str) -> str:
        model = self._get_model()
        segments, info = model.transcribe(
            file_path,
            language="fa",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())

        full_text = " ".join(transcript_parts).strip()
        logger.info(f"Transcription completed (detected language: {info.language}): {full_text[:60]}...")
        return full_text


voice_service = VoiceService()
