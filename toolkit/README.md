# 🤖🔍 HtmlRAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A toolkit to apply HtmlRAG in your own RAG systems.

## 📦 Installation

```bash
pip install -e .
```

---

## 📖 User Guide

### 🧹 HTML Cleaning

```python
from toolkit.HtmlRAG import clean_html

question = "When was the bellagio in las vegas built?"
html = """
<html>
<head>
<title>When was the bellagio in las vegas built?</title>
</head>
<body>
<p class="class0">The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
</body>
<div>
<div>
<p>Some other text</p>
<p>Some other text</p>
</div>
</div>
<p class="class1"></p>
<!-- Some comment -->
<script type="text/javascript">
document.write("Hello World!");
</script>
</html>
"""

simplified_html = clean_html(html)
print(simplified_html)

# <html>
# <title>When was the bellagio in las vegas built?</title>
# <p>The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
# <div>
# <p>Some other text</p>
# <p>Some other text</p>
# </div>
# </html>
```


### 🌲 Build Block Tree

```python
from toolkit.HtmlRAG import build_block_tree

# if you have mutiple HTML documents, merge them using the following code
# simplified_html = "\n".join([clean_html(html) for html in htmls])
block_tree, simplified_html = build_block_tree(simplified_html, max_node_words=10)
for block in block_tree:
    print("Block Content: ", block[0])
    print("Block Path: ", block[1])
    print("Is Leaf: ", block[2])
    print("")

# Block Content:  <title>When was the bellagio in las vegas built?</title>
# Block Path:  ['html', 'title']
# Is Leaf:  True
# 
# Block Content:  <div>
# <p>Some other text</p>
# <p>Some other text</p>
# </div>
# Block Path:  ['html', 'div']
# Is Leaf:  True
# 
# Block Content:  <p>The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
# Block Path:  ['html', 'p']
# Is Leaf:  True
```

### ✂️ Prune HTML Blocks with Embedding Model

```python
from toolkit.HtmlRAG import EmbedHTMLPruner

embed_html_pruner = EmbedHTMLPruner(embed_model="bm25")
block_rankings = embed_html_pruner.calculate_block_rankings(question, simplified_html, block_tree)
print(block_rankings)

# [0, 2, 1]

from transformers import AutoTokenizer

chat_tokenizer = AutoTokenizer.from_pretrained("../../../huggingface/Meta-Llama-3.1-70B-Instruct")

max_context_window = 60
pruned_html = embed_html_pruner.prune_HTML(simplified_html, block_tree, block_rankings, chat_tokenizer,
                                           max_context_window)
print(pruned_html)

# <html>
# <title>When was the bellagio in las vegas built?</title>
# <p>The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
# </html>
```

### 🌲 Build a Finer Block Tree

```python
block_tree, pruned_html=build_block_tree(pruned_html, max_node_words=10)
for block in block_tree:
    print("Block Content: ", block[0])
    print("Block Path: ", block[1])
    print("Is Leaf: ", block[2])
    print("")

# Block Content:  <title>When was the bellagio in las vegas built?</title>
# Block Path:  ['html', 'title']
# Is Leaf:  True
# 
# Block Content:  <p>The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
# Block Path:  ['html', 'p']
# Is Leaf:  True
```
    

### ✂️ Prune HTML Blocks with Generative Model

```python
from toolkit.HtmlRAG import GenHTMLPruner

ckpt_path = "../../../model/train-tree-rerank-phi35-mini/v0915/checkpoint-164"
gen_embed_pruner = GenHTMLPruner(gen_model=ckpt_path, max_node_words=5)
block_rankings = gen_embed_pruner.calculate_block_rankings(question, pruned_html, block_tree)
print(block_rankings)

# [1, 0]

max_context_window = 32
pruned_html = gen_embed_pruner.prune_HTML(pruned_html, block_tree, block_rankings, chat_tokenizer, max_context_window)
print(pruned_html)

# <p>The Bellagio is a luxury hotel and casino located on the Las Vegas Strip in Paradise, Nevada. It was built in 1998.</p>
```