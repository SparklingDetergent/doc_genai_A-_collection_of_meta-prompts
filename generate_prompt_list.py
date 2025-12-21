
import os
import re

def extract_info(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract H1 title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else ""

        # Generic titles list to avoid
        generic_titles = [
            "Role", "Mission", "Core Mission", "Context & Goal", "概要", "プロンプト",
            "Instruction", "PromptWorkflow", "Instructions", "System Prompt",
            "Constraints & Guidelines", "Steps", "Output Style Examples", "Input Data",
            "User Input", "Processing Steps", "Output Format", "役割", "役割設定",
            "指示", "命令書", "Introduction", "Summary", "Usage", "Details", "About",
            "チェックする対象", "処理の流れ", "出力形式", "文章", "最適化されたプロンプト",
            "プロンプト分析レポート", "プロンプト診断レポート", "改善版プロンプト", "フェーズ1", "フェーズ2",
            "タイルのサンプル", "英語版なので 注意。"
        ]

        # If title is missing or generic, use directory name
        # Also clean up title if it contains "Role" or similar
        dir_name = os.path.basename(os.path.dirname(filepath))

        if not title or any(g.lower() in title.lower() for g in generic_titles) or len(title) < 5:
             # Check if the title is actually descriptive enough even if it contains a generic word
             # For now, let's prefer the directory name if the extracted title is suspect
             title = dir_name

        # Extract Description
        description = ""

        # Priority 1: Specific Headers
        headers_to_look = ["Core Mission", "Role", "ミッション", "概要", "Context & Goal", "あなたの役割", "Role Definition", "Description"]

        for header in headers_to_look:
            pattern = re.compile(r'^#+\s+' + re.escape(header) + r'\s*\n(.+?)(?=\n#|\Z)', re.MULTILINE | re.DOTALL | re.IGNORECASE)
            match = pattern.search(content)
            if match:
                description = match.group(1).strip()
                break

        # Priority 2: First meaningful paragraph
        if not description:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('```') and not line.startswith('{{') and not line.startswith('!['):
                    description = line
                    break

        # Clean up description
        # Remove newlines to make it fit in one line
        description = description.replace('\n', ' ').strip()

        # Increase limit to avoid truncation
        if len(description) > 300:
            description = description[:297] + "..."

        return title, description

    except Exception as e:
        return os.path.basename(os.path.dirname(filepath)), ""

def main():
    root_dirs = ['Coding', 'PromptChallenge', 'collection1', 'collection2', 'etc']
    results = []

    for root_dir in root_dirs:
        if not os.path.exists(root_dir):
            continue

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames.sort()
            filenames.sort()

            for filename in filenames:
                if filename.lower() == 'readme.md':
                    # Use the actual filename found to preserve case
                    filepath = os.path.join(dirpath, filename)

                    title, description = extract_info(filepath)

                    # Create a relative path for the link
                    rel_path = filepath

                    results.append({
                        'path': rel_path,
                        'folder': dirpath,
                        'title': title,
                        'description': description
                    })

    # Generate Markdown
    print("# プロンプト一覧と使用ガイド\n")
    print("このリポジトリに含まれるプロンプトのリストです。各プロンプトの概要とリンクをまとめています。\n")
    print("| カテゴリ | プロンプト名 | 概要/用途 |")
    print("| :--- | :--- | :--- |")

    for item in results:
        category = item['folder'].split(os.sep)[0]
        # Escape pipe characters
        name = f"[{item['title']}]({item['path']})"
        desc = item['description'].replace('|', '\\|')
        print(f"| {category} | {name} | {desc} |")

if __name__ == "__main__":
    main()
