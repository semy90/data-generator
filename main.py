import random
from data import *
import math
from datetime import datetime, timedelta
import pandas as pd


def generate_passport():
    '''генерирует ровно один рф паспорт'''

    otako = str(random.randint(1, 99)).rjust(2,"0")
    if random.random() < 0.1:
        year = str(random.randint(97, 99))
    else:
        year = str(random.randint(0, 27)).rjust(2,"0")
    series = otako + year
    return series + str(random.randint(1, 999999)).rjust(6, "0")


def generate_card(name_bank = None, payment_system = None):
    '''генерирует одну банковскую карту'''
    if name_bank is None:
        name_bank = random.choice(list(BIN_DB.keys()))
    if payment_system is None:
            payment_system = random.choice(list(BIN_DB[name_bank].keys()))
    try:
        card_bin = random.choice(BIN_DB[name_bank][payment_system])
    except KeyError:
        raise KeyError(f"у банка <{name_bank}> нет платежной системы <{payment_system}>")
    return card_bin + str(random.randint(0, 10**10-1)).rjust(10, "0")


def check_wheights(banks):
    s = 0.0

    for bank in banks:
        if isinstance(banks[bank],dict):
            for payment_sys in banks[bank]:
                s += banks[bank][payment_sys]
        elif isinstance(banks[bank], (int, float)):
            s += banks[bank]

    return math.isclose(s, 1.0)


def generate_dict_of_quantity_banks(n, banks):
    '''генерирует словарь количеств каждого банка(и плажных средств если есть)'''
    count_every_bank={}
    if banks is None:
        return {}
    for bank in banks:
        if isinstance(banks[bank], dict):
            count_every_bank[bank] = {}
            for payment_system in banks[bank]:
                count_every_bank[bank][payment_system] = math.ceil(n * banks[bank][payment_system])
        elif isinstance(banks[bank], (float, int)):
            count_every_bank[bank] = math.ceil(n * banks[bank])
    return count_every_bank


def generate_payments(n, count_every_bank):
    '''список из n карт для оплаты; каждая карта повторяется от 1 до 5 раз.
    count_every_bank пустой -> все карты случайные'''
    groups = []
    for bank in count_every_bank:
        if isinstance(count_every_bank[bank], dict):
            for payment_system in count_every_bank[bank]:
                groups.append((bank, payment_system, count_every_bank[bank][payment_system]))
        else:
            groups.append((bank, None, count_every_bank[bank]))
    if not groups:
        groups = [(None, None, n)]

    set_of_cards = set()
    payments = []
    for bank, payment_system, count in groups:
        while count > 0:
            card = generate_card(bank, payment_system)
            while card in set_of_cards:
                card = generate_card(bank, payment_system)
            set_of_cards.add(card)
            repeats = min(random.randint(1, 5), count)
            payments += [card] * repeats
            count -= repeats
    random.shuffle(payments)
    return payments[:n]


def generate_fio():
    gender = random.choice("FM")
    if gender == "M":
        return random.choice(MALE_SURNAMES) + " " + random.choice(MALE_NAMES) + " " + random.choice(MALE_PATRONYMICS)
    else:
        return random.choice(FEMALE_SURNAMES) + " " + random.choice(FEMALE_NAMES) + " " + random.choice(FEMALE_PATRONYMICS)


def travel_hours(distance, train_type):
    return distance / TRAIN_SPEED[train_type]


def calculate_price(distance, base_price):
    price = base_price * (distance / 500)
    return int(round(price / 10) * 10)


def next_departure(not_before, hhmm):
    h, m = map(int, hhmm.split(":"))
    dep = datetime(not_before.year, not_before.month, not_before.day, h, m)
    if dep < not_before:
        dep += timedelta(days=1)
    return dep


def generate_seats(composition, count):
    seats = []
    for car, (car_class, k) in enumerate(composition["cars"], start=1):
        for seat in range(1, k + 1):
            seats.append((car, seat, car_class))
    return random.sample(seats, count)


def generate_trip(train, dep, from_msk, count, payments, set_of_passport):
    arr = dep + timedelta(hours=travel_hours(ROUTE_DISTANCE_KM, train["type"]))
    composition = COMPOSITIONS[train["composition"]]
    rows = []
    for car, seat, car_class in generate_seats(composition, count):
        passport = generate_passport()
        while passport in set_of_passport:
            passport = generate_passport()
        set_of_passport.add(passport)

        card = payments.pop()
        rows.append({
            "ФИО": generate_fio(),
            "Паспортные данные": passport[:4] + " " + passport[4:],
            "Откуда": "Москва" if from_msk else "Санкт-Петербург",
            "Куда": "Санкт-Петербург" if from_msk else "Москва",
            "Дата отъезда": dep.strftime("%Y-%m-%dT%H:%M"),
            "Дата приезда": arr.strftime("%Y-%m-%dT%H:%M"),
            "Рейс": train["from_msk"] if from_msk else train["from_spb"],
            "Вагон и место": f"{car}-{seat}",
            "Стоимость, руб.": calculate_price(ROUTE_DISTANCE_KM, composition["prices"][car_class]),
            "Карта оплаты": " ".join(card[i:i + 4] for i in range(0, 16, 4)),
        })
    return rows, arr


def read_banks():
    banks = {}
    print(TEXT_ABOUT_BANKS)
    k = int(input("Введите колво банков: "))
    for i in range(k):
        *name, part = input().split()
        payment_system = None
        if name[-1] in PAYMENT_SYSTEMS:
            payment_system = name.pop()
        name = " ".join(name)
        if name not in BIN_DB:
            raise ValueError(f"Нет такого банка: {name}")
        if name in banks and (payment_system is None or not isinstance(banks[name], dict)):
            raise ValueError(f"Банк {name} указан повторно")
        if payment_system is None:
            banks[name] = float(part)
        elif payment_system not in BIN_DB[name]:
            raise ValueError(f"У банка {name} нет платежной системы {payment_system}")
        else:
            banks.setdefault(name, {})[payment_system] = float(part)
    if not check_wheights(banks=banks):
        raise ValueError("Сумма распределения не 1!")
    return banks


def main():
    n = int(input("Введите размер датасета: "))
    if n < 50000:
        raise ValueError("Минимальный размер датасета - 50000")

    answer = input("Хотите ли генерировать датасет с определенным распределением платежных систем или банков(y/n)? ")
    if answer == "y":
        banks = read_banks()
    elif answer == "n":
        banks = {}
    else:
        raise ValueError("Вы написали не y и не n! Запустите заново и сделайте правильный выбор!")

    payments = generate_payments(n, generate_dict_of_quantity_banks(n, banks))

    set_of_passport = set()
    rows = []
    state = [[next_departure(datetime(*START_DATE), train["dep_msk"]), True] for train in TRAINS]
    while len(rows) < n:
        for train, st in zip(TRAINS, state):
            if len(rows) >= n:
                break
            dep, from_msk = st
            capacity = sum(k for _, k in COMPOSITIONS[train["composition"]]["cars"])
            count = min(int(capacity * random.uniform(*OCCUPANCY_RANGE)), n - len(rows))
            trip_rows, arr = generate_trip(train, dep, from_msk, count, payments, set_of_passport)
            rows += trip_rows
            back_time = train["dep_spb"] if from_msk else train["dep_msk"]
            st[0] = next_departure(arr + timedelta(days=1), back_time)
            st[1] = not from_msk

    df = pd.DataFrame(rows).sort_values("Дата отъезда")
    df.to_excel("dataset.xlsx", index=False)
    print(f"Готово: dataset.xlsx, строк {len(df)}")


if __name__ == "__main__":
    main()
