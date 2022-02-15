#!python3

import sys
import os
import json
import re
import random
import zipfile


def main(argv):

    preset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets.json")

    try:
        with open(preset_path, 'rb') as f:
            presets = json.loads(f.read().decode(encoding='utf8'))
    except FileNotFoundError:
        print("找不到配置文件 %s。" % os.path.basename(preset_path))

    if len(presets) == 0:
        print("未找到可用的预设。")
        return

    if len(argv) > 1:
        print("用法：main-luogu.py [测试数据存放路径]")
        return
    if len(argv) == 1:
        data_path = argv[0]
    else:
        try:
            data_path = input("输入测试数据存放路径（留空默认为当前路径）：")
        except BaseException:
            data_path = ''
        if data_path == '':
            data_path = '.'

    print("可用的预设：")

    for i in range(0, len(presets)):
        preset = presets[i]
        print("%d. %s" % (i + 1, preset["name"]))
        if preset["description"]:
            desc = preset["description"]
            if "\n" in desc:
                desc = "\n" + desc
            print("  描述：" + desc)
        print("  输入文件：")
        print("    正则：" + preset["input"]["pattern"])
        print("    子任务：" + ",".join(map(str, preset["input"]["subtask"])))
        print("    测试点：" + ",".join(map(str, preset["input"]["case"])))
        print("  输出文件：")
        print("    正则：" + preset["output"]["pattern"])
        print("    子任务：" + ",".join(map(str, preset["output"]["subtask"])))
        print("    测试点：" + ",".join(map(str, preset["output"]["case"])))

    try:
        choice = int(input("输入预设编号："))
        if choice < 1 or choice > len(presets):
            raise ValueError("not in range")
    except ValueError:
        print("预设编号必须为 %d 以内的正整数。" % (len(presets)))
        return
    except EOFError:
        return

    preset = presets[choice - 1]

    re_file = {
        "input": re.compile('^' + preset["input"]["pattern"] + '$'),
        "output": re.compile('^' + preset["output"]["pattern"] + '$')
    }

    subtasks = {}

    def extract_id(mat, arr):
        return tuple(map(lambda x: mat.group(x), arr))

    def find_case(name_subtask, name_case):
        if name_subtask not in subtasks:
            subtasks[name_subtask] = {}
        subtask = subtasks[name_subtask]
        if name_case not in subtask:
            subtask[name_case] = {"input": [], "output": []}
        return subtask[name_case]

    def handle_file(file_path, file_type):
        mat = re_file[file_type].match(file_path.replace('\\', '/'))
        if mat is not None:
            name_subtask = extract_id(mat, preset[file_type]["subtask"])
            name_case = extract_id(mat, preset[file_type]["case"])
            case = find_case(name_subtask, name_case)
            case[file_type].append(file_path)

    for path, dir_list, file_list in os.walk(data_path):
        for file_name in file_list:
            file_path = os.path.relpath(os.path.join(path, file_name), data_path)
            handle_file(file_path, "input")
            handle_file(file_path, "output")

    if len(subtasks) == 0:
        print("未找到匹配的测试点。请检查预设是否正确。")
        return

    print("一共找到了 %d 个子任务。" % len(subtasks))

    name_prefix = input("输入文件名前缀（可以为空）：")

    print("处理结果：")

    error_cnt = 0
    tasks = []
    yaml = []
    id_subtask = 0
    for name_subtask in subtasks:
        id_subtask += 1
        print("子任务 %d：%s" % (id_subtask, ' '.join(name_subtask)))
        subtask = subtasks[name_subtask]
        ind_case = 0
        id_cases = []
        for name_case in subtask:
            ind_case += 1
            print("  测试点 %d：%s" % (ind_case, ' '.join(name_case)))
            case = subtask[name_case]
            print("    输入文件：%s" % ('无' if len(case["input"]) == 0 else ', '.join(case["input"])))
            print("    输出文件：%s" % ('无' if len(case["output"]) == 0 else ', '.join(case["output"])))
            if len(case["input"]) == 1 and len(case["output"]) == 1:
                id_case = "%d-%d" % (id_subtask, ind_case)
                id_cases.append(id_case)
                tasks.append((case["input"][0], "%s%s.in" % (name_prefix, id_case)))
                tasks.append((case["output"][0], "%s%s.ans" % (name_prefix, id_case)))
            else:
                error_cnt += 1
                print("文件数量错误")

        try:
            score = int(input("输入子任务分值："))
        except BaseException:
            score = 0
        for id_case in id_cases:
            yaml.append("%s%s.in:" % (name_prefix, id_case))
            yaml.append("  - score: %d" % score)
            yaml.append("  - subtaskId: %d" % id_subtask)

    if error_cnt:
        print("共有 %d 个测试点文件数量错误。" % error_cnt)

    out_file = os.path.join(data_path, "tmp%d.zip" % random.randint(0, 65535))

    with zipfile.ZipFile(out_file, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('config.yml', '\n'.join(yaml))
        for src, dest in tasks:
            print("正在添加文件：%s => %s" % (src, dest))
            src = os.path.join(data_path, src)
            z.write(src, dest)

    print("操作完成。")
    print("输出文件：%s" % out_file)


if __name__ == "__main__":
    main(sys.argv[1:])
    input("按下回车键以退出：")
