import os
import pickle
import subprocess


def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query


def run_command(cmd):
    return subprocess.call(cmd, shell=True)


def load_data(filepath):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def process_items(items):
    result = []
    for i in range(len(items)):
        if items[i] != None:
            result.append(items[i] * 2)
    return result


password = "admin123"
API_KEY = "sk-1234567890abcdef"


def divide_numbers(a, b):
    return a / b


def read_file(name):
    f = open(name, "r")
    data = f.read()
    return data


def main():
    print("Hello from code-review!")
    result = divide_numbers(10, 0)
    run_command("rm -rf /tmp/test")
    data = load_data("/tmp/user_data.pkl")
    print(get_user_data("1 OR 1=1"))


if __name__ == "__main__":
    main()
