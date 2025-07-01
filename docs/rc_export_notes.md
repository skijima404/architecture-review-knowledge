


# Root Cause Graph エクスポート処理：設計＆運用ノート

このドキュメントは、`caused_by` を含む Root Cause ノードのエクスポート処理に関して、設計・実装・トラブルシューティングから得られた知見をまとめたものです。将来的に `triggers_symptoms` や `triggers_root_causes` など他のリレーションを扱う際にも参照できることを目的としています。

---

## ✅ 発生した問題と原因

### 🔹 1. ハイフン直後にスペースがないリスト記述

```yaml
caused_by:
  -"[[rc-020]]"    # ❌ 誤
  - "[[rc-020]]"   # ✅ 正
```

→ YAML パーサが `-` の後のスペースを要求するため、誤記はパースエラーを引き起こす。

---

### 🔹 2. 空のリストの誤記

```yaml
caused_by:
  - []   # ❌ 誤: リスト内に空リストが含まれる
caused_by: []   # ✅ 正
```

→ `- []` は `[[]]` という構造になり、文字列抽出時に失敗する。

---

### 🔹 3. コロンの後にスペースがない

```yaml
caused_by:[]   # ❌ 誤
caused_by: []  # ✅ 正
```

→ YAML の文法上、`:` の後にはスペースが必須。

---

## 🛠 スクリプトへの改善内容

### ✅ エラー検知強化

ファイル単位で YAML パース失敗時にエラー出力されるように `try/except` を追加。

```python
try:
    post = frontmatter.load(f)
except Exception as e:
    print(f"[ERROR] YAML parse failed: {filename}")
    raise e
```

---

### ✅ 空のノードを除外

```python
if rc_id and target_id:
    writer.writerow(...)
```

→ `id_from`, `id_to` が空の行をスキップすることで、CSVのクリーンさを維持。

---

## 🔄 今後の適用対象

- `triggers_symptoms`
- `triggers_root_causes`
- `related_success_criteria`
- `threatened_by`

→ 上記も同様に YAML の構文チェックと空行排除を前提として拡張予定。

---

## 📌 運用上の注意（Writer向け）

- YAML ブロックは `---` で囲み、全てのキーは `:` の後にスペースを入れる
- リストは常に `- "..."` 形式を使う
- 空の配列は `key: []` と明示し、`- []` のようなネストは禁止
- `[[rc-001]]` のような参照リンクは全てダブルクオートで囲む

---

## 🧾 関連ログ・出典

- 2025-07-01: `rc-008` を起点としたYAML構文エラーの調査と解消
- GraphDBエクスポート時の空行混入対策と再設計
