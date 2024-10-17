"""sopel-search

Search plugin for Sopel IRC bots

Copyright 2024, dgw, technobabbl.es

Licensed under the Eiffel Forum License v2.

https://sopel.chat
"""
from __future__ import annotations

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException, TimeoutException
from sopel import plugin, tools

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
            keywords=query,
            region=bot.settings.search.region,
            safesearch=bot.settings.search.safesearch,
            backend='api',
            max_results=1,
        )
    except RatelimitException:
        bot.reply(
            "Sorry, I can't search right now. If this error persists, ask {} "
            "to check my logs.".format(bot.settings.core.owner)
        )
        LOGGER.error(
            "Rate limit error from DuckDuckGo. If this problem persists, try "
            "`pip install --upgrade duckduckgo-search` to see if there is a "
            "newer version, and restart the bot if so."
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


@plugin.command('suggest')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def suggest(bot, trigger):
    """Suggest search phrases based on the given input."""
    if not trigger.group(2):
        bot.reply('{}suggest what?'.format(bot.settings.core.help_prefix))
        return plugin.NOLIMIT

    query = trigger.group(2)
    results = bot.memory['ddg_search_client'].suggestions(
        query,
        region=bot.settings.search.region,
    )
    try:
        top_three = ["'" + d['phrase'] + "'" for d in results[0:3]]
    except (IndexError, KeyError):
        bot.reply(
            "Sorry, I couldn't get any suggestions for '{}'."
            .format(query)
        )
        return plugin.NOLIMIT

    bot.say(', '.join(top_three[0:-2]) + ' and ' + top_three[-1])


"""
`.gsuggest` command code below is lightly modified from Sopel's old built-in
`search.py` plugin, whose copyright notice is retained here:

search.py - Sopel Search Engine Plugin
Copyright 2008-9, Sean B. Palmer, inamidst.com
Copyright 2012, Elsie Powell, embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""


@plugin.command('gsuggest')
@plugin.example('.gsuggest', '.gsuggest what?')
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def gsuggest(bot, trigger):
    """Get search query autocomplete from Google."""
    # It's true that using Google isn't necessarily ideal, but this is an
    # optional feature. Those who care about privacy can and should use the
    # DuckDuckGo-based `.suggest` command instead.
    try:
        import requests
        import xmltodict
    except ImportError:
        bot.reply(
            'At least one {}gsuggest command dependency is missing. Ask my '
            'owner to see the `sopel-search` plugin README for details.'
            .format(bot.settings.core.help_prefix))
        return plugin.NOLIMIT

    if not trigger.group(2):
        bot.reply('{}gsuggest what?'.format(bot.settings.core.help_prefix))
        return

    query = trigger.group(2)

    base = 'https://suggestqueries.google.com/complete/search'
    parameters = {
        'output': 'toolbar',
        'hl': 'en',
        'q': query,
    }

    response = requests.get(base, parameters)
    answer = xmltodict.parse(response.text)['toplevel']

    try:
        answer = answer['CompleteSuggestion']

        try:
            answer = answer[0]
        except KeyError:
            # only one suggestion; don't need to extract first item
            pass

        answer = answer['suggestion']['@data']
    except TypeError:
        answer = None

    if answer:
        bot.say(answer)
    else:
        bot.reply('Sorry, no result.')
