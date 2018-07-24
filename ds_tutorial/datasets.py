from io import StringIO
import xml.etree.ElementTree as _et


class ReutersParser:
    _broken = (
        b"&#1;",
        b"&#2;",
        b"&#3;",
        b"\xfc",
        b"&#5;",
        b"&#22;",
        b"&#27;",
        b"&#30;",
        b"&#31;",
        b"&#127;",
    )

    def cleanup_sgml(self, chunk):
        for item in self._broken:
            chunk = chunk.replace(item, b"")
        chunk = chunk.replace(b'<!DOCTYPE lewis SYSTEM "lewis.dtd">', b"<document>")
        return b"%s</document>" % chunk

    def get_topics(self, topics):
        return [topic.text for topic in topics]

    def get_text(self, text):
        tagmap = dict.fromkeys(("title", "dateline", "body"))
        for item in text:
            tag = item.tag.lower()
            if tag in tagmap:
                tagmap[tag] = item.text
        return tagmap

    def parse_doc(self, elem):
        doc = {}
        doc["attrs"] = dict(elem.items())
        for item in elem:
            if item.tag == "TOPICS":
                doc["topics"] = self.get_topics(item)
            elif item.tag == "DATE":
                doc["date"] = item.text
            elif item.tag == "TEXT":
                doc.update(self.get_text(item))
        return doc

    def parse_sgml(self, filename):
        stream = StringIO(
            self.cleanup_sgml(open(filename, "rb").read()).decode("utf-8")
        )
        for _, elem in _et.iterparse(stream):
            if elem.tag == "REUTERS":
                yield self.parse_doc(elem)


class ReutersCorpus:
    def __init__(self, raw_docs, multiclass=False):
        self.topics = {}
        self.target_names = []

        self.docs = list(self.get_docs(raw_docs))
        if multiclass:
            self.docs = self.filter_multi_label(self.docs)
        self.docs = self.filter_empty_cats(self.docs)

        # labels have to be without gaps
        self._renumber_topics()

    def _renumber_topics(self):
        self.topics = {}
        self.target_names = []
        for doc in self.docs:
            self._add_topics(doc)

    def _add_text(self, doc):
        # doc["text"] = " ".join([doc.get(tag) or "" for tag in
        #    ("title", "dateline", "body")])
        doc["text"] = " ".join([doc.get(tag) or "" for tag in ("dateline", "body")])
        title = " ".join([doc.get("title") or "" for i in range(1)])
        doc["text"] = "%s %s" % (title, doc["text"])

    def _add_modapte(self, doc):
        attrs = doc["attrs"]
        doc["modapte"] = "unused"
        if attrs["LEWISSPLIT"] == "TRAIN" and attrs["TOPICS"] == "YES":
            doc["modapte"] = "train"
        elif attrs["LEWISSPLIT"] == "TEST" and attrs["TOPICS"] == "YES":
            doc["modapte"] = "test"

    def _add_topics(self, doc):
        doc["cats"] = []
        for topic in doc["topics"]:
            if topic not in self.topics:
                self.target_names.append(topic)
                topic_id = len(self.target_names)
                self.topics[topic] = topic_id
            topic_id = self.topics[topic]
            doc["cats"].append(topic_id)

    def get_docs(self, documents):
        modifiers = [self._add_text, self._add_modapte, self._add_topics]
        for doc in documents:
            for modifier in modifiers:
                modifier(doc)
            if doc["modapte"] != "unused":
                yield doc

    def filter_empty_cats(self, docs):
        # modapte yields 90 categories with 1 train and test doc at least
        train, test = set(), set()
        for doc in docs:
            if doc["modapte"] == "train":
                for cat in doc["cats"]:
                    train.add(cat)
            elif doc["modapte"] == "test":
                for cat in doc["cats"]:
                    test.add(cat)
        valid_cats = train.intersection(test)
        new_docs = []
        for doc in docs:
            doc["cats"] = [c for c in doc["cats"] if c in valid_cats]
            if len(doc["cats"]) > 0:
                new_docs.append(doc)
        return new_docs

    def filter_multi_label(self, docs):
        filtered_docs = []
        for doc in docs:
            if len(doc["cats"]) == 1:
                filtered_docs.append(doc)
        return filtered_docs
