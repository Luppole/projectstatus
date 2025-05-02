import os

# Recognized code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cs',
    '.go', '.rs', '.swift', '.kt', '.m', '.rb', '.php', '.html', '.css',
    '.scss', '.vue', '.sh', '.lua'
}

# Known non-code files to skip (by extension)
SKIP_EXTENSIONS = {
    '.json', '.yml', '.yaml', '.xml', '.ini', '.env', '.md',
    '.toml', '.lock', '.txt', '.cfg', '.conf', '.log',
    '.csv', '.tsv', '.db', '.sqlite', '.exe', '.dll', '.zip',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.mp4', '.mp3',
    '.pdf', '.docx', '.pptx'
}

def count_code_lines(path):
    total_lines = 0
    for root, _, files in os.walk(path):
        for file in files:
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            if ext in CODE_EXTENSIONS and ext not in SKIP_EXTENSIONS:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        code_lines = sum(1 for line in lines if line.strip())
                        total_lines += code_lines
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")
    return total_lines

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python count_clean_code.py <path_to_project>")
    else:
        path = sys.argv[1]
        count = count_code_lines(path)
        print(f"Total lines of code in '{path}': {count}")
