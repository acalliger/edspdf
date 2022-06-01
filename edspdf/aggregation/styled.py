from typing import Dict

import pandas as pd

from edspdf.reg import registry

from .functional import prepare_newlines
from .simple import SimpleAggregator


@registry.aggregators.register("styled.v1")
class StyledAggregator(SimpleAggregator):
    def aggregate(self, lines: pd.DataFrame) -> Dict[str, str]:

        lines["line_id"] = range(len(lines))

        styles = lines[["line_id", "styles"]].explode("styles").dropna().reset_index()
        styles = styles[["line_id"]].join(pd.json_normalize(styles.styles))

        lines = prepare_newlines(
            lines,
            nl_threshold=self.nl_threshold,
            np_threshold=self.np_threshold,
        )

        lines["offset"] = (
            lines["text_with_newline"].str.len().cumsum().shift().fillna(0).astype(int)
        )

        styles = styles.merge(lines[["line_id", "offset", "label"]], on="line_id")
        styles["start"] += styles.offset
        styles["end"] += styles.offset

        df = lines.groupby(["label"]).agg(text=("text_with_newline", "sum"))

        text = df.text.to_dict()
        style = {
            label: styles.query("label == @label")
            .drop(columns=["line_id", "offset", "label"])
            .to_dict(orient="records")
            for label in text.keys()
        }

        return text, style
