import itertools
import string
import random

def generate_sample_patterns(limit_per_group=200):
    patterns = set()
    letters = string.ascii_lowercase
    nums = '0123456789'
    mix = letters + nums + '_.'

    def sample(chars, r, limit):
        cnt = 0
        for combo in itertools.product(chars, repeat=r):
            yield ''.join(combo)
            cnt += 1
            if cnt >= limit:
                break

    for p in sample(letters, 3, limit_per_group):
        patterns.add(p)
    for p in sample(letters, 4, limit_per_group):
        patterns.add(p)
    for p in sample(nums, 3, limit_per_group):
        patterns.add(p)
    for p in sample(nums, 4, limit_per_group):
        patterns.add(p)
    for p in sample(mix, 3, limit_per_group):
        patterns.add(p)
    for p in sample(mix, 4, limit_per_group):
        patterns.add(p)

    real = ['love','dark','soul','life','void','fire','wolf','moon','king','god','luz','vida','alma']
    faces = ['x_x','f_f','o_o','u_u','owo','uwu','-_-']
    for w in real+faces:
        patterns.add(w)
    return list(patterns)

def generate_filtered(charset: str, length: int, starts_with: str = '', ends_with: str = ''):
    chars = {
        'letters': string.ascii_lowercase,
        'numbers': '0123456789',
        'characters': string.ascii_lowercase + '0123456789_.'
    }[charset]
    combos = []
    import itertools
    for combo in itertools.product(chars, repeat=length):
        name = ''.join(combo)
        if starts_with and not name.startswith(starts_with.lower()):
            continue
        if ends_with and not name.endswith(ends_with.lower()):
            continue
        combos.append(name)
        if len(combos) >= 10000:
            break
    return combos
