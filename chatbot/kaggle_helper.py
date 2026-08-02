"""Simple Kaggle helper to optionally download datasets when credentials are available.

This module is optional — it detects Kaggle credentials in env or in ~/.kaggle/kaggle.json
and exposes `download_dataset(dataset, dest)` which returns the path or raises a clear error.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def kaggle_available():
    # Check env vars or default kaggle.json location
    if os.getenv('KAGGLE_USERNAME') and os.getenv('KAGGLE_KEY'):
        return True
    kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
    return kaggle_json.exists()

def download_dataset(dataset: str, dest: str = 'data') -> str:
    """Download a Kaggle dataset (owner/dataset-name) to `dest` folder.

    Example: download_dataset('zynicide/wine-reviews', dest='data/wine')
    Requires Kaggle API credentials to be configured.
    """
    try:
        if not kaggle_available():
            raise RuntimeError('Kaggle credentials not found; set KAGGLE_USERNAME/KAGGLE_KEY or ~/.kaggle/kaggle.json')

        import kaggle
        dest_path = Path(dest)
        dest_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading Kaggle dataset {dataset} to {dest_path}")
        kaggle.api.dataset_download_files(dataset, path=str(dest_path), unzip=True, quiet=False)
        return str(dest_path)

    except Exception as e:
        logger.error(f"Failed to download Kaggle dataset {dataset}: {e}")
        raise
