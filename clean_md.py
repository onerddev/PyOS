import re
import os

def remove_emojis(text):
    # Regex to match characters that are typical of emojis/symbols
    # 2600-27BF are Miscellaneous Symbols and Dingbats
    # 1F000-1FFFF are Supplemental Symbols and Pictographs (Emojis)
    emoji_pattern = re.compile(r'[\U0001f000-\U0001ffff\u2600-\u27bf]', flags=re.UNICODE)
    return emoji_pattern.sub('', text)

files = ['CONTRIBUTING_NEW.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'IMPLEMENTATION_SUMMARY.md', 'PROJECT_SUMMARY.md', 'README.md']
for f in files:
    if os.path.exists(f):
        print(f"Lendo {f}...")
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        new_content = remove_emojis(content)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Processado {f}")
