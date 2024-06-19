import hashlib
import itertools

def hash_string(input_string):
    return hashlib.sha256(input_string.encode()).hexdigest()

def find_original_string(target_hash):
    chars = 'abcd'
    for combination in itertools.product(chars, repeat=13):
        test_string = ''.join(combination)
        if hash_string(test_string) == target_hash:
            return test_string
    return None

# Podany hash do sprawdzenia
target_hash = '629f8548ea05f352dad292a965ccb1e84205116f38bd2fde004a712acaad452c'

# Znajdowanie oryginalnego ciągu znaków
original_string = find_original_string(target_hash)

if original_string:
    print(f'Original string found: {original_string}')
else:
    print('Original string not found.')