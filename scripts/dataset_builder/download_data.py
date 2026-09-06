"""
Dataset downloader for the Crime Analysis project.

This module is the first stage of the data pipeline. It is responsible
exclusively for downloading and organising raw datasets from configured
sources into the prescribed raw data directory structure.

The module performs NO cleaning, NO preprocessing, NO machine learning,
and NO database operations. Its sole purpose is to reliably fetch source
files and organise them.

Usage:
    python -m scripts.dataset_builder.download_data

Or programmatically:
    from scripts.dataset_builder.download_data import DatasetDownloader
    downloader = DatasetDownloader()
    downloader.run()
"""

from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: Tuple[str, ...] = (".csv", ".zip", ".json", ".xlsx", ".xls")
"""File extensions supported by the downloader."""

RAW_SUBDIRS: Tuple[str, ...] = ("government", "police", "news", "archived")
"""Subdirectory names inside data/raw/ where source files are organised."""

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DatasetInfo:
    """
    Metadata describing a downloaded dataset.

    Attributes:
        name: Human-readable name of the dataset.
        source: The original source identifier.
        downloaded_at: UTC timestamp of when the download completed.
        file_path: Path to the downloaded file.
        file_size: Size of the downloaded file in bytes.
        format: File extension without the dot (e.g. "csv", "zip", "json").
    """

    name: str
    source: str
    downloaded_at: str
    file_path: str
    file_size: int
    format: str

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary of this metadata."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "DatasetInfo":
        """Create a DatasetInfo from a dictionary (e.g. loaded from a JSON file)."""
        return cls(
            name=str(data["name"]),
            source=str(data["source"]),
            downloaded_at=str(data["downloaded_at"]),
            file_path=str(data["file_path"]),
            file_size=int(data["file_size"]),
            format=str(data["format"]),
        )


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------


class DatasetDownloader:
    """
    Orchestrates the downloading of crime datasets from configured sources.

    The download workflow is as follows:

        1. Ensure required directories exist.
        2. Load dataset source configuration from a JSON file.
        3. For each configured dataset, download the file, verify integrity,
           extract archives if needed, and persist metadata.
        4. Return the list of successfully downloaded datasets.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        config_path: Optional[str] = None,
        raw_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """
        Initialise the DatasetDownloader.

        Args:
            config_path: Path to the JSON configuration file listing datasets
                to download. Defaults to ``config/dataset_sources.json``.
            raw_dir: Root directory for raw data storage. Defaults to
                ``data/raw`` relative to the project root.
            log_dir: Directory for log output. Defaults to ``logs``.
            force: If True, re-download files even if they already exist.
        """
        # Resolve the project root (assumes this file lives at
        # scripts/dataset_builder/download_data.py).
        self._project_root: Path = Path(__file__).resolve().parents[2]

        # Configuration path
        if config_path:
            self._config_path: Path = Path(config_path).resolve()
        else:
            self._config_path = self._project_root / "config" / "dataset_sources.json"

        # Data directory
        if raw_dir:
            self._raw_dir: Path = Path(raw_dir).resolve()
        else:
            self._raw_dir = self._project_root / "data" / "raw"

        # Log directory
        if log_dir:
            self._log_dir: Path = Path(log_dir).resolve()
        else:
            self._log_dir = self._project_root / "logs"

        self._force: bool = force

        # Internal state
        self._downloaded_files: List[DatasetInfo] = []
        self._source_configs: List[Dict[str, object]] = []

        logger.info(
            "DatasetDownloader initialised. Config: %s, Raw: %s, Force: %s",
            self._config_path,
            self._raw_dir,
            self._force,
        )

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def create_directories(self) -> None:
        """
        Ensure all required directories exist.

        Creates ``data/raw/government/``, ``data/raw/police/``,
        ``data/raw/news/``, ``data/raw/archived/``, and the
        logs directory. Idempotent — safe to call multiple times.
        """
        directories: List[Path] = [
            self._raw_dir / subdir for subdir in RAW_SUBDIRS
        ] + [self._log_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured directory exists: %s", directory)

        logger.info(
            "Directory structure ready. %d directories under %s",
            len(directories),
            self._raw_dir,
        )

    # ------------------------------------------------------------------
    # Source configuration loading
    # ------------------------------------------------------------------

    def load_sources(self) -> List[Dict[str, object]]:
        """
        Read dataset source configuration from the JSON config file.

        The config file is expected to contain a JSON object with a
        ``datasets`` key holding an array of dataset descriptors.
        Each descriptor must have at minimum the keys ``name``,
        ``source``, ``url``, and ``category``.

        Returns:
            A list of dataset configuration dictionaries. If the config
            file does not exist, an empty list is returned with a warning.
        """
        if not self._config_path.is_file():
            logger.warning(
                "Source configuration not found at %s. Returning empty list.",
                self._config_path,
            )
            self._source_configs = []
            return self._source_configs

        with self._config_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, List[Dict[str, object]]] = json.load(fh)

        self._source_configs = data.get("datasets", [])
        logger.info(
            "Loaded %d dataset source(s) from %s",
            len(self._source_configs),
            self._config_path,
        )

        return self._source_configs

    # ------------------------------------------------------------------
    # Single dataset download
    # ------------------------------------------------------------------

    def download_dataset(self, dataset_config: Dict[str, object]) -> Optional[DatasetInfo]:
        """
        Download a single dataset from its configured URL.

        The file is saved to the appropriate subdirectory under
        ``data/raw/`` based on the dataset's ``category`` field.
        Supported formats are CSV, ZIP, JSON, and Excel (xlsx/xls).

        Args:
            dataset_config: A dictionary with keys ``name``, ``source``,
                ``url``, and ``category``.

        Returns:
            A DatasetInfo instance if the download succeeds, or None if
            the download fails or is skipped.
        """
        name: str = str(dataset_config.get("name", "unnamed"))
        source_url: str = str(dataset_config.get("url", ""))
        category: str = str(dataset_config.get("category", "archived"))

        # Validate the URL is present
        if not source_url:
            logger.error("Dataset '%s' has no URL. Skipping.", name)
            return None

        # Determine the target subdirectory and file path
        target_dir: Path = self._raw_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

        filename: str = self._infer_filename(source_url, name)
        target_path: Path = target_dir / filename

        # Skip if the file already exists and force is False
        if target_path.is_file() and not self._force:
            logger.info("File already exists (skipping): %s — %s", name, target_path)
            return DatasetInfo(
                name=name,
                source=str(dataset_config.get("source", "unknown")),
                downloaded_at=datetime.now(timezone.utc).isoformat(),
                file_path=str(target_path),
                file_size=target_path.stat().st_size,
                format=target_path.suffix.lstrip("."),
            )

        # Perform the download
        logger.info("Downloading '%s' from %s ...", name, source_url)
        try:
            self._stream_download(source_url, target_path)
        except (URLError, HTTPError, OSError) as exc:
            logger.error("Failed to download '%s': %s", name, exc)
            return None

        # Verify the downloaded file
        if not self.verify_download(target_path):
            logger.error("Verification failed for '%s'. Removing file.", name)
            self._remove_file(target_path)
            return None

        # Extract ZIP archives automatically
        if target_path.suffix.lower() == ".zip":
            extract_dir: Path = target_dir / target_path.stem
            self.extract_archive(target_path, extract_dir)

        # Build and persist metadata
        file_size: int = target_path.stat().st_size
        dataset_info: DatasetInfo = DatasetInfo(
            name=name,
            source=str(dataset_config.get("source", "unknown")),
            downloaded_at=datetime.now(timezone.utc).isoformat(),
            file_path=str(target_path),
            file_size=file_size,
            format=target_path.suffix.lstrip("."),
        )

        self.save_metadata(dataset_info, target_dir)

        logger.info("Downloaded successfully: %s (%d bytes)", name, file_size)
        return dataset_info

    # ------------------------------------------------------------------
    # Internal: stream download
    # ------------------------------------------------------------------

    @staticmethod
    def _stream_download(url: str, target_path: Path, chunk_size: int = 8192) -> None:
        """
        Download a file from *url* in chunks and write it to *target_path*.

        Uses a polite ``User-Agent`` header to reduce the likelihood of
        being blocked by the server.

        Args:
            url: The source URL to download.
            target_path: Local path where the file content is saved.
            chunk_size: Number of bytes per read chunk (default 8 KB).

        Raises:
            URLError: If the network request fails.
            HTTPError: If the server returns a non-200 status.
            OSError: If the file cannot be written.
        """
        request: Request = Request(
            url,
            headers={
                "User-Agent": (
                    "CrimeAnalysisDownloader/1.0 "
                    "(DataPipeline; +https://github.com/crime-analysis)"
                ),
            },
        )

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with urlopen(request, timeout=120) as response:
            with target_path.open("wb") as out_file:
                while True:
                    chunk: bytes = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)

    # ------------------------------------------------------------------
    # Download verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_download(file_path: Path) -> bool:
        """
        Verify that a downloaded file is valid.

        Checks:
            - The file exists on disk.
            - The file size is greater than zero bytes.
            - The file extension is one of the supported types.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if all checks pass, False otherwise.
        """
        if not file_path.is_file():
            logger.warning("Verification failed: file not found — %s", file_path)
            return False

        if file_path.stat().st_size == 0:
            logger.warning("Verification failed: file is empty — %s", file_path)
            return False

        extension: str = file_path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            logger.warning(
                "Verification warning: unsupported extension '%s' — %s",
                extension,
                file_path,
            )

        logger.debug("Verification passed: %s (%d bytes)", file_path, file_path.stat().st_size)
        return True

    # ------------------------------------------------------------------
    # Archive extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_archive(zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract a ZIP archive into a dedicated directory.

        If the extraction directory already exists, extraction is skipped
        to avoid overwriting previously extracted files.

        Args:
            zip_path: Path to the ZIP file.
            extract_dir: Directory where the contents will be extracted.

        Returns:
            Path to the extraction directory.

        Raises:
            zipfile.BadZipFile: If the ZIP file is corrupt.
        """
        if extract_dir.is_dir():
            logger.info("Extraction directory already exists (skipping): %s", extract_dir)
            return extract_dir

        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        logger.info("Extracted %s -> %s", zip_path, extract_dir)
        return extract_dir

    # ------------------------------------------------------------------
    # Metadata persistence
    # ------------------------------------------------------------------

    @staticmethod
    def save_metadata(dataset_info: DatasetInfo, target_dir: Path) -> Path:
        """
        Save dataset metadata as a JSON file alongside the data file.

        The metadata file is named ``{dataset_name}.meta.json``.

        Args:
            dataset_info: The metadata to persist.
            target_dir: Directory where the metadata file is saved.

        Returns:
            Path to the saved metadata file.
        """
        meta_path: Path = target_dir / f"{dataset_info.name}.meta.json"

        with meta_path.open("w", encoding="utf-8") as fh:
            json.dump(dataset_info.to_dict(), fh, indent=2, ensure_ascii=False)

        logger.debug("Metadata saved: %s", meta_path)
        return meta_path

    # ------------------------------------------------------------------
    # List downloaded files
    # ------------------------------------------------------------------

    def list_downloaded_files(self) -> List[DatasetInfo]:
        """
        Return metadata for all datasets downloaded in this session.

        Returns:
            A list of DatasetInfo objects for the current run.
        """
        return list(self._downloaded_files)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_filename(url: str, default_name: str) -> str:
        """
        Derive a local filename from a download URL.

        If the URL path contains a filename with an extension, that is
        used. Otherwise the default name is returned with a ``.csv``
        extension.

        Args:
            url: The source URL.
            default_name: Fallback filename.

        Returns:
            A safe filename string.
        """
        parsed = urlparse(url)
        path_part: str = parsed.path.rstrip("/")

        if path_part and "." in path_part:
            url_filename: str = path_part.rsplit("/", 1)[-1]
            if url_filename:
                return url_filename

        return f"{default_name}.csv"

    @staticmethod
    def _remove_file(path: Path) -> None:
        """
        Safely remove a file, logging errors instead of raising them.

        Args:
            path: Path to the file to remove.
        """
        try:
            path.unlink(missing_ok=True)
            logger.debug("Removed file: %s", path)
        except PermissionError as exc:
            logger.error("Cannot remove file (permission denied): %s — %s", path, exc)

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def run(self) -> List[DatasetInfo]:
        """
        Execute the complete downloading workflow.

        Steps:
            1. Create required directories.
            2. Load source configuration.
            3. Download each configured dataset.
            4. Return metadata for all successfully downloaded files.

        Returns:
            A list of DatasetInfo objects for successfully downloaded datasets.
        """
        logger.info("=" * 60)
        logger.info("Dataset download run started at %s", datetime.now(timezone.utc))
        logger.info("=" * 60)

        self.create_directories()
        sources: List[Dict[str, object]] = self.load_sources()

        if not sources:
            logger.warning("No dataset sources configured. Nothing to download.")
            return []

        successful: int = 0
        failed: int = 0

        for source_cfg in sources:
            result: Optional[DatasetInfo] = self.download_dataset(source_cfg)
            if result is not None:
                self._downloaded_files.append(result)
                successful += 1
            else:
                failed += 1

        logger.info("=" * 60)
        logger.info(
            "Download run complete. Successful: %d, Failed: %d, Total: %d",
            successful,
            failed,
            len(sources),
        )
        logger.info("=" * 60)

        return self.list_downloaded_files()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point for the dataset downloader.

    Configures console logging, creates a DatasetDownloader, and
    executes the full download workflow.

    Usage:
        python -m scripts.dataset_builder.download_data
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    downloader: DatasetDownloader = DatasetDownloader()
    results: List[DatasetInfo] = downloader.run()

    print(f"\nDownloaded {len(results)} dataset(s):")
    for info in results:
        print(f"  - {info.name}: {info.file_path} ({info.file_size:,} bytes)")


if __name__ == "__main__":
    main()