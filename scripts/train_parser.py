"""Simple training scaffold for ML parser using Kaggle datasets.
This script demonstrates how to download a dataset (if Kaggle configured) and run a placeholder training step.
"""
import argparse
from pathlib import Path
from chatbot.kaggle_helper import kaggle_available, download_dataset
import logging

logger = logging.getLogger(__name__)

def main(dataset: str, dest: str):
    if dataset:
        if not kaggle_available():
            logger.error("Kaggle credentials not found. Configure KAGGLE_USERNAME/KAGGLE_KEY or ~/.kaggle/kaggle.json")
            return
        path = download_dataset(dataset, dest)
        logger.info(f"Dataset downloaded to {path}")

    # Placeholder: load data, train model, save artifacts
    logger.info("Placeholder: implement training pipeline here (tokenization, model, eval)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='kaggle dataset slug e.g. owner/dataset', default='')
    parser.add_argument('--dest', help='destination folder', default='data')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.dataset, args.dest)
