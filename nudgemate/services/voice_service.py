import os
import wave
import asyncio
import logging
import subprocess
from pathlib import Path
import numpy as np

from nudgemate.config import settings

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    def _get_model(self):
        """Loads faster-whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(
                    f"Loading Whisper model: '{settings.WHISPER_MODEL_SIZE}' "
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

    def preload_model(self):
        """Pre-warms/loads Whisper model into memory so first voice transcription is instantaneous."""
        try:
            self._get_model()
            logger.info("Whisper model pre-warmed successfully.")
        except Exception as e:
            logger.warning(f"Could not preload Whisper model at startup (will load on demand): {e}")

    async def transcribe_audio(self, audio_file_path: Path | str, language: str | None = "fa") -> str:
        """
        Transcribes an audio file (e.g. Telegram .ogg voice note) to text.
        Executes in an executor to avoid blocking the asyncio event loop.
        """
        async with self._lock:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, self._transcribe_sync, str(audio_file_path), language
            )

    def _convert_to_pcm16_array(self, input_file: str) -> np.ndarray | None:
        """
        Converts audio file to 16kHz mono PCM 16-bit WAV via FFmpeg CLI,
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
            logger.warning(f"FFmpeg PCM conversion failed: {e}. Falling back to default loader.")
        finally:
            if os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass
        return None

    def _transcribe_sync(self, file_path: str, language: str | None = "fa") -> str:
        model = self._get_model()

        # Step 1: Attempt conversion to 16kHz float32 numpy array via ffmpeg CLI
        audio_data = self._convert_to_pcm16_array(file_path)
        audio_target = audio_data if audio_data is not None else file_path

        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500),
        }
        if language:
            transcribe_kwargs["language"] = language

        segments, info = model.transcribe(audio_target, **transcribe_kwargs)

        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())

        full_text = " ".join(transcript_parts).strip()
        logger.info(
            f"Transcription completed (detected language: {info.language}, prob: {info.language_probability:.2f}): "
            f"{full_text[:60]}..."
        )
        return full_text


voice_service = VoiceService()
