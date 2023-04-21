import threading
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from scripts.mo.dl.downloader import Downloader


class HttpDownloader(Downloader):

    def accepts_url(self, url: str) -> bool:
        return urlparse(url).scheme in ['http', 'https']

    def fetch_filename(self, url):
        response = requests.get(url, headers={'Range': 'bytes=0-1'})
        if response.status_code == 200 or response.status_code == 206:
            if 'Content-Disposition' in response.headers:
                content_disp = response.headers['Content-Disposition']
                return content_disp.split(';')[1].split('=')[1].strip('\"')
        else:
            return None

    def download(self, url: str, destination_file: str, description: str, stop_event: threading.Event):
        if stop_event.is_set():
            return

        yield {'bytes_ready': 0, 'bytes_total': 0, 'speed_rate': 0, 'elapsed': 0}

        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        yield {'bytes_ready': 0, 'bytes_total': total_size, 'speed_rate': 0, 'elapsed': 0}

        if stop_event.is_set():
            return

        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc=description)

        with open(destination_file, 'wb') as file:

            if stop_event.is_set():
                progress_bar.close()
                return

            for data in response.iter_content(1024):

                if stop_event.is_set():
                    progress_bar.close()
                    return

                file.write(data)
                progress_bar.update(len(data))
                format_dict = progress_bar.format_dict

                yield {
                    'bytes_ready': format_dict['n'],
                    'bytes_total': format_dict['total'],
                    'speed_rate': format_dict['rate'],
                    'elapsed': format_dict['elapsed']
                }
            yield {
                'bytes_ready': total_size,
                'bytes_total': total_size,
                'speed_rate': 0,
                'elapsed': 0
            }
            progress_bar.close()
