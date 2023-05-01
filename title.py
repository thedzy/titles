#!/usr/bin/env python3

"""
Script:	title.py
Date:	2020-05-04

Platform: MacOS/Windows/Linux

Description:
Print a title
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Developer'

import os
import platform
import string
from typing import Optional

import numpy
from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageOps


class Title:
    def __init__(self, characters=string.ascii_letters + string.punctuation + string.digits,
                 font=None, font_height=25, font_variation=None,
                 font_for_brightness=None,
                 character_aspect=2.2, resolution=15, algorithm='abs',
                 invert=False):

        # Character and render information
        self.characters = str(characters) + ' '
        self.character_info = {}

        # Get the default font
        system = platform.uname().system.lower()
        if 'darwin' in system:
            system_font = '/System/Library/Fonts/Menlo.ttc'
        elif 'windows' in system:
            system_font = 'C:/Windows/Fonts/consola.ttf'
        elif 'linux' in system:
            if os.path.exists('/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'):
                system_font = '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'
            else:
                system_font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

        if font is None:
            self.display_font = system_font
        else:
            if os.path.exists(font):
                self.display_font = font
            else:
                print('Path to {} cannot be accessed/found'.format(font))
                self.display_font = system_font

        # Dimension to create a sample character
        self.sample_height, self.sample_width = 200, 200

        # Set the default font size and style
        self.font_height = font_height
        self.font_variation = font_variation

        # Load font to be used
        self.font = ImageFont.FreeTypeFont(self.display_font, self.font_height, layout_engine=ImageFont.Layout.BASIC)

        # If specified, set font variation, on error list variations
        self.font = self.font.font_variant()
        if self.font_variation:
            try:
                self.font.set_variation_by_name(self.font_variation)
            except (ValueError, OSError):
                try:
                    variations = font.get_variation_names()
                    print(f'Choose from the following variations:')
                    for variation in variations:
                        print(f'\t - {variation.decode()}')
                except OSError:
                    print('Font does not support variations')

        # Set the default font used for rendering
        if font_for_brightness is None:
            self.font_for_brightness = system_font
        else:
            if os.path.exists(font_for_brightness):
                self.font = font
            else:
                print('Path to {} cannot be accessed/found'.format(font))
                self.font = system_font

        # Load font to be used for brightness
        self.font_for_brightness = ImageFont.FreeTypeFont(self.font_for_brightness, self.sample_height,
                                                          layout_engine=ImageFont.Layout.BASIC)

        # Set information to calculate rendering
        self.character_aspect = character_aspect
        self.resolution = resolution
        self.algorithm = getattr(self, f'find_match_{algorithm}')

        self.invert = invert

        # Get window/terminal size
        try:
            self.window_width, _ = os.get_terminal_size()
        except:
            self.window_width = 180

        self.upper_left, self.lower_right = self.__calculate_bounding_box()

        self.__calculate_characters()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        pass

    def print(self, text, algorithm: Optional[str] = None, invert: bool = False) -> None:
        """
        Print text
        :param text: (str) Text to print
        :param algorithm: (str) Algorithm to use
        :param invert: (bool) Invert text
        :return: None
        """

        if algorithm is None:
            algorithm = self.algorithm
        else:
            algorithm = getattr(self, f'find_match_{algorithm}')

        # Get height
        _, top, _, bottom = self.font.getbbox(self.characters)
        text_height = int((bottom - top) * 1.4)

        # Generate images for each lines
        text_images = []
        for line in text.split('\n'):
            # Skip blank lines
            if len(line.strip()) == 0:
                continue

            # Render text
            text_image = Image.new('L', (self.window_width * 20, text_height), 0)
            draw = ImageDraw.Draw(text_image)
            draw.text((0, 0), line, font=self.font, fill=255, align='left')

            # Crop empty space
            image_black = Image.new(text_image.mode, text_image.size, 0)
            diff = ImageChops.difference(text_image, image_black)
            image_bounds = diff.getbbox()

            # Crop out empty space on the width and height
            text_image = text_image.crop((image_bounds[0], image_bounds[1], image_bounds[2], image_bounds[3]))

            text_images.append(text_image)

        # Find the largest image to scale evenly
        image_width = 0
        for text_image in text_images:
            # Get image size
            text_image_width, _ = text_image.width, text_image.height
            image_width = text_image_width if text_image_width > image_width else image_width

        # Find the scale for scaling down
        resize_ratio = self.window_width / image_width if image_width > self.window_width else 1

        # Print Characters
        for text_image in text_images:
            image_width, image_height = text_image.width, text_image.height

            # Scale it smaller than 1 to 1 and by resolution
            text_image = text_image.resize((int(image_width * resize_ratio * self.resolution),
                                            int(image_height * resize_ratio * self.resolution / self.character_aspect)))

            # Invert?
            if invert is None:
                if self.invert:
                    text_image = ImageOps.invert(text_image)
            else:
                if invert:
                    text_image = ImageOps.invert(text_image)

            # Get final image size
            image_width = text_image.width
            image_height = text_image.height

            # Write image to screen
            line = 0
            while line < image_height:
                # For section/"column" in "row"
                printed_line = ''
                for index in range(image_width // self.resolution):
                    index = index * self.resolution

                    # Section of image (resolution * resolution)
                    pattern = numpy.zeros((self.resolution, self.resolution))
                    for col in range(self.resolution):
                        for row in range(self.resolution):
                            try:
                                pattern[row][col] = text_image.getpixel((index + col, line + row))
                            except IndexError:
                                pattern[row][col] = 0

                    # Find matching character for section append string
                    printed_line += algorithm(pattern, self.character_info, self.resolution)
                print(printed_line)

                # Jump to the next "row" of pixels in the image
                line += self.resolution

    def set_characters(self, characters: str) -> None:
        """
        Set the default characters to use to render the text
        :param characters: (string) Characters to render with
        :return: (void)
        """
        self.characters = str(characters) + ' '
        self.__calculate_characters()

    def set_character_aspect(self, character_aspect: float = 2.4) -> None:
        """
        Set the default character aspect ratio
        :param character_aspect: (float) Width to height ration, ex 2.4
        :return: (void)
        """
        self.character_aspect = float(character_aspect)

    def set_font(self, font: str) -> None:
        """
        Set the default font for rendering
        :param font: (string) Path to font file
        :return: (bool) Successfully set
        """
        self.font = ImageFont.FreeTypeFont(font, self.font_height, layout_engine=ImageFont.Layout.BASIC)

    def set_font_size(self, font_height: int = 20) -> None:
        """
        Set the default font size
        :param font_height: (int) Font size
        :return: (void)
        """
        self.font_height = int(font_height)
        self.font = ImageFont.FreeTypeFont(self.display_font, self.font_height, layout_engine=ImageFont.Layout.BASIC)

    def set_invert(self, invert: bool = False) -> None:
        """
        Set whether the default is to invert or not
        :param invert: (bool) To invert text
        :return: (void)
        """
        self.invert = bool(invert)

    @staticmethod
    def find_match_norm(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using numpy linear algebra
        :param pattern: 2d array of values
        :param characters: (dict) Characters ans 2d arrays
        :param resolution: (int) Array size
        :return: (str) Character that best matches
        """

        matched_character, matched_matrix = ' ', None
        min_distance = numpy.inf
        for character, matrix in characters.items():
            distance = numpy.linalg.norm(pattern - matrix)
            if distance < min_distance:
                min_distance = distance
                matched_character, matched_matrix = character, matrix

        # Return best match
        return matched_character

    @staticmethod
    def find_match_outline(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using count of close matches
        :param pattern: 2d array of values
        :param characters: (dict) Characters and 2d arrays
        :param resolution: (int) Array size
        :return: (str) Character that best matches
        """
        threshold = resolution / 4
        best_match, matched_character = 0, ' '
        for character, matrix in characters.items():
            new_matrix = numpy.abs(pattern - matrix)
            mask = (new_matrix < threshold) | (new_matrix > (256 - threshold))
            distance = numpy.count_nonzero(mask)
            if distance > best_match:
                best_match = distance
                matched_character, matched_matrix = character, matrix

        # Return best match
        return matched_character

    @staticmethod
    def find_match_low(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using count of close low matches
        :param pattern: 2d array of values
        :param characters: (dict) Characters and 2d arrays
        :param resolution: (int) Array size
        :return:
        """
        threshold = 40
        best_match, matched_character = 0, ' '
        for character, matrix in characters.items():
            new_matrix = numpy.abs(pattern - matrix)
            distance = sum(1 for x in new_matrix for y in x if y < threshold)
            if distance > best_match:
                best_match = distance
                matched_character, matched_matrix = character, matrix

        # Return best match
        return matched_character

    @staticmethod
    def find_match_abs(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using numpy sum(abs(matrix-matrix))
        :param pattern: 2d array of values
        :param characters: (dict) Characters ans 2d arrays
        :param resolution: (int) Array size
        :return:
        """
        best_match = numpy.infty
        matched_character = ' '
        for character, matrix in characters.items():
            simularity = numpy.sum(numpy.abs(pattern - matrix))
            if simularity < best_match:
                matched_character = character
                best_match = simularity

        # Return best match
        return matched_character

    @staticmethod
    def find_match_abs2(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using numpy filtering for count of values with less than 64 difference
        :param pattern: 2d array of values
        :param characters: (dict) Characters ans 2d arrays
        :param resolution: (int) Array size
        :return: (str) Character that best matches
        """
        best_match = numpy.infty
        for character, matrix in characters.items():
            mask = (numpy.abs(pattern - matrix) > 64)
            simularity = numpy.count_nonzero(mask)

            if simularity < best_match:
                matched_character = character
                best_match = simularity

        # Return best match
        return matched_character

    @staticmethod
    def find_match_binary(pattern: numpy.ndarray, characters: dict, resolution: int) -> str:
        """
        Compare a pattern and find the match in the character set using numpy binary matching
        :param pattern: 2d array of values
        :param characters: (dict) Characters ans 2d arrays
        :param resolution: (int) Array size
        :return: (str) Character that best matches
        """
        best_match = numpy.infty
        for character, matrix in characters.items():
            new_pattern = numpy.interp(pattern, (0.0, 256.0), (0, 2)).astype(int)
            new_matrix = numpy.interp(matrix, (0.0, 256.0), (0, 2)).astype(int)
            mask = (numpy.abs(new_pattern - new_matrix) == 1)
            simularity = numpy.count_nonzero(mask)

            if simularity < best_match:
                matched_character = character
                best_match = simularity

        # Return best match
        return matched_character

    def __calculate_bounding_box(self) -> tuple:
        """
        Calculate the bounding box for the rending font
        :return: (tuple)(tuple) Upper, lower coordinates
        """

        # Render a sample character to get crop dimensions
        character_image = Image.new('L', (self.sample_width * 2, self.sample_height * 2), 0)
        draw = ImageDraw.Draw(character_image)

        # Draw each character over each other
        for index, char in enumerate(self.characters):
            # Draw the character in the center of the image
            draw.text((0, 0), char, font=self.font_for_brightness, fill=256)

        # Get the bounding box of the characters
        bounding_box = character_image.getbbox()
        upper_left = bounding_box[0:2]
        lower_right = bounding_box[2:4]

        return upper_left, lower_right

    def __calculate_characters(self) -> None:
        """
        Calculate the array information for each character for mapping
        :return: None
        """

        self.character_info = {}

        # Get brightness of a character in matrix
        for supplied_char in self.characters:
            self.character_info[supplied_char] = self.__image_chopper(supplied_char, self.upper_left,
                                                                      self.lower_right)

    def __image_chopper(self, character: str, top_left: numpy.ndarray,
                        bottom_right: numpy.ndarray) -> numpy.ndarray:
        """
        Chop up image and return 2d array of values
        :param character: Character to slice
        :param top_left: (tuple) Coordinates
        :param bottom_right:(tuple) Coordinates
        :return: (numpy.ndarray) Matrix of brightness values
        """

        # Get image size
        width, height = bottom_right

        # Create image of character
        character_image = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(character_image)
        draw.text((0, -top_left[1]), character, font=self.font_for_brightness, fill=255, align='left')

        # Crop to bounds
        character_image = character_image.crop((0, 0, bottom_right[0], bottom_right[1]))

        # Resize to resolution and convert to greyscale
        resized_image = character_image.resize((self.resolution, self.resolution))
        resized_image = resized_image.convert('L')

        # Return matrix of brightness values
        return numpy.asarray(resized_image)
