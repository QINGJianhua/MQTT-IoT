import json
import re


def comments_strip(stext):
    pattern = r"/\*[^/\*]*\*/"
    text_list = re.split(pattern, stext, maxsplit=0)
    sdata = ''.join(text_list)
    return sdata


def dumps(filename,data):
    with open(filename, 'w') as json_file:
        json_file.write(json.dumps(data))


def loads(filename):
    with open(filename) as json_file:
        json_text = json_file.read()
        json_text = comments_strip(json_text)
        data = json.loads(json_text)
        return data


def _test1():
    data = {"id":"05000001","va":1201}
    dumps('data.json',data)
    data = loads('data.json')

    print(data.get("id"))
    print(data)

def _test2():
    data = '{"id":"05000001","va/*/aa":1201 /* aaaa */}'
    print(comments_strip(data))
    
    
if __name__ == "__main__":
    _test1()
    _test2()
    
    
