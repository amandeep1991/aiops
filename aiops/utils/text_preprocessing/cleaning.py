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
            # "ignore_links": "a",
            "ignore_images": "img",
            "ignore_videos": "video",

            # Saving the template for quick code changes
            # "ignore_": "",
        }

    def process(self, html_text, *args, **kwargs):
        html_text = html_text.replace("’", "'").encode('ascii', errors='ignore')
        html_text = html_text.decode('ascii')

        special_characters = ["\-", u"\u002d", u"\u058a", u"\u058b", u"\u2010", u"\u2011", u"\u2012",
                              u"\u2013", u"\u2014", u"\u2015", u"\u2e3a", u"\u2e3b", u"\ufe58",
                              u"\ufe63", u"\uff0d", u"\u1427"]
        for c in special_characters:
            html_text = re.sub(c, " ", html_text, flags=re.IGNORECASE)

        soup = BeautifulSoup(html_text, 'lxml')
        soup_with_tables = BeautifulSoup(html_text, 'lxml')

        for key, value in self.mapping_for_filtering_specific_tags_by_bs.items():
            if kwargs.get(key, True):
                # logger.debug("filtering out: '{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
                list(map(lambda table: table.extract(), soup.find_all(value)))

        text = soup.text
        text_with_tables = soup_with_tables.text
        text = self.manipulation_over_text(kwargs, text)
        text_with_tables = self.manipulation_over_text(kwargs, text_with_tables)
        return text, text_with_tables

    def manipulation_over_text(self, kwargs, text):
        for pattern, replace in kwargs.get("regex_tuples_list", []):
            # logger.debug("filtering out: regex='{value}' tag for specified configuration: '{key}'".format(key=key, value=value))
            text = re.sub(pattern, replace, text, flags=re.IGNORECASE)
        if kwargs.get("replace_contractions", True):
            for pattern, replace in contractions_replace_dict.items():
                text = re.sub(r"\b" + pattern + r"\b", replace, text, flags=re.IGNORECASE)
            # logger.debug("contractions have been replaced successfully")
        if kwargs.get("replace_social_media", True):
            for pattern, replace in social_media_replace_dict.items():
                text = re.sub(pattern, replace, text, flags=re.IGNORECASE)
            # logger.debug("social_media have been replaced successfully")
        if kwargs.get("mask_months", False):
            text = re.sub(*mask_map.get("mask_months"), text, flags=re.IGNORECASE)
            # logger.debug("months successfully masked!")
        if kwargs.get("mask_timezones", False):
            text = re.sub(*mask_map.get("mask_timezones"), text, flags=re.IGNORECASE)
            # logger.debug("time-zones successfully masked!")
        if kwargs.get("mask_years", False):
            text = re.sub(*mask_map.get("mask_years"), text, flags=re.IGNORECASE)
        if kwargs.get("mask_question_marks", False):
            text = re.sub(*mask_map.get("mask_question_marks"), text, flags=re.IGNORECASE)
        if kwargs.get("mask_exclamation_marks", False):
            text = re.sub(*mask_map.get("mask_exclamation_marks"), text, flags=re.IGNORECASE)
        # if kwargs.get("mask_email_id", True):
        #     text = re.sub(r'[^a-zA-Z][^\n]*@[^\n]*[^a-zA-Z]', '', text, flags=re.IGNORECASE)
        if kwargs.get("mask_urls", True):
            text = re.sub(r'^https?:\/\/[^ ]*[\r\n]*', '', text, flags=re.MULTILINE + re.DOTALL)
        # text = re.sub(r"\d+", r" ", text, flags=re.IGNORECASE)
        text = re.sub(r"\t[\t  ]+", r" ", text, flags=re.IGNORECASE)
        text = re.sub(r"\r[\r  ]+", r"\n", text, flags=re.IGNORECASE)
        text = re.sub(r"[\n\t\r][\n\t\r  ]+", r"\n", text, flags=re.IGNORECASE)
        text = re.sub(r"[  ]+", r" ", text, flags=re.IGNORECASE)
        return text
