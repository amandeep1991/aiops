import abc
import re

from bs4 import BeautifulSoup

from aiops.config import logger
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

        special_characters = ["\-", u"\u002d", u"\u058a", u"\u058b", u"\u2010", u"\u2011", u"\u2012",
                              u"\u2013", u"\u2014", u"\u2015", u"\u2e3a", u"\u2e3b", u"\ufe58",
                              u"\ufe63", u"\uff0d", u"\u1427"]
        for c in special_characters:
            html_text = html_text.replace(c, " ")

        soup = BeautifulSoup(html_text, 'lxml')

        for key, value in self.mapping_for_filtering_specific_tags_by_bs.items():
            if kwargs.get(key, True):
                logger.debug("filtering out: '{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
                map(lambda table: table.replaceWith(""), soup.find_all(value))

        text = soup.text
        for pattern, replace in kwargs.get("regex_tuples_list", []):
            logger.debug("filtering out: regex='{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
            text = re.sub(pattern, replace, text)

        if kwargs.get("replace_contractions", True):
            for pattern, replace in contractions_replace_dict.items():
                text = re.sub(r"\b" + pattern + r"\b", replace, text)
            logger.debug("contractions have been replaced successfully")

        if kwargs.get("replace_social_media", True):
            for pattern, replace in social_media_replace_dict.items():
                text = re.sub(pattern, replace, text)
            logger.debug("social_media have been replaced successfully")

        if kwargs.get("mask_months", True):
            text = re.sub(*mask_map.get("mask_months"), text)
            logger.debug("months successfully masked!")

        if kwargs.get("mask_timezones", True):
            text = re.sub(*mask_map.get("mask_timezones"), text)
            logger.debug("time-zones successfully masked!")

        if kwargs.get("mask_years", True):
            text = re.sub(*mask_map.get("mask_years"), text)

        if kwargs.get("mask_question_marks", True):
            text = re.sub(*mask_map.get("mask_question_marks"), text)

        if kwargs.get("mask_exclamation_marks", True):
            text = re.sub(*mask_map.get("mask_exclamation_marks"), text)

        text = re.sub(r"\d+", r" ", text)
        text = re.sub(r"\t+", r" ", text)
        text = re.sub(r"\r+", r"\n", text)
        text = re.sub(r"[^a-z\n]", r" ", text)
        text = re.sub(r"\n+", r"\n", text)
        text = re.sub(r" +", r" ", text)
        return text
