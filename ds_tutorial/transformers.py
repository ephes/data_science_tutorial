import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin


class EmptyFitMixin:
    def fit(self, x, y=None):
        return self


class TextFromColumns(EmptyFitMixin, BaseEstimator, TransformerMixin):
    """Extract the text from a list of columns in a single pass.

    Takes a pandas dataframe and produces a series of texts
    from joined columns defined in `text_cols`.
    """

    def __init__(self, columns=["title", "body"]):
        self.text_cols = columns

    def transform(self, df):
        def join(items, axis=None):
            return " ".join([str(item) for item in items])

        data = df[self.text_cols].apply(lambda x: "" if x[0] is None else x, axis=1)
        texts = data.apply(join, axis=1)
        return texts


class TextFromColumns2(EmptyFitMixin, BaseEstimator, TransformerMixin):
    """Extract the text from a list of columns in a single pass.

    Takes a pandas dataframe and produces a series of texts
    from joined columns defined in `text_cols`.
    """
    text_cols = ["title", "body"]

    def transform(self, df):
        def join(items, axis=None):
            return " ".join([str(item) for item in items])

        data = df[self.text_cols].apply(lambda x: "" if x[0] is None else x, axis=1)
        texts = data.apply(join, axis=1)
        return texts


class TextStats(BaseEstimator, EmptyFitMixin, TransformerMixin):
    """Extract features from each document"""

    def transform(self, col):
        tc = col.str
        features = [
            tc.len(),  # character count
            tc.count("\n"),  # line count
            tc.count("\."),  # sentence count
            tc.split().apply(lambda x: len(x) if x is not None else 0),  # word count
        ]
        features = np.concatenate([f.values.reshape(-1, 1) for f in features], axis=1)
        where_are_NaNs = np.isnan(features)
        features[where_are_NaNs] = 0
        return features.astype(np.float)


class ColumnSelector(EmptyFitMixin, BaseEstimator, TransformerMixin):
    def __init__(self, column, filter_none=True):
        self.column = column
        self.filter_none = filter_none

    def transform(self, df):
        col = df[self.column]
        if self.filter_none:
            col = col.apply(lambda x: "" if x is None else x)
        return col
