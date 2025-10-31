import hashlib
import zipfile
from pathlib import Path
from typing import Any, Dict

import requests
import yaml
from tqdm import tqdm


def ensure_data_available() -> None:
    """
    Check if data exists locally. Download from Zenodo if missing.

    This function is called on package import to ensure data availability.
    Downloads only occur on first use or if data is missing/corrupted.
    """
    if _data_exists():
        return  # Data already available

    config = _load_config()
    dataset_info = config["dataset"]
    file_info = config["files"][0]

    print("=" * 70)
    print(f"📦 CPC Data v{dataset_info['version']}: Dataset not found")
    print("=" * 70)
    print("Downloading dataset from Zenodo (this only happens once)...")
    print(f"Dataset: {dataset_info['name']}")
    print(f"Size: ~{file_info['size_mb']} MB")
    print(f"Source: https://doi.org/10.5281/zenodo.{dataset_info['zenodo_record_id']}")
    print()

    download_data()

    print()
    print("✅ Download complete! Data ready for use.")
    print("=" * 70)


def download_data(force: bool = False) -> None:
    """
    Download and extract the CPC dataset from Zenodo.

    Args:
        force: If True, re-download even if data exists
    """
    if not force and _data_exists():
        print("Data already exists. Use force=True to re-download.")
        return

    from utils import get_project_root

    config = _load_config()
    file_info = config["files"][0]
    settings = config["download_settings"]

    project_root = get_project_root()

    # Setup archive directory
    archive_dir = project_root / settings["archive_dir"]
    archive_dir.mkdir(parents=True, exist_ok=True)
    zip_path = archive_dir / file_info["filename"]

    # Download file
    _download_file(file_info["url"], zip_path, settings["chunk_size"])

    # Verify checksum if enabled
    if settings["verify_checksum"]:
        print("Verifying download...")
        if not _verify_md5(zip_path, file_info["md5"]):
            zip_path.unlink()  # Delete corrupted file
            raise RuntimeError("Download verification failed. Please try again.")
        print("✓ Verification successful")

    # Extract to data directory
    print("Extracting dataset...")
    data_dir = project_root / file_info["extract_to"]
    data_dir.mkdir(parents=True, exist_ok=True)
    _extract_zip(zip_path, data_dir)

    # Cleanup archive if configured
    if not settings["keep_archive"]:
        print("Cleaning up archive...")
        zip_path.unlink()
    else:
        print(f"Archive kept at: {zip_path}")

    # Verify extraction
    if not _data_exists():
        raise RuntimeError("Data extraction completed but verification failed")


def _load_config() -> Dict[str, Any]:
    """Load download configuration from YAML file."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _data_exists() -> bool:
    """
    Check if essential data files exist.

    Returns:
        True if data appears to be present and complete
    """
    from utils import get_project_root

    data_dir = get_project_root() / "data"

    # Check for key files that should always exist
    essential_files = [
        data_dir / "class_values.csv",
        data_dir / "injection_molding" / "upper_workpiece" / "static_data.csv",
        data_dir / "injection_molding" / "lower_workpiece" / "static_data.csv",
        data_dir / "screw_driving" / "static_data.csv",
    ]

    return all(f.exists() for f in essential_files)


def _download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
    """
    Download a file from URL with progress bar.

    Args:
        url: URL to download from
        destination: Path to save the file
        chunk_size: Size of chunks to download
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(destination, "wb") as f, tqdm(
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading",
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            pbar.update(len(chunk))


def _verify_md5(file_path: Path, expected_md5: str) -> bool:
    """
    Verify file MD5 checksum.

    Args:
        file_path: Path to file to verify
        expected_md5: Expected MD5 hash

    Returns:
        True if checksum matches
    """
    md5_hash = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)

    actual_md5 = md5_hash.hexdigest()
    return actual_md5 == expected_md5


def _extract_zip(zip_path: Path, destination: Path) -> None:
    """
    Extract a ZIP file to destination directory.

    Args:
        zip_path: Path to ZIP file
        destination: Directory to extract to
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Extract with progress bar
        members = zip_ref.namelist()
        for member in tqdm(members, desc="Extracting", unit="file"):
            zip_ref.extract(member, destination)
