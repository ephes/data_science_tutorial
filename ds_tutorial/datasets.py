import pandas as pd

from io import StringIO
from collections import Counter
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

    @property
    def number_of_samples(self):
        return len(self.docs)

    @property
    def number_of_classes(self):
        return len([name for name, count in self.topics.items() if count > 1])

    @property
    def texts(self):
        return [d["text"] for d in self.docs]

    @property
    def topic_counts(self):
        counts = Counter()
        for doc in self.docs:
            for topic in doc["cats"]:
                counts[topic] += 1
        return counts

    def top_n(self, n=10):
        topic_lookup = {v: k for k, v in self.topics.items()}
        top_topics = sorted(
            [(v, k) for k, v in self.topic_counts.items()], reverse=True
        )[:n]
        top_n_topics = [
            (topic_lookup[topic_id], topic_id) for (count, topic_id) in top_topics[:n]
        ]
        top_n_ids = [topic_id for (name, topic_id) in top_n_topics]
        top_n_names = [name for name, topic_id in top_n_topics]
        return top_n_ids, top_n_names

    def get_labels(self, docs, top_n):
        labels = []
        for doc in docs:
            # default label is the first one
            label = doc["cats"][0]
            for cat in doc["cats"]:
                if cat in top_n:
                    label = cat
            labels.append(label)
        return labels

    def split_modapte(self):
        train, test = [], []
        for doc in self.docs:
            if doc["modapte"] == "train":
                train.append(doc)
            elif doc["modapte"] == "test":
                test.append(doc)
        return train, test

    def build_dataframe(self, n=10):
        top_ten_ids, top_ten_names = self.top_n(n=n)
        train_docs, test_docs = self.split_modapte()
        docs = train_docs + test_docs
        train_labels = self.get_labels(train_docs, set(top_ten_ids))
        test_labels = self.get_labels(test_docs, set(top_ten_ids))

        labels = train_labels + test_labels
        label_lookup = {}
        num = 0
        for label in sorted(labels):
            if label not in label_lookup:
                label_lookup[label] = num
                num += 1

        topic_lookup = {v: k for k, v in self.topics.items()}
        orig_labels = [topic_lookup[l] for l in labels]

        labels = [label_lookup[l] for l in labels]
        train_labels = [label_lookup[l] for l in train_labels]
        test_labels = [label_lookup[l] for l in test_labels]
        top_ten_ids = [label_lookup[tid] for tid in top_ten_ids]

        # build dataframe
        df = pd.DataFrame()
        df["modapte"] = [d["modapte"] for d in docs]
        df["category"] = orig_labels
        df["label"] = train_labels + test_labels
        df["date"] = [d["date"] for d in docs]
        df["title"] = [d["title"] for d in docs]
        df["dateline"] = [d["dateline"] for d in docs]
        df["body"] = [d["body"] for d in docs]
        df["newid"] = [d["attrs"]["NEWID"] for d in docs]
        df["date"] = pd.to_datetime(
            df.date.str.split(".").apply(lambda x: x[0].lstrip()),
            format="%d-%b-%Y %H:%M:%S",
        )
        df["wd_name"] = df.date.dt.weekday_name
        return df, top_ten_ids, train_labels, test_labels


def build_reuters_dataframe(docs, topics, train_labels, test_labels, top_ten_ids):
    # remove gaps
    labels = train_labels + test_labels
    label_lookup = {}
    num = 0
    for label in sorted(labels):
        if label not in label_lookup:
            label_lookup[label] = num
            num += 1

    topic_lookup = {v: k for k, v in topics.items()}
    orig_labels = [topic_lookup[l] for l in labels]

    labels = [label_lookup[l] for l in labels]
    train_labels = [label_lookup[l] for l in train_labels]
    test_labels = [label_lookup[l] for l in test_labels]
    top_ten_ids = [label_lookup[tid] for tid in top_ten_ids]

    # build dataframe
    df = pd.DataFrame()
    df["modapte"] = [d["modapte"] for d in docs]
    df["category"] = orig_labels
    df["label"] = train_labels + test_labels
    df["date"] = [d["date"] for d in docs]
    df["title"] = [d["title"] for d in docs]
    df["dateline"] = [d["dateline"] for d in docs]
    df["body"] = [d["body"] for d in docs]
    df["newid"] = [d["attrs"]["NEWID"] for d in docs]
    df["date"] = pd.to_datetime(
        df.date.str.split(".").apply(lambda x: x[0].lstrip()),
        format="%d-%b-%Y %H:%M:%S",
    )
    df["wd_name"] = df.date.dt.weekday_name
    return df, top_ten_ids, train_labels, test_labels
