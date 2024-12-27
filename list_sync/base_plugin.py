import pluginlib

@pluginlib.Parent('list_scraper')
class ListScraper(object):

    @pluginlib.abstractmethod
    def get_list(list_id, config=None):
        pass
