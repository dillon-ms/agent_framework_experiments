import inspect


class MyPlasticClass:
    def __init__(self):
        self.name = "Plastic"

    def __get_method_n_plus_1(self, new_method_name):
        print(f"Generating method: {new_method_name}")
        def func():
            method_index = int(new_method_name.split("_")[-1])
            following_method_name = f"my_method_{method_index + 1}"
            self.__setattr__(new_method_name, self.__get_method_n_plus_1(following_method_name))
        return func

    def my_method_1(self):
        method_name = inspect.currentframe().f_code.co_name
        print(f"Current method: {method_name}")
        self.__get_method_n_plus_1("my_method_2")()



pc = MyPlasticClass()
pc.my_method_1()
pc.my_method_2()