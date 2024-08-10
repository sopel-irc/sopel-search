"""Configuration definitions for sopel-search.

Part of sopel-search.

Copyright 2024, dgw, technobabbl.es

Licensed under the Eiffel Forum License v2.

https://sopel.chat
"""
from __future__ import annotations

from sopel.config.types import (
    ChoiceAttribute,
    StaticSection,
    ValidatedAttribute,
)


SAFESEARCH_LEVELS = (
    'on',
    'moderate',
    'off',
)


class SearchSection(StaticSection):
    region = ValidatedAttribute(
        name='region',
        default='us-en',
    )
    """Search region to use for DuckDuckGo queries.

    See https://duckduckgo.com/params for up-to-date list of options.
    """

    safesearch = ChoiceAttribute(
        name='safesearch',
        choices=SAFESEARCH_LEVELS,
        default='moderate',
    )
    """SafeSearch level for DuckDuckGo searches."""


def configure_plugin(config):
    config.define_section('search', SearchSection)
    config.search.configure_setting(
        'region',
        "What region should I use for DuckDuckGo searches? "
        "(see https://duckduckgo.com/params for options)",
    )
    config.search.configure_setting(
        'safesearch',
        "Choose a SafeSearch level for searches using this plugin: {}"
        .format('/'.join(SAFESEARCH_LEVELS)),
    )
