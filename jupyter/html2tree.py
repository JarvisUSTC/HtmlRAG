from bs4 import BeautifulSoup
from html4rag.html_utils import simplify_html
from bs4.element import NavigableString

def build_document_tree(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 根节点
    root = {"tag": "root", "children": []}
    stack = [root]  # 栈，用于追踪当前层级的节点

    # 已解析节点集合，存储已处理的节点引用
    parsed_nodes = set()

    # 遍历所有标签
    for tag in soup.descendants:
        # 跳过已解析节点
        if tag in parsed_nodes:
            continue

        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6", "title"] or (tag.name and "html" in tag.name):  # 标题节点: h1-h6, title, html
            if "html" in tag.name:
                node = {"tag": "html", "text": None, "children": []}
                stack[-1]["children"].append(node)
                stack.append(node)
            elif tag.name == "title":
                # 找到之前的html节点，修改其text
                for i in range(len(stack)-1, -1, -1):
                    if stack[i]["tag"] == "html":
                        stack[i]["text"] = tag.get_text()
                        break
                # 如果没有找到html节点，创建一个
                if stack[-1]["tag"] != "html":
                    node = {"tag": "html", "text": tag.get_text(), "children": []}
                    stack[-1]["children"].append(node)
                    stack.append(node)
            else:
              # 先找到最近的层级节点
              if tag.name == stack[-1]["tag"]:
                  # 如果当前标题与前一个标题同级，将当前标题添加到前一个标题的父节点下
                  stack.pop()
              else:
                  # 如果当前标题与前一个标题不同级，那要找到最近的同级标题
                  for i in range(len(stack)-1, -1, -1):
                      if stack[i]["tag"] != "html" and stack[i]["tag"] != "root" and int(stack[i]["tag"][1]) < int(tag.name[1]):
                          stack = stack[:i+1]
                          break
                  if i == 0:
                      stack = [root]
              
              node = {"tag": tag.name, "text": tag.get_text(), "children": []}

              # 插入到栈顶节点的 children 中
              stack[-1]["children"].append(node)

              # 将当前节点推入栈
              stack.append(node)

            # 标记为已解析
            parsed_nodes.add(tag)

        elif tag.name in ["ul", "ol"]:  # 列表节点
            # 找到最近的层级节点
            parent_node = stack[-1]

            # 创建列表节点
            list_node = {"tag": tag.name, "text": None, "children": []}
            parent_node["children"].append(list_node)

            # 遍历所有直接子节点（不限制为 li）
            for child in tag.find_all(recursive=False):
                if child not in parsed_nodes:
                    if child.name == "li":  # 如果是 li，递归解析
                        list_item = build_list_item_node(child, parsed_nodes)
                        if list_item:
                            list_node["children"].append(list_item)
                    else:  # 其他标签，直接添加为子节点
                        text = child.get_text(strip=True)
                        list_node["children"].append({
                            "tag": child.name,
                            "text": text,
                            "children": []
                        })
                    # 标记为已解析
                    parsed_nodes.add(child)

            # 标记当前列表节点为已解析
            parsed_nodes.add(tag)

        elif tag.name == "table":
            # 表格节点
            node = {"tag": "table", "text": str(tag), "children": []}
            stack[-1]["children"].append(node)

            # 标记当前表格及其所有子节点为已解析
            mark_all_children_as_parsed(tag, parsed_nodes)
        
        elif isinstance(tag, NavigableString):
            continue
        
        elif len(tag.find_all(recursive=False)) == 0:
            # 叶子节点
            text = tag.get_text().strip()
            if text:
                node = {"tag": tag.name, "text": text, "children": []}
                stack[-1]["children"].append(node)

    return root

def build_list_item_node(list_item, parsed_nodes):
    """解析列表项及其嵌套内容"""
    direct_text = ''.join(list_item.find_all(text=True, recursive=False)).strip()
    node = {
        "tag": "li",
        "text": direct_text,
        "children": []
    }

    # 遍历子节点，包括可能存在的非列表项
    for child in list_item.find_all(recursive=False):
        if child in parsed_nodes:
            continue

        if child.name in ["ul", "ol"]:  # 嵌套列表
            nested_list = {"tag": child.name, "text": None, "children": []}
            for nested_item in child.find_all("li", recursive=False):
                nested_list_item = build_list_item_node(nested_item, parsed_nodes)
                if nested_list_item:
                    nested_list["children"].append(nested_list_item)
            node["children"].append(nested_list)
            parsed_nodes.add(child)
        elif child.name and child.get_text(strip=True):  # 非 `ul`, `ol` 标签
            child_node = {
                "tag": child.name,
                "text": child.get_text(strip=True),
                "children": []
            }
            node["children"].append(child_node)
            parsed_nodes.add(child)

    parsed_nodes.add(list_item)  # 标记列表项为已解析
    return node

  
def mark_all_children_as_parsed(element, parsed_nodes):
    """递归标记节点及其所有子节点为已解析"""
    parsed_nodes.add(element)
    for child in element.descendants:
        parsed_nodes.add(child)

def remove_nonsemantic_tags(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定义需要保留的语义化标签
    semantic_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "p", "table", "tr", "td"}

    # 遍历所有标签
    for tag in soup.find_all(True):  # True 表示查找所有标签
        if tag.name not in semantic_tags:
            # 替换非语义标签为其内容，移除多余的换行符
            tag.unwrap()
    
    # 去除多余换行符，清理整个文档
    cleaned_html = "".join(soup.prettify().splitlines())
    return cleaned_html

