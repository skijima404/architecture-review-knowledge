import os
import re
import frontmatter

# 対象フォルダ
SYMPTOM_DIR = "../symptom"  # 必要に応じてパスを変更してください

# 置換マッピング
RELATION_MAP = {
    "caused_by": "triggered_by",
    "triggers_symptoms": "triggers",
    "related_success_criteria": "threatens"
}

def replace_keys_in_yaml(post, mapping):
    updated = False
    metadata = post.metadata
    for old_key, new_key in mapping.items():
        if old_key in metadata:
            metadata[new_key] = metadata.pop(old_key)
            updated = True
    return post, updated

def process_file(filepath):
    post = frontmatter.load(filepath)
    updated_post, changed = replace_keys_in_yaml(post, RELATION_MAP)

    if changed:
        frontmatter.dump(updated_post, filepath, encoding="utf-8")
        print(f"✅ Updated: {filepath}")
    else:
        print(f"⏩ Skipped (no change): {filepath}")

def main():
    for filename in os.listdir(SYMPTOM_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(SYMPTOM_DIR, filename)
            process_file(filepath)

if __name__ == "__main__":
    main()