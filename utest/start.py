#!/usr/bin/python3
# coding:utf-8

import sys

sys.path.insert(0, "..")

import types
import unittest
import test_environment
import evalcache
import hashlib


class A:
    def __init__(self):
        self.i = 3

    def summ(self, a, b, c, d):
        return a + b + c + d

    def __repr__(self):
        return "A" + str(self.i)


class TestLazy(unittest.TestCase):
    def tearDown(self):
        test_environment.clean()

    def test_arithmetic_full(self):
        a = test_environment.lazy(1)
        b = test_environment.lazy(2)
        c = test_environment.lazy(3)
        d = test_environment.lazy(4)

        count = (a + b + c).unlazy()
        total_objects = test_environment.count_cached_objects()

        self.assertEqual(count, 6)
        self.assertTrue(total_objects, 2)  # 2 summ

    def test_arithmetic_part(self):
        a = test_environment.lazy(1)
        b = test_environment.lazy(2)
        c = test_environment.lazy(3)
        d = test_environment.lazy(4)

        count = (a + b + c + d).unlazy()
        total_objects = test_environment.count_cached_objects()

        self.assertEqual(count, 10)
        self.assertEqual(total_objects, 3)  # 3 summ

    def test_twoargs(self):
        @test_environment.lazy
        def summ(a, b):
            return a + b

        summ(0, 0).unlazy()
        summ(0, 1).unlazy()
        summ(1, 1).unlazy()
        summ(1, 1).unlazy()
        summ(1, b=1).unlazy()
        summ(a=1, b=1).unlazy()
        summ(b=1, a=1).unlazy()

        total_objects = test_environment.count_cached_objects()
        self.assertEqual(total_objects, 5)

    def test_fibonachi(self):
        @test_environment.lazy
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)

        ret = fib(9).unlazy()

        self.assertEqual(ret, 34)
        self.assertEqual(
            test_environment.count_cached_objects(), 18
        )  # range(0-9) and 8 summ

    # def test_method_strange(self):
    #    A.lazy_sum = types.MethodType( test_environment.lazy(A.summ), A )
    #    ret = A.lazy_sum(1,2,3,d=4)
    #    self.assertEqual(ret.unlazy(), 10)

    def test_method(self):
        class Cls:
            def get_three(self):
                return 3

            def __repr__(self):
                return "Cls"

        Cls.get_three = test_environment.lazy(Cls.get_three)
        a = Cls()
        self.assertEqual(a.get_three().unlazy(), 3)

    def test_getattr(self):
        lazy = evalcache.Lazy(cache={})

        class Cls:
            def __init__(self):
                self.i = 3

            def __repr__(self):
                return "Cls"

        Cls = lazy(Cls)
        a = Cls()

        self.assertEqual(a.i.unlazy(), 3)

    def test_getlazyattr(self):
        lazy = evalcache.LazyHash()

        class Cls:
            def __init__(self):
                self.i = 3

            def foo(self):
                return 4

        Cls.foo = lazy(Cls.foo)
        Cls = lazy(Cls)
        a = Cls()

        self.assertEqual(a.i.unlazy(), 3)
        self.assertEqual(a.foo().unlazy(), 4)


class TestMemoize(unittest.TestCase):
    def tearDown(self):
        test_environment.clean_memoize()

    def test_arithmetic(self):
        @test_environment.memoize
        def maker(n):
            return n

        a = test_environment.memoize(1)
        b = test_environment.memoize(2)
        c = maker(3)
        d = maker(4)

        self.assertEqual(len(test_environment.memoize.cache), 0)  # no unlazy yet

        count = a + b + c + d

        self.assertEqual(len(test_environment.memoize.cache), 5)  # c, d and 3 summ
        self.assertEqual(count, 10)

    def test_fibonachi(self):
        @test_environment.memoize
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)

        ret = fib(9)

        self.assertEqual(ret, 34)
        self.assertEqual(
            len(test_environment.memoize.cache), 19
        )  # range(0-9) and 9 summ and eq(assertEqual)


class TestOnplaceMemoize(unittest.TestCase):
    def tearDown(self):
        test_environment.clean_onplace_memoize()

    def test_arithmetic(self):
        @test_environment.onplace_memoize
        def maker(n):
            return n

        a = test_environment.onplace_memoize(1)
        b = test_environment.onplace_memoize(2)
        c = maker(3)
        d = maker(4)

        self.assertEqual(len(test_environment.onplace_memoize.cache), 2)  # c, d

        count = a + b + c + d

        self.assertEqual(len(test_environment.onplace_memoize.cache), 3)  # c, d and a+b
        self.assertEqual(count, 10)

    def test_fibonachi(self):
        @test_environment.onplace_memoize
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)

        self.assertEqual(fib(9), 34)
        self.assertEqual(len(test_environment.onplace_memoize.cache), 10)  # range(0-9)


class TestOptions(unittest.TestCase):
    def tearDown(self):
        test_environment.clean_onplace_memoize()

    def test_function_dump(self):
        nlazy = evalcache.Lazy(
            cache=evalcache.DirCache(test_environment.dircache_path),
            function_dump=False,
            onplace=True,
        )
        flazy = evalcache.Lazy(
            cache=evalcache.DirCache(test_environment.dircache_path),
            function_dump=True,
            onplace=True,
        )

        lmb_1 = lambda: 1
        lmb_2 = lambda: 2

        nlazy_11 = nlazy(lmb_1, hint="a")()
        nlazy_12 = nlazy(lmb_2, hint="b")()
        nlazy_21 = nlazy(lmb_1)()
        nlazy_22 = nlazy(lmb_2)()

        flazy_11 = flazy(lmb_1, hint="a")()
        flazy_12 = flazy(lmb_2, hint="b")()
        flazy_21 = flazy(lmb_1)()
        flazy_22 = flazy(lmb_2)()

        self.assertNotEqual(nlazy_11, nlazy_12)
        self.assertEqual(nlazy_21, nlazy_22)
        self.assertNotEqual(flazy_11, flazy_12)
        self.assertNotEqual(flazy_21, flazy_22)

class TestAtackStability(unittest.TestCase):
    def tearDown(self):
        test_environment.clean_onplace_memoize()

    def test_function_dump(self):
        nlazy = evalcache.Lazy(
            cache=evalcache.DirCache(test_environment.dircache_path),
            function_dump=False,
            onplace=True,
        )
        
        self.assertNotEqual(
            nlazy((1,10)).__lazyhash__,
            nlazy("<class 'tuple'><splitter>01<splitter>110").__lazyhash__
        )

        self.assertNotEqual(
            nlazy(("<splitter>01<splitter>210,",)).__lazyhash__,
            nlazy((1,10)).__lazyhash__
        )


class TestUnpacking(unittest.TestCase):
    def tearDown(self):
        test_environment.clean_onplace_memoize()

    def test_aaa(self):
        nlazy = evalcache.Lazy(
            cache=evalcache.DirCache(test_environment.dircache_path),
            encache=False,
        )

        class Cls:
            def get_three(self):
                return 3

            def __repr__(self):
                return "Cls"

            def __getitem__(self, i):
                return i

            def __len__(self):
                return 2

        @nlazy
        def foo():
            return Cls()

        a, b = foo()

class TestCachedOperations(unittest.TestCase):
    def tearDown(self):
        test_environment.clean()

    def test_cached_operations(self):
        nlazy = evalcache.Lazy(
            cache=evalcache.DirCache(test_environment.dircache_path),
        )

        i = nlazy(3)
        print(float(i))

        self.assertEqual(i, 3)
        #self.assertEqual(i, 3)


class TestDirCacheClean(unittest.TestCase):
    def tearDown(self):
        test_environment.clean()
        test_environment.full_clean()

    def test_cached_operations(self):
        nlazy = evalcache.Lazy(
            cache=evalcache.DirCache_v2(test_environment.dircache_path2),
        )


def cont_test():
    nlazy = evalcache.Memoize(algo = hashlib.sha512)
    s = {}

    for i in range(0,100):
        for j in range(0,100):
            h = nlazy((i,j)).__lazyhash__

            if h in s:
                print("FAULT:", (i,j), "equal", s[h])
                return

            s[h] = (i,j)

if __name__ == "__main__":
    test_environment.clean()
    cont_test()

    unittest.main()
