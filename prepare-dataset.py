#!/bin/env python3
import argparse
import json
import os
import random

from PIL import Image, ImageOps
from tqdm import tqdm

import constants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='dataset.config.json', help='path to the config file')
    parser.add_argument('--captcha_dir', default='captcha', help='path to the captcha')
    parser.add_argument('--segmented_dir', default='dataset/segmented', help='path to the output dataset')
    parser.add_argument('--whole_dir', default='dataset/whole', help='path to the output dataset')
    args = parser.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    with open(os.path.join(args.captcha_dir, constants.SEGMENTATION_FILE_NAME)) as f:
        lines = f.readlines()
    if 'random-seed' in config:
        random.Random(config['random-seed']).shuffle(lines)
    else:
        random.shuffle(lines)
    filenames = set()
    for count, line in enumerate(tqdm(lines, desc='Segmented')):
        line = line.strip()
        filename, segments = line.split(':')
        segments = [int(i) for i in segments.split(',')]
        filename_without_ext = os.path.splitext(filename)[0]
        code = filename_without_ext.split('.')[1]
        filenames.add(filename)
        try:
            image = Image.open(os.path.join(args.captcha_dir, filename))
        except FileNotFoundError:
            continue
        image = ImageOps.grayscale(image)
        image = image.crop((
            config['margin-left'], config['margin-top'],
            constants.IMAGE_WIDTH - config['margin-right'],
            constants.IMAGE_HEIGHT - config['margin-bottom']
        ))
        train_or_test = 'train' if count / (len(lines) - 1) <= config.get('train-test-ratio', 0.8) else 'test'
        folder = os.path.join(args.whole_dir, train_or_test)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), 'wb') as image_file:
            image.save(image_file)
        folder = os.path.join(args.whole_dir, 'all')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), 'wb') as image_file:
            image.save(image_file)
        for left in range(0, image.width - config['character-width'] + 1, config['slide-x']):
            character_image = image.crop((left, 0, left + config['character-width'], image.height))
            center = config['margin-left'] + left + config['character-width'] / 2
            distances = [abs(center - segment) for segment in segments]
            min_distance = min(distances)
            character = '+' if min_distance >= config['blank-distance'] else code[distances.index(min_distance)]
            folder = os.path.join(args.segmented_dir, train_or_test, character)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, f'{filename_without_ext}.{round(center)}.jpeg'), 'wb') as image_file:
                character_image.save(image_file)
            folder = os.path.join(args.segmented_dir, 'all', character)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, f'{filename_without_ext}.{round(center)}.jpeg'), 'wb') as image_file:
                character_image.save(image_file)
    unsegmented = []
    for filename in os.listdir(args.captcha_dir):
        name, ext = os.path.splitext(filename)
        name = name.split('.')
        if ext == '.jpeg' and len(name) == 2 and len(name[0]) == 32 and filename not in filenames:
            unsegmented.append(filename)
    for count, filename in enumerate(tqdm(unsegmented, desc='Unsegmented')):
        try:
            image = Image.open(os.path.join(args.captcha_dir, filename))
        except FileNotFoundError:
            continue
        image = ImageOps.grayscale(image)
        image = image.crop((
            config['margin-left'], config['margin-top'],
            constants.IMAGE_WIDTH - config['margin-right'],
            constants.IMAGE_HEIGHT - config['margin-bottom']
        ))
        train_or_test = 'train' if count / (len(unsegmented) - 1) <= config.get('train-test-ratio', 0.8) else 'test'
        folder = os.path.join(args.whole_dir, train_or_test)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), 'wb') as image_file:
            image.save(image_file)
        folder = os.path.join(args.whole_dir, 'all')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), 'wb') as image_file:
            image.save(image_file)


if __name__ == '__main__':
    main()
