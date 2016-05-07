import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as etree


MAX_PAGES_TO_LIST = 10


class Template:

    def __init__(self, arguments):
        self.arguments = arguments
        self.page_title = ""


class TemplateArgument:

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.empty = value == ""


class ArgumentCount:

    def __init__(self, name):
        self.name = name
        self.total = 0
        self.non_empty = 0
        self.page_titles = set()

    def __lt__(self, other):
        return self.name < other.name


def main():
    if len(sys.argv) != 3:
        print("Usage: {} SITE TEMPLATE".format(sys.argv[0]))
        sys.exit(1)
    site = sys.argv[1]
    template_name = sys.argv[2]
    page_ids = fetch_transclusions(site, template_name)
    templates = []
    for i, page_id in enumerate(page_ids):
        msg = "Parsing {}/{}: ".format(i + 1, len(page_ids))
        print(msg, end="")
        templates.extend(fetch_and_parse_page(site, page_id, template_name))
    print_counts(count_arguments(templates))


def fetch_transclusions(site, template_name):
    continue_ = None
    transclusions = []
    while True:
        args = {
            "action": "query",
            "titles": template_name,
            "prop": "transcludedin",
            "tilimit": "max",
        }
        if continue_ is not None:
            args["ticontinue"] = continue_
        j = read_api_page(site, args)
        page = list(j["query"]["pages"].values())[0]
        transclusions.extend(page["transcludedin"])
        if "continue" not in j:
            break
        continue_ = j["continue"]["ticontinue"]
    return [t["pageid"] for t in transclusions]


def fetch_and_parse_page(site, page_id, template_name):
    j = read_api_page(site, {
        "action": "parse",
        "pageid": str(page_id),
        "prop": "parsetree",
    })
    title = j["parse"]["title"]
    print("Parsing '{}' ...".format(title))
    tree = j["parse"]["parsetree"]["*"]
    document = etree.fromstring(tree)
    return parse_page(title, document, template_name)


def parse_page(title, document, template_name):
    templates = find_templates(document, template_name)
    for tmpl in templates:
        tmpl.page_title = title
    return templates


def find_templates(document, template_name):
    templates = document.findall(".//template")
    parsed = []
    for tmpl in templates:
        tmpl_name = tmpl.findtext("./title", "").strip()
        if (tmpl_name == template_name or
                ("Template:" + tmpl_name) == template_name):
            parsed.append(parse_template(tmpl))
    return parsed


def parse_template(template):
    parts = template.findall("./part")
    arguments = [parse_template_part(p) for p in parts]
    return Template(arguments)


def parse_template_part(part):
    name = part.findtext("name").strip()
    value = part.findtext("value").strip()
    return TemplateArgument(name, value)


def count_arguments(templates):
    counts = {}
    for tmpl in templates:
        for arg in tmpl.arguments:
            if arg.name not in counts:
                counts[arg.name] = ArgumentCount(arg.name)
            counts[arg.name].total += 1
            if not arg.empty:
                counts[arg.name].non_empty += 1
            counts[arg.name].page_titles.add(tmpl.page_title)
    return counts.values()


def print_counts(counts):
    for count in sorted(counts):
        msg = "{:25} {:5} {:5}".format(
            count.name, count.total, count.non_empty)
        if len(count.page_titles) <= MAX_PAGES_TO_LIST:
            msg += "   " + ", ".join(count.page_titles)
        print(msg)


def read_api_page(site, arguments):
    endpoint = urllib.parse.urljoin(site, "/w/api.php")
    arguments = dict(arguments)
    arguments["format"] = "json"
    url = endpoint + "?" + urllib.parse.urlencode(arguments)
    return read_json_page(url)


def read_json_page(url):
    page = urllib.request.urlopen(url).read().decode("utf-8")
    return json.loads(page)
