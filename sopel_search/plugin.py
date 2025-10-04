"""sopel-search

Search plugin for Sopel IRC bots

Copyright 2024, dgw, technobabbl.es

Licensed under the Eiffel Forum License v2.

https://sopel.chat
"""
from __future__ import annotations

from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException
import requests
from sopel import plugin, tools
import xmltodict

from .config import configure_plugin, SearchSection


LOGGER = tools.get_logger('search')
PLUGIN_OUTPUT_PREFIX = '[search] '


def setup(bot):
    bot.settings.define_section('search', SearchSection)
    refresh_ddgs_client(bot)


def shutdown(bot):
    del bot.memory['ddg_search_client']


def configure(config):
    configure_plugin(config)


# recreate the DDGS client hourly to avoid excess `RatelimitException`s
# it seems to get stale after a while, probably longer than an hour but
# it's not that expensive to recreate the client more often
@plugin.interval(60 * 60)
def refresh_ddgs_client(bot):
    bot.memory['ddg_search_client'] = DDGS()
    LOGGER.debug('Refreshed DuckDuckGo search client.')


@plugin.commands('search', 'ddg', 'g')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def search(bot, trigger):
    """Search DuckDuckGo for the given query."""
    if not trigger.group(2):
        bot.reply('{}{} what?'.format(
            bot.settings.core.help_prefix,
            trigger.group(1),
        ))
        return plugin.NOLIMIT

    query = trigger.group(2)

    try:
        results = bot.memory['ddg_search_client'].text(
            query=query,
            region=bot.settings.search.region,
            safesearch=bot.settings.search.safesearch,
            backend='duckduckgo, google, brave, bing',
            max_results=1,
        )
    except RatelimitException:
        bot.reply(
            "Sorry, I can't search right now. If this error persists, ask {} "
            "to check my logs.".format(bot.settings.core.owner)
        )
        LOGGER.error(
            "Rate limit error. If this problem persists, try `pip install "
            "--upgrade ddgs` to see if there is a newer version, and restart "
            "the bot if so."
        )
        LOGGER.debug(
            "Refreshing DDGS client to try to recover from RatelimitException.")
        refresh_ddgs_client(bot)
        return
    except TimeoutException:
        bot.reply("Sorry, the search request timed out. Try again later.")
        LOGGER.error("Timeout during search request.")
        LOGGER.debug(
            "Refreshing DDGS client to try to recover from TimeoutException.")
        refresh_ddgs_client(bot)
        return

    if not results:
        bot.reply("Sorry, no results found for '{}'.".format(query))
        return

    result = results[0]
    bot.say(
        '{title} — {link}'.format(
            title=result['title'],
            link=result['href'],
        )
    )


"""
`.gsuggest` command code below is based on Sopel's old built-in `search.py`
plugin, whose copyright notice is retained here.

search.py - Sopel Search Engine Plugin
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""


@plugin.command('suggest', 'gsuggest')
@plugin.example('.gsuggest', '.gsuggest what?')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def gsuggest(bot, trigger):
    """Get search query autocomplete suggestions from Google."""
    # It's true that using Google isn't necessarily ideal, but DDGS removed
    # support for suggestions in its 7.x release series.
    if not trigger.group(2):
        bot.reply('{}gsuggest what?'.format(bot.settings.core.help_prefix))
        return

    query = trigger.group(2)
    language = (bot.settings.search.region.partition('-')[1] or 'en').lower()

    base = 'https://suggestqueries.google.com/complete/search'
    parameters = {
        'output': 'toolbar',
        'hl': language,
        'q': query,
    }

    response = requests.get(base, parameters)

    try:
        answers = xmltodict.parse(response.text)['toplevel']['CompleteSuggestion']
    except TypeError:
        # empty suggestion list returns `{'toplevel': None}`, which will raise
        # `TypeError` when trying to access nonexistent `CompleteSuggestion` key
        answers = []

    if not isinstance(answers, list):
        # a single suggestion is returned as just a dict; wrap it in a list
        answers = [answers]

    answers = [f"'{answer['suggestion']['@data']}'" for answer in answers]
    top_three = answers[:3]

    if answers:
        start = ', '.join(top_three[:-1])
        if start:
            start += ' and '
        bot.say(start + top_three[-1])
    else:
        bot.reply('Sorry, no result.')
