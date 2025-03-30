from collections import UserDict
from datetime import datetime
import pickle


# Клас для базового поля (Field) і його наслідування
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone must have exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        if isinstance(value, str):
            try:
                self.value = datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                raise ValueError("Invalid date format. Use DD.MM.YYYY")
        else:
            raise ValueError("Birthday must be a string in format DD.MM.YYYY")


# Клас Record: запис для контакту
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [
            num_ph for num_ph in self.phones if num_ph.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                return

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if self.birthday:
            today = datetime.today()
            next_birthday = self.birthday.value.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            return (next_birthday - today).days
        return None

    def __str__(self):
        phones_str = ", ".join(phone.value for phone in self.phones)
        birthday_str = self.birthday.value.strftime(
            "%d.%m.%Y") if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {birthday_str}"


# Клас AddressBook
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        today = datetime.today()
        upcoming_birthdays = []
        for rec_birth in self.data.values():
            if rec_birth.birthday:
                next_birthday = rec_birth.birthday.value.replace(
                    year=today.year)
                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)
                if 0 <= (next_birthday - today).days <= days:
                    upcoming_birthdays.append(rec_birth)
        return upcoming_birthdays


# serialisation

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


# deserialisation

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# Декоратор для обробки помилок
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {e}"
        except IndexError:
            return "Error: Missing arguments."
        except Exception as e:
            return f"Unexpected error: {e}"
    return wrapper


# command functions processing
@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2 or not args[1].isdigit():
        raise ValueError("Please provide both name and a valid phone number.")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    record.add_phone(phone)
    return message


@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise ValueError(f"Contact {name} not found in AddressBook.")
    record.edit_phone(old_phone, new_phone)
    return f"Phone number {old_phone} changed to {new_phone} for contact {name}."


@input_error
def show_phones(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError(f"Contact {name} not found in AddressBook.")
    phones = ", ".join(phone.value for phone in record.phones)
    return f"Contact {name}'s phones: {phones}" if phones else f"Contact {name} has no phones."


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "AddressBook is empty."
    result = "All contacts:\n"
    for record in book.data.values():
        result += str(record) + "\n" + ("-" * 20) + "\n"
    return result.strip()


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError(f"Contact {name} not found in AddressBook.")
    record.add_birthday(birthday)
    return f"Birthday {birthday} added for contact {name}."


@input_error
def birthdays(args, book: AddressBook):
    days = int(args[0]) if args else 7
    upcoming_birthdays = book.get_upcoming_birthdays(days)
    if not upcoming_birthdays:
        return "No upcoming birthdays in the next week."
    result = "Upcoming birthdays:\n"
    for record in upcoming_birthdays:
        result += f"{record.name.value}: {record.birthday.value.strftime('%d.%m.%Y')}\n"
    return result.strip()


# Parser for output command
def parse_input(user_input: str):
    if not user_input.strip():
        return "", []
    parts = user_input.strip().split(" ")
    command, args = parts[0], parts[1:]
    return command, args


# Main function
def main():
    book = load_data()  # Завантаження книги з файлу
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if not command:
            print("Please enter a valid command.")
            continue

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)  # Save book to file before exiting
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phones(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
