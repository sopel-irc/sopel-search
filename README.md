# sopel-search

Search plugin for Sopel IRC bots

## Installing

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```shell
$ pip install sopel-search
```

This plugin is designed for use with Sopel version 8.0+, but may have a higher
minimum Python version requirement than Sopel itself due to upstream libraries.

## Configuring

The easiest way to configure `sopel-search` is via Sopel's configuration
wizard—simply run `sopel-plugins configure search` and enter the values for
which it prompts you. Available settings are:

* `region`: Set this to the primary geographical region of your bot's users,
  using one of the values from https://duckduckgo.com/params

  Setting this correctly may improve the relevance of both search results and
  query suggestions using `.suggest`.
* `safesearch`: Controls SafeSearch filtering of `.search` results; one of 'on',
  'moderate', and 'off'.

## Using

Two primary functions are available, `search` and `suggest`:

* `.search` (aliases: `.ddg`, `.g`): Perform a text search and return the top result
* `.suggest`: Fetch autocomplete suggestions for the stem of a search query
