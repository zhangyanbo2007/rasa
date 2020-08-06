import time
list = []
with open("./dialogue_data.md", "r") as f:
    for num, line in enumerate(f):
        if num >= 112:
            if line[0:2] == "* ":
                list.append("\n")
                list.append("## " + line[2:])
                list.append(line)
                list.append("    - utter_"+line[2:])
            else:
                list.append(line)
        else:
            list.append(line)
with open("./dialogue_data.md", "w") as f:
    f.write("".join(list))
