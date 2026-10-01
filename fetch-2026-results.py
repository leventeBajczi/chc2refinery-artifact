#!/usr/bin/env python3
"""Extract the published CHC-COMP 2026 results into results/.

The archive (https://doi.org/10.5281/zenodo.20413019, 2 GB) is a snapshot of the competition
directory. By default, only the BenchExec result files (results/*.xml, results/*.txt) are
extracted: they are all that `make process-results` needs. With --logfiles, the run logs
(results/*.logfiles/, 5.6 GB unpacked) are extracted too; the result pages link to them, and
validating the models again needs them.

Only the extracted parts of the archive are downloaded, with HTTP range requests. If the server
does not support them, or with --archive, the whole archive is used instead.

Usage: fetch-2026-results.py [--logfiles] [--archive upload.zip] [--dest .]
"""
import argparse
import io
import os
import re
import shutil
import sys
import urllib.request
import zipfile

URL = 'https://zenodo.org/records/20413019/files/upload.zip?download=1'
MD5 = '498fd7d36bb1fe338322d282ba744833'


class HttpFile(io.RawIOBase):
    """A read-only, seekable view of a remote file, read with HTTP range requests."""

    def __init__(self, url: str):
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': 'bytes=0-0'})) as r:
            if r.status != 206:
                raise OSError('the server does not support range requests')
            self.url = r.geturl()
            self.size = int(r.headers['Content-Range'].rsplit('/', 1)[1])
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        self.pos = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence] + offset
        return self.pos

    def readinto(self, buffer):
        end = min(self.pos + len(buffer), self.size)
        if end <= self.pos:
            return 0
        request = urllib.request.Request(self.url, headers={'Range': f'bytes={self.pos}-{end - 1}'})
        with urllib.request.urlopen(request) as r:
            data = r.read()
        buffer[:len(data)] = data
        self.pos += len(data)
        return len(data)


def open_archive(path: str | None) -> zipfile.ZipFile:
    if path:
        return zipfile.ZipFile(path)
    try:
        return zipfile.ZipFile(io.BufferedReader(HttpFile(URL), buffer_size=8 << 20))
    except OSError as e:
        print(f'{e}: downloading the whole archive (2 GB) to upload.zip', file=sys.stderr)
        urllib.request.urlretrieve(URL, 'upload.zip')
        return zipfile.ZipFile('upload.zip')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--logfiles', action='store_true', help='also extract the run logs (5.6 GB)')
    parser.add_argument('--archive', help=f'a local copy of the archive (md5 {MD5}) instead of {URL}')
    parser.add_argument('--dest', default='.', help='directory to extract into (default: .)')
    args = parser.parse_args(argv)

    wanted = re.compile(r'results/[^/]+\.(xml|txt)' + (r'|results/[^/]+\.logfiles/.+' if args.logfiles else ''))
    with open_archive(args.archive) as archive:
        members = [m for m in archive.infolist() if wanted.fullmatch(m.filename) and not m.is_dir()]
        total = sum(m.compress_size for m in members)
        print(f'Extracting {len(members)} files ({total / 1e6:.0f} MB compressed) into {args.dest}/results')
        done = 0
        for i, member in enumerate(members):
            target = os.path.join(args.dest, member.filename)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with archive.open(member) as source, open(target, 'wb') as out:
                shutil.copyfileobj(source, out)
            done += member.compress_size
            if (i + 1) % 1000 == 0 or i + 1 == len(members):
                print(f'  {i + 1}/{len(members)} files, {done / 1e6:.0f}/{total / 1e6:.0f} MB', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
