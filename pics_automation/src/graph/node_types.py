import copy
import time
from abc import abstractmethod, ABC


def search_image(img: str, precision: float) -> tuple:
    # todo
    pass


def click_coords(coords: tuple) -> bool:
    # todo
    pass


def parse_coords(coords):
    if isinstance(coords, tuple) and len(coords) == 2 and all(map(lambda x: isinstance(x, int), coords)):
        return coords
    raise ValueError("Coords doesn't match (int, int) type.")


def parse_ordinal(ordinal: str):
    if ordinal.isalpha() and ordinal.islower():
        return ordinal.lower()
    raise ValueError("Node ordinal must be a lowered alphabetical string.")


def parse_img_path(path: str):
    for char in "_.\\/-:":
        path = path.replace(char, '')
    if not path.isalnum():
        raise ValueError("Illegal characters in image path.")
    return True


def resettable(f):
    def __init_and_copy__(self, *args, **kwargs):
        f(self, *args, **kwargs)

        def reset(o=self):
            o.__dict__ = o.__original_dict__
            o.__original_dict__ = copy.deepcopy(self.__dict__)
        self.reset = reset
        self.__original_dict__ = copy.deepcopy(self.__dict__)
    return __init_and_copy__


class _Node(ABC):

    @resettable
    def __init__(self, ordinal: str, telegram_loggable: bool, wait_before_exec: int):
        self._concluded = False
        self._result = None
        self._ordinal = parse_ordinal(ordinal)
        self._telegram_loggable = telegram_loggable
        self._wait_before_exec = wait_before_exec

    def _send_telegram_log(self, message: str = ''):
        # todo
        pass

    def _set_concluded(self):
        self._concluded = True
        if self._telegram_loggable:
            self._send_telegram_log()

    @property
    def run(self):
        try:
            if self._concluded:
                return None
            time.sleep(self._wait_before_exec)
            if c := self.__procedure:
                self._set_concluded()
                self._result = c
                return c
            else:
                return False
        except Exception as e:
            self._send_telegram_log(str(e))

    @property
    def result(self):
        return self._result

    @property
    def force_rerun(self):
        self._concluded = False
        res = self.run
        self._concluded = True
        return res

    @property
    @abstractmethod
    def no_decidable_criteria(self):
        pass

    @property
    @abstractmethod
    def __procedure(self):
        pass


class ClickNode(_Node):

    @resettable
    def __init__(self, ordinal: str, send_telegram_log: bool, get_coords_from_node: _Node = False, coords: tuple = None,
                 wait_before_exec: int = 0):
        super(ClickNode, self).__init__(ordinal, send_telegram_log, wait_before_exec)
        if not get_coords_from_node and not coords:
            raise AttributeError("A ClickNode must either be initialized with a coordinate or get one from another "
                                 "node")
        if coords:
            self._coords = parse_coords(coords)
        else:
            self._get_coords_from_node = get_coords_from_node

    @property
    def no_decidable_criteria(self):
        return True

    @property
    def coords(self):
        if self._coords:
            return self._coords
        else:
            return self._get_coords_from_node.result

    @property
    def __procedure(self):
        if click_coords(self._coords):
            return True


class ImageSearchNode(_Node):

    @resettable
    def __init__(self, ordinal: str, send_telegram_log: bool, image_path, precision, wait_before_exec: int):
        super(ImageSearchNode, self).__init__(ordinal, send_telegram_log, wait_before_exec)
        if parse_img_path(image_path):
            self._image_path = image_path
        self._coords = ()
        self._precision = precision

    @property
    def no_decidable_criteria(self):
        return False

    @property
    def _Node__procedure(self):
        if c := search_image(self._image_path, self._precision):
            self._set_coords(c)
            return self._coords

    def _set_coords(self, c):
        self._coords = c


class ImageSearchAndClickNode(ImageSearchNode):

    @property
    def no_decidable_criteria(self):
        return False

    @property
    def __procedure(self):
        if c := search_image(self._image_path, self._precision):
            self._set_coords(c)
            if click_coords(self._coords):
                return True


class FunctionNode(_Node):

    @resettable
    def __init__(self, ordinal: str, send_telegram_log: bool, wait_before_exec: int, fn, *args, **kwargs):
        super(FunctionNode, self).__init__(ordinal, send_telegram_log, wait_before_exec)
        self._fn = fn
        self._fn_args = args
        self._fn_kwargs = kwargs

    @property
    def no_decidable_criteria(self):
        return False

    @property
    def __procedure(self):
        return self._fn(*self._fn_args, **self._fn_kwargs)


class DefaultNode(FunctionNode):

    @property
    def no_decidable_criteria(self):
        pass


class StartNode(FunctionNode):

    @property
    def _Node__procedure(self):
        return self._fn(*self._fn_args, **self._fn_kwargs)

    @property
    def no_decidable_criteria(self):
        return False


class EndNode(FunctionNode):

    @property
    def _Node__procedure(self):
        return self._fn(*self._fn_args, **self._fn_kwargs)

    @property
    def no_decidable_criteria(self):
        return False
