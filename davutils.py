# -*- coding: utf-8 -*-

import time
import os.path
from fnmatch import fnmatchcase

class DAVError(Exception):
    '''A protocol exception that is passed to client through HTTP.
    Two properties:
    - httpstatus: e.g. '404 Not Found'
    - body: None or e.g. '<DAV:cannot-modify-protected-property/>'
    
    Argument httpstatus is passed to WebDAV client as HTTP status code.
    Body can optionally be an XML response body; otherwise,
    exception handler generates an text/plain response of the
    status code.
    '''
    def __init__(self, httpstatus, body = None):
        self.httpstatus = httpstatus
        self.body = body
    
    def __str__(self):
        return self.httpstatus
    
    def __repr__(self):
        return ('DAVError(' + repr(self.httpstatus) +
                ', ' + repr(self.body) + ')')
    
    def __eq__(self, other):
        return (isinstance(other, DAVError)
                and self.httpstatus == other.httpstatus
                and self.body == other.body)
    
    def __hash__(self):
        return hash(self.httpstatus) ^ hash(self.body)

def read_blocks(source, count = None, blocksize = 1024*1024):
    '''Read and yield block-sized strings from open file object,
    up to a total of count bytes.
    '''
    while count is None or count > 0:
        if count is not None:
            blocksize = min(count, blocksize)

        data = source.read(blocksize)
        
        if len(data) == 0:
            return # End of file
        
        if count is not None:
            count -= len(data)
        
        yield data

def write_blocks(dest, blocks):
    '''Write a series of blocks to open file object.'''
    for block in blocks:
        dest.write(block)

def path_inside_directory(path, root):
    '''Check if path is inside root directory.
    '''
    path_parts = os.path.abspath(path).split(os.path.sep)
    root_parts = os.path.abspath(root).split(os.path.sep)
    
    return path_parts[:len(root_parts)] == root_parts

def get_isoformat(timestamp):
    '''Format the timestamp according to ISO8601 / RFC3339.'''
    t = time.gmtime(timestamp)
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', t)

def get_rfcformat(timestamp):
    '''Format the timestamp according to RFC822.'''
    t = time.gmtime(timestamp)
    return time.strftime('%a, %d %b %Y %H:%M:%S %z', t)

def get_usertime(timestamp):
    '''Format the timestamp for reading by user.'''
    t = time.localtime(timestamp)
    return time.strftime('%d-%b-%Y %H:%M:%S', t)

def set_mtime(real_path, rfctime):
    '''Set file modification time based on a RFC822 timestamp.'''
    timestamp = time.strptime(rfctime, '%a, %d %b %Y %H:%M:%S %z')
    os.utime(real_path, (timestamp, timestamp))

def pretty_unit(value, base=1000, minunit=None, format="%0.1f"):
    ''' Finds the correct unit and returns a pretty string
    pretty_unit(4190591051, base=1024) = "3.9 Gi"

    From http://github.com/str4nd/bittivahti/
    '''
    if not minunit:
        minunit = base
    
    # Units based on base
    if base == 1000:
        units = [' ', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    elif base == 1024:
        units = [' ', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']
    else:
        raise InvalidBaseException("The unit base has to be 1000 or 1024")
    
    # Divide until below threshold or base
    v = float(value)
    u = base
    for unit in units:
        if v >= base or u <= minunit:
            v = v/base
            u = u * base
        else:
            return format % v + " " + unit

def create_etag(real_path):
    '''Get an unique identifier for this revision of the file.
    This is used by HTTP clients for caching purposes.
    '''
    return ('"' + str(os.path.getmtime(real_path)) +
        'S' + str(os.path.getsize(real_path)) + '"')

def compare_etags(etag, etag_list):
    '''Compare the specified etag against the list.
    List can be either a single tag, a list separated with comma,
    or an asterisk:
    - '"tag"': matches only if etag == '"tag"'
    - '"tag1", "tag2"': matches if etag in ['"tag1"', '"tag2"']
    - '*': matches any etag
    
    Note: the ETags generated by this application do not contain
    commas. This function can't match against ETags with commas.
    '''
    parts = [e.strip() for e in etag_list.split(',')]
    
    if parts == ['*']:
        return True
    elif etag in parts:
        return True
    else:
        return False

def add_to_dict_list(dictionary, key, item):
    '''Add the item to the list stored in the dictionary with
    the specified key. If the key does not exist, create a new
    list.
    '''
    if not dictionary.has_key(key):
        dictionary[key] = []
    dictionary[key].append(item)

def search_directory(directory, depth = -1):
    '''Find all files and directories under a directory tree,
    yielding paths. Depth is the recursion limit:
        0 == yield just the start directory,
        1 == yield start directory and files there,
        -1 == infinite.
    '''
    
    yield directory
    
    if depth == 0 or not os.path.isdir(directory):
        return
    
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if os.path.isdir(filename):
            for path in search_directory(path, depth - 1):
                yield path
        else:
            yield path

def add_to_zip_recursively(zipobj, real_path, root_dir, check_read):
    '''Adds the file at real_path, and if it is a directory,
    all files under it to a ZIP archive.
    Filenames are converted from UTF-8 to CP437.
    Root_dir is stripped from beginning of each file name.
    Check_read is a function that returns False for files that
    should not be included in archive.
    '''
    if not root_dir.endswith('/'):
        root_dir += '/'
    
    for path in search_directory(real_path):
        if not os.path.isdir(path) or not check_read(path):
            continue
        
        assert path[:len(root_dir)] == root_dir
        rel_path = path[len(root_dir):]
        rel_path = rel_path.encode('cp437', 'replace')
        zipobj.write(path, rel_path)

def compare_path(real_path, patterns):
    '''Compare a path to a list of patterns.
    Patterns can be either shell glob patterns that
    are compared against each path component,
    or functions that get passed the complete path.
    '''
    real_path = os.path.normpath(real_path)
    parts = real_path.strip('/').split('/')
    
    for pattern in patterns:
        if callable(pattern):
            if pattern(real_path):
                return True
        else:
            for part in parts:
                if fnmatchcase(part, pattern):
                    return True
    
    return False

if __name__ == '__main__':
    print "Unit tests"
    
    assert path_inside_directory('/tmp/foobar', '/tmp')
    assert path_inside_directory('/', '/')
    assert path_inside_directory('foobar', '')
    assert not path_inside_directory('/', '/tmp')
    assert not path_inside_directory('/tmp/../tmp/..', '/tmp')
    assert not path_inside_directory('..', '')
    
    test_dict = {}
    add_to_dict_list(test_dict, 'ankka', 'heppa')
    add_to_dict_list(test_dict, 'ankka', 'koira')
    assert test_dict['ankka'] == ['heppa', 'koira']
    
    assert compare_etags('"foo"', '"foo"')
    assert not compare_etags('"foo"', '"foo2"')
    assert compare_etags('"foo"', '"foo", "foo2"')
    assert compare_etags('"foo"', '"foo2","foo"')
    assert compare_etags('"foo"', '*')
    assert not compare_etags('"foo"', '')
    
    assert compare_path('/tmp/.svn/foo', ['foo'])
    assert not compare_path('/tmp/.svn/foo2', ['foo'])
    assert compare_path('/tmp/.svn/foo', ['.svn'])
    assert compare_path('/tmp/hack.php', ['*.php'])
    assert compare_path('/tmp/.hack.php', ['*.php'])
    assert compare_path('/tmp/hack.php.txt', ['*.php.*'])
    assert compare_path('/tmp/foo', ['*'])
    
    print "Unit tests OK"
    