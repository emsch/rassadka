from itertools import permutations

import pandas as pd

from rassadka_modules.rassadka_exceptions import *
from rassadka_modules.safe_class import SafeClass
from rassadka_modules.common import Ch


class Checker(SafeClass):
    def __setattr__(self, key, value):
        raise PermissionError("Sorry")

    outer_name = inner_name = "Основные настройки"
    settings = dict()
    allowed = set()
    _pre_inited = False

    _required_general_options = {"main_settings"}

    # changed as we add 7th class
    _required_settings_shape = (16, 4)

    _required_settings_options = {
        "cl7_8",
        "cl7_9",
        "cl7_10",
        "cl7_11",
        # the above adds 7th class
        "cl8_9",
        "cl8_10",
        "cl8_11",
        "cl9_10",
        "cl9_11",
        "cl10_11",
        "one_school",
        "one_town",
        "com_in_one",
        "max_compart",
        "debug_mode"}

    kl_comb_names = {
        "cl7_8": (7, 8),
        "cl7_9": (7, 9),
        "cl7_10": (7, 10),
        "cl7_11": (7, 11),
        # the above adds 7th class
        "cl8_9": (8, 9),
        "cl8_10": (8, 10),
        "cl8_11": (8, 11),
        "cl9_10": (9, 10),
        "cl9_11": (9, 11),
        "cl10_11": (10, 11)
    }

    _standard_settings_column_names = ["key", "description", "code", "result"]

    _required_settings_values_condition = {
        "cl7_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl7_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl7_8": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl7_9": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        # the above adds 7th class
        "cl8_9": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl8_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl8_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl9_10": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "cl10_11": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "one_school": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "one_town": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "com_in_one": Ch(lambda x: x in {1, 0}, "in {0, 1}"),
        "max_com_part": Ch(lambda x: 0 <= x <= 1, "0 <= x <= 1"),
        "debug_mode": Ch(lambda x: x in {1, 0}, "in {0, 1}")
    }

    @classmethod
    def _eval_klass_conditions(cls):
        allowed = set()
        for name, item in cls.kl_comb_names.items():
            if cls.settings[name]:
                allowed.update(permutations(item))
        cls.allowed = allowed

    @classmethod
    def _init_settings(cls, matrix):
        # Проверяем наличие ошибок неправильного заполнения таблицы свойств
        if not cls._check_shape(fact=matrix.shape,
                                req=cls._required_settings_shape):
            raise WrongShapeException(fact=matrix.shape,
                                      req=cls._required_settings_shape,
                                      name="Проверка размерности таблицы с общими настройками",
                                      aud=cls.outer_name)
        if not cls._check_nans(fact=matrix):
            raise NansInMatrixException(name="Проверка наличия отсутствующих значений в общих настройках",
                                        aud=cls.outer_name)
        # Чтобы проверить саму табличку надо проделать несколько махинаций, ведь по умолчанию все в виде матриц
        settings = pd.DataFrame(matrix[1:], columns=matrix[0])
        settings.columns = cls._standard_settings_column_names
        settings.set_index("key", inplace=True)
        # Проверяем все ли настнойки внесены в табличку
        if not cls._check_settings(fact=set(settings.index),
                                   req=cls._required_settings_options):
            raise NotEnoughSettings(fact=set(settings.index),
                                    req=cls._required_settings_options,
                                    name="Проверка вхождения всех необходимых\
переменных по ключу в общих настройках",
                                    aud=cls.outer_name)
        # Проверяем, что это именно то, что мы ожидали получить на входе
        if not cls._check_values_condition(fact=settings["code"].to_dict(),
                                           req=cls._required_settings_values_condition):
            raise ValuesConditionException(fact=settings["code"].to_dict(),
                                           req=cls._required_settings_values_condition,
                                           name="Проверка валидности ввода настроек в таблицу с общими настройками",
                                           aud=cls.outer_name)
        cls.settings = settings["code"].to_dict()
    
    @classmethod
    def raw_global_init(cls, raw_settings):
        if cls._pre_inited is True:
            raise PermissionError("Уже инициализирована")
        try:
            if not cls._check_settings(fact=set(raw_settings.keys()),
                                       req=cls._required_general_options):
                raise NotEnoughSettings(fact=set(raw_settings.keys()),
                                        req=cls._required_general_options,
                                        name="Проверка основных тегов на листе",
                                        aud=cls.outer_name)
            cls._init_settings(raw_settings["main_settings"])
            cls._eval_klass_conditions()
        except UserErrorException as e:
            print(e)
            e.log_error()
        cls._pre_inited = True

    @classmethod
    def clean_global_init(cls, clean_settings):
        if cls._pre_inited is True:
            raise PermissionError("Уже инициализирована")
        cls.settings = clean_settings
        cls._eval_klass_conditions()
        cls._pre_inited = True

    def __str__(self):
        res = """
            main_settings:
{0}
""".format(self.settings)
        return res
    
    @classmethod
    def compare(cls, one, two, task):
        """
        Проверка двух экзембляров
        :param one:
        :param two:
        :param task:    (check klass?, check school?)
        :return: bool
        """
        if not one or not two:
            return True

        res = True
        # Проверяем, могут ли классы сидеть вместе
        if task["klass"]:         # первая позиция отвечает за класс
            res &= (one["klass"], two["klass"]) in cls.allowed
        if not cls.settings["one_school"]:
            if task["school"]:         # вторая позиция за школу
                res &= one["school"] != two["school"]
        if not cls.settings["one_town"]:
            if task["town"]:
                if one["town"] != "Москва":
                    res &= one["town"] != two["town"]
        return res

    @classmethod
    def refresh(cls, new_settings):
        cls.settings.update(new_settings)
        cls._eval_klass_conditions()
