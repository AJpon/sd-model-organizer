import threading
from urllib.parse import urlparse

from scripts.mo.dl.downloader import Downloader


class MegaDownloader(Downloader):

    def accepts_url(self, url: str) -> bool:
        hostname = urlparse(url).hostname
        if hostname == 'mega.nz':
            if 'mega.nz/folder/' in url:
                raise Exception('Mega folder download not supported')

            try:
                import mega
                return True
            except ImportError:
                print("mega.py package is required to download ", url)

        return False

    def fetch_filename(self, url: str):
        raise NotImplementedError('MEGA not implemented yet')

    def download(self, url: str, destination_file: str, stop_event: threading.Event):
        raise NotImplementedError('MEGA not implemented yet')

# _mega_instance = None
# def _mega() -> Mega:
#     global _mega_instance
#     if _mega_instance is None:
#         _mega_instance = Mega()
#         _mega_instance.login()
#     return _mega_instance
#
#
# def accepts_url(url) -> bool:
#     hostname = urlparse(url).hostname
#     return hostname == 'mega.nz'
#
#
# def fetch_filename(url: str):
#     try:
#         return _mega().get_public_url_info(url)['name']
#     except Exception as ex:
#         print(ex)
#         return None
#
# def download(url: str):
#     mega = Mega()
#     m = mega.login()
#     m_url = ''
#     m.download_url(m_url,
#                    dest_path='/Users/alexander/Projects/Python/stable-diffusion-webui/extensions/sd-model-organizer/tmp')
