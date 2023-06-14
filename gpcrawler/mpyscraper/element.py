"""Handle extraction of specific elements from response data."""

from html import unescape
from typing import Dict, Callable, List, Any, AnyStr, Optional

from .constants.regex import NOT_NUMBER


def nested_lookup(source: List[Any], indexes: List[int]) -> Any:
    """Recursively lookup an item in a nested list.

    Args:
        source: nested list
        indexes: list of indexes in order of nesting level
    Returns:
        the item in source located at the indexes
        source [
                'DEVELOPER',
                [None, None, None, None, [None, None, 'DEVELOPER_URL']],
                True
               ]
        indexes [1, 4, 2] returns 'DEVELOPER_URL'
    """
    if not source:
        return source
    if len(indexes) == 1:
        return source[indexes[0]]
    if indexes[0] >= len(source):
        return None
    return nested_lookup(source[indexes[0]], indexes[1::])


class ElementSpec:
    def __init__(
        self,
        ds_num: Optional[int],
        data_map: List[int],
        post_processor: Callable = None,
        fallback_value: Any = None,
    ):
        self.ds_num = ds_num
        self.data_map = data_map
        self.post_processor = post_processor
        self.fallback_value = fallback_value

    def extract_content(self, source: dict) -> Any:
        try:
            if self.ds_num is None:
                result = nested_lookup(source, self.data_map)
            else:
                result = nested_lookup(
                    source["ds:{}".format(self.ds_num)], self.data_map
                )

            if self.post_processor is not None:
                result = self.post_processor(result)
        except:
            if isinstance(self.fallback_value, ElementSpec):
                result = self.fallback_value.extract_content(source)
            else:
                result = self.fallback_value

        return result


def unescape_text(text: AnyStr) -> AnyStr:
    """Replace HTML line breaks and return the unescaped text."""
    return unescape(text.replace("<br>", "\r\n"))

def extract_categories(s, categories=[]):
    if s == None or len(s) == 0:
        return categories

    if len(s) >= 4 and type(s[0]) is str:
        categories.append({"name": s[0], "id": s[2]})
    else:
        for sub in s:
            extract_categories(sub, categories)

    return categories

def get_categories(s):
    categories = extract_categories(nested_lookup(s, [118]))
    if len(categories) == 0:
        # add genre and genreId like GP does when there're no categories available
        categories.append(
            {
                "name": nested_lookup(s, [79, 0, 0, 0]),
                "id": nested_lookup(s, [79, 0, 0, 2]),
            }
        )

    return categories

DETAIL = {
    "title": ElementSpec(5, [1, 2, 0, 0]),
    "description": ElementSpec(
        5,
        [1, 2],
        lambda s: unescape_text(
            nested_lookup(s, [12, 0, 0, 1]) or nested_lookup(s, [72, 0, 1])
        ),
    ),
    "descriptionHTML": ElementSpec(
        5,
        [1, 2],
        lambda s: nested_lookup(s, [12, 0, 0, 1]) or nested_lookup(s, [72, 0, 1]),
    ),
    "summary": ElementSpec(5, [1, 2, 73, 0, 1], unescape_text),
    "installs": ElementSpec(5, [1, 2, 13, 0]),
    "minInstalls": ElementSpec(5, [1, 2, 13, 1]),
    "realInstalls": ElementSpec(5, [1, 2, 13, 2]),
    "score": ElementSpec(5, [1, 2, 51, 0, 1]),
    "ratings": ElementSpec(5, [1, 2, 51, 2, 1]),
    "reviews": ElementSpec(5, [1, 2, 51, 3, 1]),
    "histogram": ElementSpec(
        5,
        [1, 2, 51, 1],
        lambda container: [
            container[1][1],
            container[2][1],
            container[3][1],
            container[4][1],
            container[5][1],
        ],
        [0, 0, 0, 0, 0],
    ),
    "price": ElementSpec(
        5, [1, 2, 57, 0, 0, 0, 0, 1, 0, 0], lambda price: (price / 1000000) or 0
    ),
    "free": ElementSpec(5, [1, 2, 57, 0, 0, 0, 0, 1, 0, 0], lambda s: s == 0),
    "currency": ElementSpec(5, [1, 2, 57, 0, 0, 0, 0, 1, 0, 1]),
    "sale": ElementSpec(4, [0, 2, 0, 0, 0, 14, 0, 0], bool, False),
    "saleTime": ElementSpec(4, [0, 2, 0, 0, 0, 14, 0, 0]),
    "originalPrice": ElementSpec(
        3, [0, 2, 0, 0, 0, 1, 1, 0], lambda price: (price / 1000000) or 0
    ),
    "saleText": ElementSpec(4, [0, 2, 0, 0, 0, 14, 1]),
    "offersIAP": ElementSpec(5, [1, 2, 19, 0], bool, False),
    "inAppProductPrice": ElementSpec(5, [1, 2, 19, 0]),
    # "size": ElementSpec(8, [0]),
    # "androidVersion": ElementSpec(5, [1, 2, 140, 1, 1, 0, 0, 1], lambda s: s.split()[0]),
    # "androidVersionText": ElementSpec(5, [1, 2, 140, 1, 1, 0, 0, 1]),
    "developer": ElementSpec(5, [1, 2, 68, 0]),
    "developerId": ElementSpec(5, [1, 2, 68, 1, 4, 2], lambda s: s.split("id=")[1]),
    "developerEmail": ElementSpec(5, [1, 2, 69, 1, 0]),
    "developerWebsite": ElementSpec(5, [1, 2, 69, 0, 5, 2]),
    "developerAddress": ElementSpec(5, [1, 2, 69, 2, 0]),
    "privacyPolicy": ElementSpec(5, [1, 2, 99, 0, 5, 2]),
    # "developerInternalID": ElementSpec(5, [0, 12, 5, 0, 0]),
    "genre": ElementSpec(5, [1, 2, 79, 0, 0, 0]),
    "genreId": ElementSpec(5, [1, 2, 79, 0, 0, 2]),
    "categories": ElementSpec(5, [1, 2], get_categories, []),
    "icon": ElementSpec(5, [1, 2, 95, 0, 3, 2]),
    "headerImage": ElementSpec(5, [1, 2, 96, 0, 3, 2]),
    "screenshots": ElementSpec(
        5, [1, 2, 78, 0], lambda container: [item[3][2] for item in container], []
    ),
    "video": ElementSpec(5, [1, 2, 100, 0, 0, 3, 2]),
    "videoImage": ElementSpec(5, [1, 2, 100, 1, 0, 3, 2]),
    "contentRating": ElementSpec(5, [1, 2, 9, 0]),
    "contentRatingDescription": ElementSpec(5, [1, 2, 9, 2, 1]),
    "adSupported": ElementSpec(5, [1, 2, 48], bool),
    "containsAds": ElementSpec(5, [1, 2, 48], bool, False),
    "released": ElementSpec(5, [1, 2, 10, 0]),
    "updated": ElementSpec(5, [1, 2, 145, 0, 1, 0]),
    "version": ElementSpec(
        5, [1, 2, 140, 0, 0, 0], fallback_value="Varies with device"
    ),
    # "recentChanges": ElementSpec(5, [1, 2, 144, 1, 1], unescape_text),
    # "recentChangesHTML": ElementSpec(5, [1, 2, 144, 1, 1]),
    "comments": ElementSpec(
        8, [0], lambda container: [item[4] for item in container], []
    ),
    # "editorsChoice": ElementSpec(5, [0, 12, 15, 0], bool, False),
    # "similarApps": ElementSpec(
    #     7,
    #     [1, 1, 0, 0, 0],
    #     lambda container: [container[i][12][0] for i in range(0, len(container))],
    # ),
    # "moreByDeveloper": [
    #     ElementSpec(
    #         9,
    #         [0, 1, 0, 0, 0],
    #         lambda container: [
    #             container[i][12][0] for i in range(0, len(container))
    #         ],
    #     ),
    #     ElementSpec(
    #         9,
    #         [0, 1, 0, 6, 0],
    #         lambda container: [
    #             container[i][12][0] for i in range(0, len(container))
    #         ],
    #     ),
    # ],
}

CLUSTER = {
    "cluster": ElementSpec(3, [0, 1, 0, 0, 3, 4, 2]),
    "apps": ElementSpec(3, [0, 1, 0, 0, 0]),
    "token": ElementSpec(3, [0, 1, 0, 0, 7, 1])
}
