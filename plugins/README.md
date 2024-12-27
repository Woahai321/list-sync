# List Scraper Plugins

Each of these files implements the [base_plugin.py](https://github.com/ghomasHudson/Jellyfin-Auto-Collections/blob/master/utils/base_plugin.py) base class:

```python
import pluginlib

@pluginlib.Parent('list_scraper')
class ListScraper(object):

    @pluginlib.abstractmethod
    def get_list(list_id, config=None):
        pass
```

`get_list` should return a dictionary with the format:

```
{
  "name": "Ultimate top 100 list",
  "items": [
    {"title": "My Movie", "release_year": "2021", "media_type": "movie"},
     ...
  ]
}
```
