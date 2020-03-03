# testdata-packer-syzoj

## 介绍

这是一个使用 `Python3` 编写，用来自动打包测试数据并生成 syzoj 格式 `data.yml` 的工具。

## 用法

```bash
main.py [测试数据存放路径]
```

## 预设

这个工具支持通过预设来使用正则表达式来匹配测试点的输入输出文件。

程序源文件目录下的 `presets.json` 中描述了所有预设。这个文件在被 `JSON` 解析后应该返回一个数组，其中每个元素描述一个预设。

### 一个例子

假设测试数据存放方式如下：

```plain
subtask1
    data(1).in
    data(1).ans
    data(2).in
    data(2).ans
subtask2
    data(1).in
    data(1).out
    data(2).in
    data(2).out
    data(3).in
    data(3).out
subtask3
    data(1).in
    data(1).ans
```

那么可以编写如下 `JSON` 作为预设：

```json
{
    "name": "预设名",
    "description": "文件命名形如 subtask1/data(1).in",
    "input": {
        "pattern": "subtask(\\d+)/data(\\d+)\\.in",
        "subtask": [1],
        "case": [2]
    },
    "output": {
        "pattern": "subtask(\\d+)/data(\\d+)\\.(out|ans)",
        "subtask": [1],
        "case": [2]
    }
}
```

其中 `input` 和 `output` 的 `pattern` 转义前分别为 `subtask(\d+)/data(\d+)\.in`，`subtask(\d+)/data(\d+)\.(out|ans)`。

### 说明

描述预设的 `JSON` 中各个字段的含义分别是：

- `name`：预设名
- `description`：预设描述
- `input`：输入文件格式
  - `pattern`：用于匹配文件相对路径的正则表达式
  - `subtask`：正则表达式中用于确定测试点所属子任务的组编号
  - `case`：正则表达式中用于区分同一子任务中不同测试点的组编号
- `output`：输出文件格式，与输入文件格式相同

下面重点解释一下匹配过程。

### 正则表达式

正则表达式的定义和具体语法可以参见 [这里](https://zh.wikipedia.org/wiki/%E6%AD%A3%E5%88%99%E8%A1%A8%E8%BE%BE%E5%BC%8F) 或 [这里](https://en.wikipedia.org/wiki/Regular_expression)，此处不再赘述。

正则表达式中的组即为所有被圆括号包含的部分，如上述例子中 `sample.output` 共有三个组，即 `\d+`，`\d+` 和 `out|ans`。

组可以嵌套，如 `([a-z]+(\d+))` 中就出现了组的嵌套，它们分别是 `[a-z]+(\d+)` 和 `\d+`。

组的标号从 `1` 开始，标号顺序由组的左括号在字符串中的位置决定。特别地，整个正则表达式也被看作一个组，它的标号为 `0`。

这个工具会自动在正则表达式的首尾加上 `^` 和 `$`（因此不需要在 `JSON` 文件中显式地添加它们），以确保正则表达式匹配到整个字符串而不是它的子串。

同时，这个工具会自动把路径中的反斜杠 `\` 替换为斜杠 `/` 后进行匹配，因此正则表达式中路径的分隔符统一为 `/`。

### 子任务和测试点的匹配规则

匹配算法会尝试用输入和输出文件的正则表达式来匹配测试数据存放路径下所有的文件，匹配失败的文件会被忽略。

对于匹配成功的所有文件，不同子任务和测试点的区分按如下规则：

1. 如果两个文件对应文件类型指明的 `subtask` 组的匹配结果完全相同，则它们会被认为是属于同一个子任务。
2. 如果两个文件属于同一个子任务，且它们对应文件类型指明的 `case` 组的匹配结果完全相同，则它们会被认为是属于同一个测试点。

例如，假设文件列表如下：

```plain
in/subtaskA/easy-1.in
in/subtask1/easy-1.in
in/subtask1/easy-2.in
in/subtask2/hard-1.in
out/sub1-easy/1.ans
out/sub1-easy/2.ans
out/sub1-easy/3.ans
```

配置 `JSON` 如下（省略了与匹配无关的字段）：

- `input`
    - `pattern`：`in/subtask(\d)/([a-z]+)-(\d)\.in`
    - `subtask`: `[1]`
    - `case`：`[2, 3]`
- `output`
    - `pattern`：`out/sub(\d)-([a-z]+)/(\d)\.ans`
    - `subtask`: `[1]`
    - `case`：`[2, 3]`

那么匹配结果如下：

- 子任务 `1`：
  - 测试点 `easy`, `1`
    - 输入文件：`in/subtask1/easy-1.in`
    - 输出文件：`out/sub1-easy/1.ans`
  - 测试点 `easy`, `2`
    - 输入文件：`in/subtask1/easy-2.in`
    - 输出文件：`out/sub1-easy/2.ans`
  - 测试点 `easy`, `3`
    - 输入文件：无
    - 输出文件：`out/sub1-easy/3.ans`
- 子任务 `2`
  - 测试点 `hard`, `1`
    - 输入文件：`in/subtask2/hard-1.in`
    - 输出文件：无

其中子任务和测试点后的字符串代表对应的组的匹配结果。

如果一个测试点中输入文件或输出文件的数量不为 `1`，那么它会显示警告信息并忽略这个测试点。注意算法不会检查某个测试点的输入和输出文件是否相同，或者同一个文件是否被多个测试点共用。预设的 `JSON` 应当能够避免这种情况。

### 预设文件约定

正则表达式的使用使得预设的编写有了很高的自由度，但预设必须满足几个限制（算法不会试图检查预设是否满足了这些限制）：

1. `JSON` 结构和上述结构相同（可以有附加的字段，但没有任何效果）；
2. `pattern` 是一个合法的正则表达式（注意字符串可能需要转义）；
3. `subtask` 非空，其中每个元素是数字类型，并且组的编号应合法；
5. `input` 和 `output` 中 `subtask` 元素个数相同；
6. `case` 的限制同 `subtask`。

对于不符合上述要求的 `JSON`，不保证程序的运行结果。
