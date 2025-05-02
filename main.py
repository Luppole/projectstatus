import os
from collections import defaultdict
from tabulate import tabulate

# Maps file extensions to language names
EXT_LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JSX', '.tsx': 'TSX',
    '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cs': 'C#', '.go': 'Go', '.rs': 'Rust',
    '.swift': 'Swift', '.kt': 'Kotlin', '.m': 'Objective-C', '.rb': 'Ruby', '.php': 'PHP',
    '.html': 'HTML', '.css': 'CSS', '.scss': 'Sass', '.vue': 'Vue', '.sh': 'Shell', '.lua': 'Lua'
}

# Extensions to skip entirely
SKIP_EXTENSIONS = {
    '.json', '.yml', '.yaml', '.xml', '.ini', '.env', '.md',
    '.toml', '.lock', '.txt', '.cfg', '.conf', '.log',
    '.csv', '.tsv', '.db', '.sqlite', '.exe', '.dll', '.zip',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.mp4', '.mp3',
    '.pdf', '.docx', '.pptx'
}

def count_code_lines_by_language(path):
    code_stats = defaultdict(int)
    for root, _, files in os.walk(path):
        for file in files:
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            if ext in SKIP_EXTENSIONS:
                continue
            language = EXT_LANG_MAP.get(ext)
            if not language:
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    code_lines = sum(1 for line in lines if line.strip())
                    code_stats[language] += code_lines
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    return code_stats

def export_to_txt(stats, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tabulate(sorted(stats.items(), key=lambda x: -x[1]), headers=["Language", "Lines of Code"]))
    print(f"\n📁 Results exported to: {output_path}")

def cli(path):
    stats = count_code_lines_by_language(path)
    if not stats:
        print("⚠️ No code files found.")
        return

    while True:
        print("\n📊 Code Line Stats (Sorted):")
        print(tabulate(sorted(stats.items(), key=lambda x: -x[1]), headers=["Language", "Lines of Code"]))
        
        print("\n🛠 Options:")
        print("1. Export to TXT")
        print("2. Show sorted alphabetically")
        print("3. Show top N languages")
        print("4. Exit")
        choice = input("\nEnter option number: ").strip()

        if choice == '1':
            output_path = input("Enter output file path (e.g., results.txt): ").strip()
            export_to_txt(stats, output_path)
        elif choice == '2':
            print(tabulate(sorted(stats.items()), headers=["Language", "Lines of Code"]))
        elif choice == '3':
            n = input("How many top languages to display? ").strip()
            try:
                n = int(n)
                print(tabulate(sorted(stats.items(), key=lambda x: -x[1])[:n], headers=["Language", "Lines of Code"]))
            except:
                print("Invalid number.")
        elif choice == '4':
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python code_line_inspector.py <path_to_project>")
    else:
        cli(sys.argv[1])
