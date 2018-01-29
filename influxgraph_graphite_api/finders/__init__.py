import fnmatch
import os.path
import re

EXPAND_BRACES_RE = re.compile(r'.*(\{.*?[^\\]?\})')


def get_real_metric_path(absolute_path, metric_path):
    # Support symbolic links (real_metric_path ensures proper cache queries)
    real_fs_path = os.path.realpath(absolute_path)
    if absolute_path != real_fs_path:
        relative_fs_path = metric_path.replace('.', os.sep)
        abs_fs_path = os.path.dirname(absolute_path[:-len(relative_fs_path)])
        base_fs_path = os.path.realpath(abs_fs_path)
        relative_real_fs_path = real_fs_path[len(base_fs_path):].lstrip('/')
        return fs_to_metric(relative_real_fs_path)

    return metric_path


def fs_to_metric(path):
    dirpath = os.path.dirname(path)
    filename = os.path.basename(path)
    return os.path.join(dirpath, filename.split('.')[0]).replace(os.sep, '.')


def _deduplicate(entries):
    yielded = set()
    for entry in entries:
        if entry not in yielded:
            yielded.add(entry)
            yield entry


def extract_variants(pattern):
    """Extract the pattern variants (ie. {foo,bar}baz = foobaz or barbaz)."""
    v1, v2 = pattern.find('{'), pattern.find('}')
    if v1 > -1 and v2 > v1:
        variations = pattern[v1+1:v2].split(',')
        variants = [pattern[:v1] + v + pattern[v2+1:] for v in variations]
    else:
        variants = [pattern]
    return list(_deduplicate(variants))


def match_entries(entries, pattern):
    """A drop-in replacement for fnmatch.filter that supports pattern
    variants (ie. {foo,bar}baz = foobaz or barbaz)."""
    matching = []

    for variant in expand_braces(pattern):
        matching.extend(fnmatch.filter(entries, variant))

    return list(_deduplicate(matching))


def expand_braces(pattern):
    """Find the rightmost, innermost set of braces and, if it contains a
    comma-separated list, expand its contents recursively (any of its items
    may itself be a list enclosed in braces).

    Return the full list of expanded strings.
    """
    res = set()

    # Used instead of s.strip('{}') because strip is greedy.
    # We want to remove only ONE leading { and ONE trailing }, if both exist
    def remove_outer_braces(s):
        if s[0] == '{' and s[-1] == '}':
            return s[1:-1]
        return s

    match = EXPAND_BRACES_RE.search(pattern)
    if match is not None:
        sub = match.group(1)
        v1, v2 = match.span(1)
        if "," in sub:
            for pat in sub.strip('{}').split(','):
                subpattern = pattern[:v1] + pat + pattern[v2:]
                res.update(expand_braces(subpattern))
        else:
            subpattern = pattern[:v1] + remove_outer_braces(sub) + pattern[v2:]
            res.update(expand_braces(subpattern))
    else:
        res.add(pattern.replace('\\}', '}'))

    return list(res)
