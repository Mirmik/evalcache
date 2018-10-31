import evalcache
import evalcache.lazy

from evalcache.lazy import expand, hashfuncs, updatehash_LazyObject, LazyObject
from evalcache.dircache import DirCache

import hashlib
import inspect

import os


class LazyFile:
	"""Декоратор функций создания ленивых файлов."""


    def __init__(self, fcache=DirCache(".evalfile"), algo=hashlib.sha256, encache=True, decache=True, diag=False, onplace=False):
        self.algo = algo
        self.fcache = fcache
        self.encache = encache
        self.decache = decache
        self.diag = diag
        self.onplace = onplace

    def __call__(self, field="path"):
    	"""Параметр указывает, в каком поле передаётся путь к создаваемому файлу"""
        
        def decorator(func):
            return LazyFileMaker(self, func, field)

        return decorator


class LazyFileMaker(LazyObject):
	"""Обёртка - фабрика. Создаёт и тут же расскрывает объект ленивого файла"""

    def __init__(self, lazyfier, value, field):
        LazyObject.__init__(self, lazyfier, value=value)
        self.field = field

    def __call__(self, *args, **kwargs):
        return LazyFileObject(self.__lazybase__, self, args, kwargs).unlazy()


class LazyFileObject(LazyObject):
	"""Объект ленивого файла наследует логику построения хэша от предка, но переопределяет
	логику раскрытия."""

    def __init__(self, *args, **kwargs):
        LazyObject.__init__(self, *args, **kwargs)

    def unlazy(self):
        func = expand(self.generic)
        spec = inspect.getfullargspec(func)

        if self.generic.field in self.kwargs:
            path = self.kwargs[self.generic.field]

        else:
            for i in range(0, len(self.args)):
                if spec.args[i] == self.generic.field:
                    path = self.args[i]
                    break

        if os.path.exists(path):
            os.remove(path)

        path_of_copy = self.__lazybase__.fcache.makePathTo(
            self.__lazyhexhash__)

        if self.__lazyhexhash__ in self.__lazybase__.fcache:
            os.link(path_of_copy, path)
        else:
            args = expand(self.args)
            kwargs = expand(self.kwargs)
            ret = func(*args, **kwargs)
            os.link(path, path_of_copy)


hashfuncs[LazyFileMaker] = updatehash_LazyObject
hashfuncs[LazyFileObject] = updatehash_LazyObject
