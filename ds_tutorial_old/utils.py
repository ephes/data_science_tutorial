import requests
from tqdm import tqdm_notebook as tqdm


def download_from_url(url, dst, chunk_size=1024):
    """
    @param: url to download
    @param: dst path to destination file
    """
    file_size = int(requests.head(url).headers["Content-Length"])
    first_byte = dst.stat().st_size if dst.exists() else 0
    
    # return early when we are already done
    if first_byte >= file_size:
        return file_size
    
    # download first_byte to file_size
    header = {"Range": "bytes={}-{}".format(first_byte, file_size)}
    pbar = tqdm(
        total=file_size, initial=first_byte,
        unit='B', unit_scale=True, desc=url.split('/')[-1])
    req = requests.get(url, headers=header, stream=True)
    with(open(str(dst), 'ab')) as f:
        for chunk in req.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(chunk_size)
    pbar.close()
    return file_size
