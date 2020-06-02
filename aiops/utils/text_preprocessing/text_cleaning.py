import abc
import logging
import re

from bs4 import BeautifulSoup

from aiops.utils.text_preprocessing.mask_conf import mask_map
from aiops.utils.text_preprocessing.replace_conf import social_media_replace_dict, contractions_replace_dict


class TextCleaning(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def process(self, text, *args, **kwargs):
        raise NotImplementedError


class HtmlTextCleaning(TextCleaning):

    def __init__(self) -> None:
        self.mapping_for_filtering_specific_tags_by_bs = {
            "ignore_tables": "table",
            "ignore_links": "a",
            "ignore_images": "img",
            "ignore_videos": "video",

            # Saving the template for quick code changes
            # "ignore_": "",
        }

    def process(self, html_text, *args, **kwargs):
        html_text = html_text.encode('ascii', errors='ignore')
        html_text = html_text.lower().decode('ascii')
        html_text = html_text.replace("\-", " ")
        soup = BeautifulSoup(html_text, 'lxml')

        for key, value in self.mapping_for_filtering_specific_tags_by_bs.items():
            if kwargs.get(key, True):
                logging.debug("filtering out: '{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
                map(lambda table: table.replaceWith(""), soup.find_all(value))

        text = soup.text
        for pattern, replace in kwargs.get("regex_tuples_list", True):
            logging.debug("filtering out: regex='{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
            text = re.sub(pattern, replace, text)

        if kwargs.get("replace_contractions", True):
            for pattern, replace in contractions_replace_dict.items():
                text = re.sub(r"\b"+pattern+r"\b", replace, text)
            logging.debug("contractions have been replaced successfully")

        if kwargs.get("replace_social_media", True):
            for pattern, replace in social_media_replace_dict.items():
                text = re.sub(pattern, replace, text)
            logging.debug("social_media have been replaced successfully")

        if kwargs.get("mask_months", True):
            for pattern, replace in mask_map.get("mask_months"):
                text = re.sub(pattern, replace, text)
            logging.debug("months successfully masked!")

        if kwargs.get("mask_timezones", True):
            for pattern, replace in mask_map.get("mask_timezones"):
                text = re.sub(pattern, replace, text)
            logging.debug("time-zones successfully masked!")

        if kwargs.get("mask_years", True):
            text = re.sub(*mask_map.get("mask_years"), text)

        if kwargs.get("mask_question_marks", True):
            text = re.sub(*mask_map.get("mask_question_marks"), text)

        if kwargs.get("mask_exclamation_marks", True):
            text = re.sub(*mask_map.get("mask_exclamation_marks"), text)

        text = re.sub(r"\d+", r" ", text)
        text = re.sub(r"\t+", r" ", text)
        text = re.sub(r"\r+", r" ", text)
        text = re.sub(r"[^a-z]", r" ", text)
        text = re.sub(r" +", r" ", text)
        return text
