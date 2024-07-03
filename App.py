from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Ваш токен бота
BOT_TOKEN = '7213835668:AAE3zQGnqNfMRq7W1EuHAiBLm5d5SFC_7rQ'

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Список групп (Пример)
groups = {"ИП1-21": [], "102": [], "103": []}

teacher_sessions = {}


# Кодовые фразы для учителей
teacher_codes = {
    "учитель1": "учитель123",
    "учитель2": "учитель456",
    "учитель3": "учитель789",
    "учитель4": "учитель012",
    "учитель5": "учитель345"
}

# Определение состояний
class UserStates(StatesGroup):
    choosing_role = State()
    student_group = State()
    teacher_authorization = State()
    teacher_choose_group = State()
    teacher_message = State()


# Клавиатуры
role_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Студент"),
    KeyboardButton("Учитель")
)

change_group_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Изменить группу")
)

group_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for group in groups.keys():
    group_keyboard.add(KeyboardButton(group))

resend_message_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Отправить сообщение заново")
)


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Выберите свою роль.", reply_markup=role_keyboard)
    await UserStates.choosing_role.set()


# Обработчик выбора роли
@dp.message_handler(lambda message: message.text in ["Студент", "Учитель"], state=UserStates.choosing_role)
async def choose_role(message: types.Message, state: FSMContext):
    if message.text == "Студент":
        await message.answer("Введите номер вашей группы:")
        await UserStates.student_group.set()
    elif message.text == "Учитель":
        await message.answer("Введите кодовую фразу для авторизации:")
        await UserStates.teacher_authorization.set()


# Обработчик ввода группы студентом
@dp.message_handler(state=UserStates.student_group)
async def student_group(message: types.Message, state: FSMContext):
    group_number = message.text
    if group_number in groups:
        groups[group_number].append(message.chat.id)
        await message.answer(f"Вы успешно добавлены в группу {group_number}!", reply_markup=change_group_keyboard)
        await state.finish()
    else:
        await message.answer("Такой группы не существует. Попробуйте снова.")


# Обработчик изменения группы студентом
@dp.message_handler(lambda message: message.text == "Изменить группу")
async def change_group(message: types.Message):
    await message.answer("Введите номер вашей группы:")
    await UserStates.student_group.set()


# Обработчик ввода кодовой фразы учителем
@dp.message_handler(state=UserStates.teacher_authorization)
async def teacher_authorization(message: types.Message, state: FSMContext):
    code_phrase = message.text
    teacher_name = None
    for name, code in teacher_codes.items():
        if code == code_phrase:
            teacher_name = name
            break

    if teacher_name:
        teacher_sessions[message.chat.id] = {'name': teacher_name, 'group': None}
        await message.answer(f"Авторизация успешна, {teacher_name}! Выберите группу для отправки сообщения:", reply_markup=group_keyboard)
        await UserStates.teacher_choose_group.set()
    else:
        await message.answer("Неверная кодовая фраза. Попробуйте снова.")



# Обработчик выбора группы учителем
@dp.message_handler(lambda message: message.text in groups.keys(), state=UserStates.teacher_choose_group)
async def teacher_choose_group(message: types.Message, state: FSMContext):
    teacher_sessions[message.chat.id]['group'] = message.text
    await message.answer(f"Вы выбрали группу {message.text}. Введите сообщение для рассылки:")
    await UserStates.teacher_message.set()



# Обработчик отправки сообщения учителем
@dp.message_handler(state=UserStates.teacher_message)
@dp.message_handler(state=UserStates.teacher_message)
async def teacher_message(message: types.Message, state: FSMContext):
    teacher_session = teacher_sessions.get(message.chat.id)
    if not teacher_session or not teacher_session.get('group'):
        await message.answer("Произошла ошибка. Пожалуйста, начните заново.")
        await state.finish()
        return

    selected_group = teacher_session['group']
    teacher_name = teacher_session['name']
    message_text = message.text

    for student_id in groups[selected_group]:
        try:
            await bot.send_message(student_id, f"Сообщение от {teacher_name}: {message_text}")
        except Exception as e:
            print(f"Не удалось отправить сообщение {student_id}: {e}")

    await message.answer("Сообщение успешно отправлено!", reply_markup=resend_message_keyboard)
    await state.finish()


# Обработчик для повторной отправки сообщения учителем
@dp.message_handler(lambda message: message.text == "Отправить сообщение заново")
async def resend_message(message: types.Message, state: FSMContext):
    teacher_sessions[message.chat.id]['group'] = None
    await message.answer("Выберите группу для отправки сообщения:", reply_markup=group_keyboard)
    await UserStates.teacher_choose_group.set()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
