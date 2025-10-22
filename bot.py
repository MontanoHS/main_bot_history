import os
import logging
import requests
import json
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
BOT_TOKEN = "8426780934:AAH3B12akGlHF2G8v-JMCyGYK8Sx0Mn65f4"

# API ключ Mistral AI
MISTRAL_API_KEY = "DEjwzJreL18S35aAKXlUPac0zfqhUfnL"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# СИСТЕМА ДОСТИЖЕНИЙ

class UserAchievements:
    def __init__(self, user_id):
        self.user_id = user_id
        self.achievements = {
            'quiz_master': {'name': '🎯 Мастер викторин', 'desc': 'Пройдите викторину на 5/5', 'earned': False, 'progress': 0, 'target': 1},
            'question_pro': {'name': '🔍 Профи вопросов', 'desc': 'Задайте 5 вопросов', 'earned': False, 'progress': 0, 'target': 5},
            'neural_expert': {'name': '🤖 Друг нейросетей', 'desc': 'Используйте нейросеть 3 раза', 'earned': False, 'progress': 0, 'target': 3},
            'rights_expert': {'name': '⚖️ Знаток прав', 'desc': 'Изучите все разделы обучения', 'earned': False, 'progress': 0, 'target': 4},
            'active_citizen': {'name': '🇷🇺 Активный гражданин', 'desc': 'Используйте все функции бота', 'earned': False, 'progress': 0, 'target': 4}
        }
        self.user_stats = {
            'quiz_completed': 0,
            'questions_asked': 0,
            'neural_used': 0,
            'sections_studied': 0,
            'tools_used': 0,
            'quiz_best_score': 0,
            'materials_downloaded': 0
        }

    def update_stat(self, stat_type, value=1):
        if stat_type in self.user_stats:
            self.user_stats[stat_type] += value
            # Обновляем лучший результат в викторине
            if stat_type == 'quiz_completed' and value > 0:
                self.user_stats['quiz_best_score'] = max(self.user_stats['quiz_best_score'], value)
            self._check_achievements()
    
    def _check_achievements(self):
        # Проверяем достижения на основе статистики
        if self.user_stats['quiz_completed'] >= 1 and self.user_stats['quiz_best_score'] >= 5:
            self.achievements['quiz_master']['progress'] = 1
            self.achievements['quiz_master']['earned'] = True
        
        self.achievements['question_pro']['progress'] = min(self.user_stats['questions_asked'], 5)
        if self.user_stats['questions_asked'] >= 5:
            self.achievements['question_pro']['earned'] = True
        
        self.achievements['neural_expert']['progress'] = min(self.user_stats['neural_used'], 3)
        if self.user_stats['neural_used'] >= 3:
            self.achievements['neural_expert']['earned'] = True
        
        self.achievements['rights_expert']['progress'] = min(self.user_stats['sections_studied'], 4)
        if self.user_stats['sections_studied'] >= 4:
            self.achievements['rights_expert']['earned'] = True
        
        self.achievements['active_citizen']['progress'] = min(self.user_stats['tools_used'], 4)
        if self.user_stats['tools_used'] >= 4:
            self.achievements['active_citizen']['earned'] = True
    
    def get_achievements_text(self):
        text = "🏆 Ваши достижения:\n\n"
        earned_count = 0
        total_count = len(self.achievements)
        
        for achievement_id, achievement in self.achievements.items():
            status = "✅" if achievement['earned'] else "🔄"
            progress = f" ({achievement['progress']}/{achievement['target']})" if not achievement['earned'] else ""
            text += f"{status} {achievement['name']}{progress}\n"
            text += f"   └ {achievement['desc']}\n\n"
            
            if achievement['earned']:
                earned_count += 1
        
        text += f"Прогресс: {earned_count}/{total_count} достижений получено"
        return text

# Хранилище достижений пользователей (в реальном проекте используйте БД)
user_achievements_db = {}

def get_user_achievements(user_id):
    if user_id not in user_achievements_db:
        user_achievements_db[user_id] = UserAchievements(user_id)
    return user_achievements_db[user_id]

# ПРАКТИЧЕСКИЕ ИНСТРУМЕНТЫ

class PracticalTools:
    @staticmethod
    def get_election_checklist():
        return """
✅ Чек-лист "Иду на выборы"

📋 Что проверить перед выборами:
• Паспорт гражданина РФ
• Знаю адрес избирательного участка
• Изучил(а) программы кандидатов
• Определил(а) удобное время для голосования

🎯 В день выборов:
• Возьми с собой паспорт
• Приди на участок в удобное время
• Получи бюллетень в комиссии
• Заполни бюллетень в кабинке для голосования
• Опусти бюллетень в урну

💡 Помни:
• Голосование тайное - никто не видит твой выбор
• Если ошибся - можно попросить новый бюллетень
• Голосовать можно только по месту регистрации
        """
    
    @staticmethod
    def get_election_calendar():
        return """
📅 Календарь выборов 2024

🇷🇺 Основные даты:
• 8 сентября 2024 - Единый день голосования
• Выборы губернаторов в 20 регионах
• Выборы депутатов в 15 региональных парламентах
• Муниципальные выборы

⏰ Важные сроки:
• За 45 дней - начало агитации
• За 1 день - день тишины
• С 8:00 до 20:00 - время голосования

🔔 Напоминание: Установи напоминание в телефоне!
        """
    
    @staticmethod
    def find_polling_station():
        return """
🗺️ Найди свой избирательный участок

1. Онлайн:
   • Сайт ЦИК России
   • Портал "Госуслуги"
   • Мобильное приложение "Госуслуги"

2. По документу:
   • Уведомление от УИК
   • Паспорт (прописка)

3. По адресу:
   • Обычно школы, детские сады, учреждения культуры
   • Ближайший к месту жительства

📍 Совет: Уточни адрес заранее!
        """

# ОБРАЗОВАТЕЛЬНЫЙ КОНТЕНТ

class EducationalContent:
    SCENARIOS = {
        "first_time": {
            "title": "🎓 Первый раз на выборах",
            "content": """
🤔 Ты впервые идешь на выборах? Вот что тебя ждет:

1. Подготовка:
   - Проверь, где твой избирательный участок
   - Возьми паспорт
   - Реши, в какое время тебе удобно

2. На участке:
   - Подойди к членам комиссии
   - Предъяви паспорт
   - Получи бюллетень

3. Голосование:
   - Пройди в кабинку для голосования
   - Поставь отметку в бюллетене
   - Опусти бюллетень в урну

🎉 Поздравляю! Ты выполнил(а) гражданский долг!
            """
        },
        "other_city": {
            "title": "✈️ Голосование в другом городе",
            "content": """
🏙️ Находишься не в своем городе в день выборов?

Есть несколько вариантов:

1. Досрочное голосование:
   - Обратись в свою УИК заранее
   - Проголосуй до основного дня

2. Открепительное удостоверение:
   - Получи в своей УИК за 15-4 дня до выборов
   - Проголосуй на любом удобном участке

3. Порядок действий:
   - Узнай в своей УИК о возможности
   - Собери необходимые документы
   - Следи за сроками!

⚠️ Важно: Узнай подробности в своей участковой комиссии!
            """
        },
        "mistake": {
            "title": "❌ Ошибся в бюллетене",
            "content": """
😅 Испортил(а) бюллетень? Не беда!

Правильный порядок действий:

1. Не паникуй!
2. Не выходи из кабинки с испорченным бюллетенем
3. Обратись к члену избирательной комиссии
4. Скажи: "Я испортил(а) бюллетень, прошу выдать новый"
5. Тебе обязаны выдать новый бюллетень
6. Испорченный бюллетень будет погашен

📝 Запомни: Это твое право по статье 69 ФЗ-67!
            """
        }
    }
    
    # Учебные пособия
    STUDY_MATERIALS = {
        "constitution": {
            "title": "📖 Название",
            "description": "Описание",
            "file_url": "https://drive.google.com/file/d/1HbYfa1y9TkHjIp_OYCrKVaIv5fLp0Ast/view?usp=drive_link",  # Замените на реальный URL
            "file_type": "PDF"
        }
    }
    
    @staticmethod
    def get_dictionary():
        return """
📚 Словарь избирательных терминов

• Бюллетень - документ для голосования
• УИК - Участковая избирательная комиссия
• ЦИК - Центральная избирательная комиссия
• День тишины - запрет агитации за сутки до выборов
• Открепительное удостоверение - документ для голосования не по месту прописки
• Электорат - граждане, имеющие право голоса
• Инаугурация - торжественная церемония вступления в должность

💡 Совет: Изучай термины - стань грамотным избирателем!
        """

# КЛАСС ДЛЯ РАБОТЫ С MISTRAL AI

class MistralAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_legal_answer(self, question: str) -> str:
        """
        Получает ответ от Mistral AI в стиле практикующего юриста
        """
        prompt = f"""
        Ты - опытный практикующий юрист, специализирующийся на избирательном праве России. 
        Ответь на вопрос пользователя профессионально, но доступно.
        
        Требования к ответу:
        - Используй юридическую терминологию
        - Ссылайся на конкретные статьи законы (ФЗ-67, Конституция РФ и др.)
        - Структурируй ответ логически
        - Будь точным и лаконичным
        - Объясни сложные моменты простым языком
        
        Вопрос: {question}
        
        Ответ:
        """
        
        data = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": "Ты - опытный юрист по избирательному праву. Давай точные, профессиональные ответы со ссылками на законодательство."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"❌ Ошибка при обращении к Mistral AI: {response.status_code}\n\nПопробуйте позже или задайте вопрос в другом стиле."
                
        except Exception as e:
            return f"❌ Произошла ошибка: {str(e)}\n\nПожалуйста, попробуйте позже."

# Инициализация клиента Mistral AI
mistral_client = MistralAIClient(MISTRAL_API_KEY)

# БАЗА ДАННЫХ ВОПРОСОВ ДЛЯ ВИКТОРИНЫ

class QuizQuestion:
    def __init__(self, question, options, correct_index):
        self.question = question
        self.options = options
        self.correct_index = correct_index

QUIZ_QUESTIONS = [
    QuizQuestion(
        question="С какого возраста гражданин России получает право голосовать на выборах?",
        options=["С 16 лет", "С 18 лет", "С 21 года", "С 25 лет"],
        correct_index=1
    ),
    QuizQuestion(
        question="Можно ли проголосовать за другого человека по его паспорту?",
        options=["Да, если он доверяет", "Только для близких родственников", "Нет, это нарушение", "Только с доверенностью"],
        correct_index=2
    ),
    QuizQuestion(
        question="Что такое 'дневное молчание' в избирательном праве?",
        options=["День без телевизора", "Запрет агитации в день выборов", "Тихий час на участке", "Перерыв в работе комиссии"],
        correct_index=1
    ),
    QuizQuestion(
        question="Можно ли взять бюллетень домой для заполнения?",
        options=["Да, конечно", "Только в особых случаях", "Нет, голосовать только в кабине", "Только инвалидам"],
        correct_index=2
    ),
    QuizQuestion(
        question="Что делать, если ошибся при заполнении бюллетеня?",
        options=["Исправить ошибку", "Попросить новый бюллетень", "Ничего, голос не засчитается", "Отдать испорченный членам комиссии"],
        correct_index=1
    )
]

# СИСТЕМА СТИЛЕЙ ОТВЕТОВ

class AnswerStyle:
    @staticmethod
    def lawyer_style(question: str) -> str:
        answers = {
            "возраст": "👨‍⚖️ Согласно статье 4 Федерального закона №67-ФЗ «Об основных гарантиях избирательных прав», активное избирательное право возникает у граждан Российской Федерации по достижении возраста 18 лет. Данное положение коррелирует с нормами Конституции РФ, устанавливающими полную дееспособность гражданина.",
            "паспорт": "👨‍⚖️ В соответствии с пунктом 2 статьи 64 Федерального закона №67-ФЗ, голосование за другого лица с использованием его документа, удостоверяющего личность, квалифицируется как нарушение избирательного законодательства и влечёт административную ответственность по статье 5.22 КоАП РФ.",
            "молчание": "👨‍⚖️ Согласно статье 45.1 Федерального закона №67-ФЗ, в день голосования и предшествующий ему день запрещается проведение предвыборной агитации. Данный период именуется «днем тишины» и направлен на обеспечение свободного волеизъявления граждан.",
            "бюллетень": "👨‍⚖️ Статья 69 Федерального закона №67-ФЗ明确规定, что заполнение избирательного бюллетеня должно осуществляться в специально оборудованной кабине, иное место для голосования, обеспечивающее тайну волеизъявления. Вынос бюллетеня за пределы помещения для голосования не допускается.",
            "ошибка": "👨‍⚖️ В случае порчи избирательного бюллетеня избиратель вправе обратиться к члену участковой избирательной комиссии с заявлением о выдаче нового бюллетеня, при этом испорченный бюллетень погашается в установленном порядке (пункт 8 статьи 69 Федерального закона №67-ФЗ)."
        }
        return answers.get(question.lower(), "👨‍⚖️ Вопрос требует детального юридического анализа соответствующей нормы избирательного законодательства.")

    @staticmethod
    def student_style(question: str) -> str:
        answers = {
            "возраст": "👨‍🎓 Проще говоря - с 18 лет. Как только тебе исполнилось 18, ты уже полноправный избиратель! Это как получить ключи от взрослой жизни - можно голосовать за президента, депутатов и на референдумах.",
            "паспорт": "👨‍🎓 Ни в коем случае! Это серьезное нарушение. Каждый голосует только за себя лично. Представь, если бы кто-то сдал за тебя экзамен - неправильно же!",
            "молчание": "👨‍🎓 Это когда за сутки до выборов запрещена всякая агитация - никаких плакатов, роликов, раздач листовок. Чтобы люди спокойно подумали и приняли решение без давления.",
            "бюллетень": "👨‍🎓 Нет, бюллетень заполняется только в кабинке для голосования. Это как контрольная работа - пишешь только в аудитории под наблюдением.",
            "ошибка": "👨‍🎓 Если накарябал не то - не страшно! Подойди к члену комиссии и попроси новый бюллетень. Старый заберут и уничтожат, а ты получишь чистый бланк."
        }
        return answers.get(question.lower(), "👨‍🎓 По этому вопросу нужно уточнить в избирательной комиссии или посмотреть в интернете актуальную информацию!")

    @staticmethod
    def grandma_style(question: str) -> str:
        answers = {
            "возраст": "👵 Ой, деточка, голосовать можно как станешь совсем взрослым - в 18 лет! Это как раньше в армию забирали - тоже с 18. Тебе ещё рановато, подрасти немного! 🍪",
            "паспорт": "👵 Ах ты, хитрец! Нет, голосовать за другого - это как есть суп за соседа: и ему не поможешь, и себе живот забьешь! Каждый должен свой суп кушать и своим голосом голосовать! 🍲",
            "молчание": "👵 Это когда перед выборами все успокаиваются, как перед сном! Никто не кричит, не агитирует - тишина, благодать! Чтобы народ без суеты решил, за кого голосовать. 😴",
            "бюллетень": "👵 Нет, милок, бюллетень домой нести - это как из столовой тарелку унести! Заполнил в кабинке - и опустил в урну. Всё по честному! 📝",
            "ошибка": "👵 Испортил бумажку? Не беда! Подойди к тётеньке в комиссии, скажи честно - она тебе новую даст. Они там добрые, помогут! 💕"
        }
        return answers.get(question.lower(), "👵 Ой, милок, я уже не помню такие тонкости! Спроси у молодых, они сейчас всё в интернете знают! 📱")

# СОСТОЯНИЯ FSM

class UserStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_style = State()
    in_quiz = State()
    waiting_for_neural_question = State()

# КЛАВИАТУРЫ

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🎯 Викторина"), KeyboardButton("❓ Задать вопрос"))
    keyboard.add(KeyboardButton("🤖 Нейросеть-юрист"), KeyboardButton("📚 Обучение"))
    keyboard.add(KeyboardButton("🛠️ Инструменты"), KeyboardButton("🏆 Достижения"))
    keyboard.add(KeyboardButton("ℹ️ О проекте"))
    return keyboard

def get_style_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👨‍⚖️ Юрист", callback_data="style_lawyer"),
        InlineKeyboardButton("👨‍🎓 Студент", callback_data="style_student"),
        InlineKeyboardButton("👵 Бабушка", callback_data="style_grandma")
    )
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

def get_quiz_keyboard(question):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i, option in enumerate(question.options):
        keyboard.add(InlineKeyboardButton(option, callback_data=f"quiz_{i}"))
    keyboard.add(InlineKeyboardButton("❌ Отменить викторину", callback_data="cancel_quiz"))
    return keyboard

def get_education_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎓 Первый раз на выборах", callback_data="scenario_first_time"),
        InlineKeyboardButton("✈️ Голосование в другом городе", callback_data="scenario_other_city"),
        InlineKeyboardButton("❌ Ошибся в бюллетене", callback_data="scenario_mistake"),
        InlineKeyboardButton("📚 Словарь терминов", callback_data="dictionary"),
        InlineKeyboardButton("📖 Учебные пособия", callback_data="study_materials"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return keyboard

def get_study_materials_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for material_id, material in EducationalContent.STUDY_MATERIALS.items():
        keyboard.add(InlineKeyboardButton(
            f"{material['title']} ({material['file_type']})", 
            callback_data=f"material_{material_id}"
        ))
    keyboard.add(InlineKeyboardButton("❌ Назад к обучению", callback_data="back_to_education"))
    return keyboard

def get_tools_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✅ Чек-лист 'Иду на выборы'", callback_data="tool_checklist"),
        InlineKeyboardButton("📅 Календарь выборов", callback_data="tool_calendar"),
        InlineKeyboardButton("🗺️ Найти участок", callback_data="tool_station"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return keyboard

def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("❌ Отмена"))
    return keyboard

def get_back_to_main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main"))
    return keyboard

# ОБРАБОТЧИКИ КОМАНД

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = """
👋 Привет! Я бот «Голос Молодёжи»!

Я помогу тебе разобраться в избирательном праве просто и интересно. 

Выбери, что тебя интересует:
"""
    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    
    # Инициализируем достижения для пользователя
    user_achievements = get_user_achievements(message.from_user.id)
    user_achievements.update_stat('tools_used')  # Открытие бота = использование инструмента

@dp.message_handler(lambda message: message.text == "ℹ️ О проекте")
async def about_project(message: types.Message):
    about_text = """
ℹ️ О ПРОЕКТЕ

Мы — группа студентов, создавших этот проект для повышения правовой грамотности молодёжи.

Наша миссия: Показать, что каждый голос важен, а участие в выборах — это просто, значимо и интересно!

Что мы делаем:
• Объясняем избирательное право простым языком
• Помогаем разобраться в процедурах голосования  
• Мотивируем молодёжь активно участвовать в выборах

Присоединяйся к нам! Вместе мы можем изменить будущее! ✨
    """
    await message.answer(about_text)

@dp.message_handler(lambda message: message.text == "🎯 Викторина")
async def start_quiz(message: types.Message):
    await UserStates.in_quiz.set()
    
    # Начинаем с первого вопроса
    question = QUIZ_QUESTIONS[0]
    
    await message.answer(f"🎯 ВИКТОРИНА\n\nВопрос 1/5:\n{question.question}", 
                        reply_markup=get_quiz_keyboard(question))
    
    # Сохраняем состояние
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.update_data(quiz_score=0, current_question=0)

@dp.message_handler(lambda message: message.text == "❓ Задать вопрос")
async def ask_question(message: types.Message):
    style_text = """
❓ ЗАДАТЬ ВОПРОС

Выбери стиль ответа:

• 👨‍⚖️ Юрист - точные формулировки, ссылки на законы
• 👨‍🎓 Студент - простыми словами, как для друга  
• 👵 Бабуля - очень просто, с шутками и аналогиями

Теперь напиши свой вопрос про выборы или избирательное право!
    """
    await message.answer(style_text, reply_markup=get_style_keyboard())
    await UserStates.waiting_for_question.set()

@dp.message_handler(lambda message: message.text == "🤖 Нейросеть-юрист")
async def start_neural_dialog(message: types.Message):
    neural_text = """
🤖 НЕЙРОСЕТЬ-ЮРИСТ

Задайте любой вопрос об избирательном праве, и нейросеть Mistral AI ответит вам как практикующий юрист:

• 📚 Профессиональные консультации
• ⚖️ Ссылки на законы и нормативные акты  
• 🎯 Точные и структурированные ответы
• 💡 Объяснение сложных юридических понятий

Просто напишите ваш вопрос:
    """
    await message.answer(neural_text, reply_markup=get_cancel_keyboard())
    await UserStates.waiting_for_neural_question.set()

@dp.message_handler(lambda message: message.text == "📚 Обучение")
async def show_education(message: types.Message):
    education_text = """
📚 ОБРАЗОВАТЕЛЬНЫЙ РАЗДЕЛ

Выбери интересующую тему:

• 🎓 Первый раз на выборах - пошаговый гид для новичков
• ✈️ Голосование в другом городе - как проголосовать не по месту прописки
• ❌ Ошибся в бюллетене - что делать в такой ситуации
• 📚 Словарь терминов - основные понятия избирательного права
• 📖 Учебные пособия - скачай полезные материалы

Выбирай тему и становись грамотным избирателем! 🎯
    """
    await message.answer(education_text, reply_markup=get_education_keyboard())
    
    # Обновляем статистику
    user_achievements = get_user_achievements(message.from_user.id)
    user_achievements.update_stat('sections_studied')

@dp.message_handler(lambda message: message.text == "🛠️ Инструменты")
async def show_tools(message: types.Message):
    tools_text = """
🛠️ ПРАКТИЧЕСКИЕ ИНСТРУМЕНТЫ

Полезные инструменты для подготовки к выборам:

• ✅ Чек-лист - ничего не забудь перед выборами
• 📅 Календарь - важные даты и сроки
• 🗺️ Найти участок - как узнать где голосовать

Выбирай нужный инструмент! 🔧
    """
    await message.answer(tools_text, reply_markup=get_tools_keyboard())
    
    # Обновляем статистику
    user_achievements = get_user_achievements(message.from_user.id)
    user_achievements.update_stat('tools_used')

@dp.message_handler(lambda message: message.text == "🏆 Достижения")
async def show_achievements(message: types.Message):
    user_achievements = get_user_achievements(message.from_user.id)
    achievements_text = user_achievements.get_achievements_text()
    await message.answer(achievements_text)

# ОБРАБОТЧИКИ ОТМЕНЫ 

@dp.message_handler(lambda message: message.text == "❌ Отмена", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.finish()
    await message.answer("❌ Действие отменено. Возвращаю в главное меню.", reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'cancel', state="*")
async def cancel_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("❌ Действие отменено. Возвращаю в главное меню.")
    await callback_query.message.answer("Выберите действие:", reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'cancel_quiz', state=UserStates.in_quiz)
async def cancel_quiz(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("❌ Викторина отменена. Возвращаю в главное меню.")
    await callback_query.message.answer("Выберите действие:", reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'back_to_education')
async def back_to_education(callback_query: types.CallbackQuery):
    education_text = """
📚 ОБРАЗОВАТЕЛЬНЫЙ РАЗДЕЛ

Выбери интересующую тему:

• 🎓 Первый раз на выборах - пошаговый гид для новичков
• ✈️ Голосование в другом город - как проголосовать не по месту прописки
• ❌ Ошибся в бюллетене - что делать в такой ситуации
• 📚 Словарь терминов - основные понятия избирательного права
• 📖 Учебные пособия - скачай полезные материалы

Выбирай тему и становись грамотным избирателем! 🎯
    """
    await callback_query.message.edit_text(education_text, reply_markup=get_education_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Возвращаю в главное меню.")
    await callback_query.message.answer("Выберите действие:", reply_markup=get_main_keyboard())

# ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ

@dp.callback_query_handler(lambda c: c.data.startswith('style_'), state=UserStates.waiting_for_question)
async def set_answer_style(callback_query: types.CallbackQuery, state: FSMContext):
    style = callback_query.data.split('_')[1]
    await state.update_data(answer_style=style)
    
    style_names = {
        'lawyer': 'юриста',
        'student': 'студента', 
        'grandma': 'бабушку'
    }
    
    await callback_query.message.edit_text(
        f"✅ Выбран стиль {style_names[style]}! Теперь задай свой вопрос текстом.",
        reply_markup=None
    )

@dp.callback_query_handler(lambda c: c.data.startswith('quiz_'), state=UserStates.in_quiz)
async def process_quiz_answer(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    question_index = user_data.get('current_question', 0)
    score = user_data.get('quiz_score', 0)
    
    question = QUIZ_QUESTIONS[question_index]
    selected_answer = int(callback_query.data.split('_')[1])
    
    # Проверка ответа
    if selected_answer == question.correct_index:
        score += 1
        await callback_query.answer("✅ Верно!")
    else:
        correct_answer = question.options[question.correct_index]
        await callback_query.answer(f"❌ Неверно! Правильный ответ: {correct_answer}")
    
    # Переход к следующему вопросу или завершение
    question_index += 1
    if question_index < len(QUIZ_QUESTIONS):
        await state.update_data(quiz_score=score, current_question=question_index)
        next_question = QUIZ_QUESTIONS[question_index]
        
        await callback_query.message.edit_text(
            f"🎯 ВИКТОРИНА\n\nВопрос {question_index + 1}/5:\n{next_question.question}",
            reply_markup=get_quiz_keyboard(next_question)
        )
    else:
        # Завершение викторины
        await state.finish()
        
        # Обновляем статистику достижений
        user_achievements = get_user_achievements(callback_query.from_user.id)
        user_achievements.update_stat('quiz_completed')
        user_achievements.user_stats['quiz_best_score'] = max(user_achievements.user_stats['quiz_best_score'], score)
        user_achievements._check_achievements()
        
        # Оценка результата
        if score == 5:
            result_text = "🎉 Ух ты, я бы на твоём месте пошёл на юриста! Ты отлично разбираешься в избирательном праве!"
        elif score >= 3:
            result_text = "📚 Ты хорошо знаешь избирательное право, но стоит немного подучить отдельные моменты."
        else:
            result_text = "🤔 Я бы тебе посоветовал поподробнее почитать об избирательном праве. Знания - сила!"
        
        result_text += f"\n\nТвой результат: {score} из 5 правильных ответов!"
        
        await callback_query.message.edit_text(result_text)

@dp.callback_query_handler(lambda c: c.data.startswith('scenario_'))
async def show_scenario(callback_query: types.CallbackQuery):
    scenario_id = callback_query.data.split('_')[1]
    
    if scenario_id in EducationalContent.SCENARIOS:
        scenario = EducationalContent.SCENARIOS[scenario_id]
        response_text = f"{scenario['title']}\n\n{scenario['content']}"
        await callback_query.message.edit_text(response_text)
    
    # Обновляем статистику
    user_achievements = get_user_achievements(callback_query.from_user.id)
    user_achievements.update_stat('sections_studied')

@dp.callback_query_handler(lambda c: c.data == 'dictionary')
async def show_dictionary(callback_query: types.CallbackQuery):
    dictionary_text = EducationalContent.get_dictionary()
    await callback_query.message.edit_text(dictionary_text)
    
    # Обновляем статистику
    user_achievements = get_user_achievements(callback_query.from_user.id)
    user_achievements.update_stat('sections_studied')

@dp.callback_query_handler(lambda c: c.data == 'study_materials')
async def show_study_materials(callback_query: types.CallbackQuery):
    materials_text = """
📖 УЧЕБНЫЕ ПОСОБИЯ

Здесь ты можешь скачать полезные материалы по избирательному праву

Выбери пособие для скачивания:
    """
    await callback_query.message.edit_text(materials_text, reply_markup=get_study_materials_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('material_'))
async def send_study_material(callback_query: types.CallbackQuery):
    material_id = callback_query.data.split('_')[1]
    
    if material_id in EducationalContent.STUDY_MATERIALS:
        material = EducationalContent.STUDY_MATERIALS[material_id]
        
        # Отправляем сообщение о загрузке
        await callback_query.message.edit_text(f"📥 Загружаю: {material['title']}\n\n{material['description']}")
        
        try:
            # Отправляем файл
            await bot.send_document(
                chat_id=callback_query.message.chat.id,
                document=material['file_url'],
                caption=f"📖 {material['title']}\n\n{material['description']}\n\nФормат: {material['file_type']}",
                reply_markup=get_back_to_main_keyboard()
            )
            
            # Обновляем статистику
            user_achievements = get_user_achievements(callback_query.from_user.id)
            user_achievements.update_stat('materials_downloaded')
            
        except Exception as e:
            error_text = f"""
❌ Не удалось загрузить файл

{material['title']} временно недоступен.

Причина: {str(e)}

Попробуйте позже или выберите другое пособие.
            """
            await callback_query.message.edit_text(error_text, reply_markup=get_study_materials_keyboard())
    else:
        await callback_query.message.edit_text("❌ Пособие не найдено. Выберите другое.", reply_markup=get_study_materials_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith('tool_'))
async def show_tool(callback_query: types.CallbackQuery):
    tool_id = callback_query.data.split('_')[1]
    
    if tool_id == 'checklist':
        response_text = PracticalTools.get_election_checklist()
    elif tool_id == 'calendar':
        response_text = PracticalTools.get_election_calendar()
    elif tool_id == 'station':
        response_text = PracticalTools.find_polling_station()
    else:
        response_text = "Инструмент временно недоступен"
    
    await callback_query.message.edit_text(response_text)
    
    # Обновляем статистику
    user_achievements = get_user_achievements(callback_query.from_user.id)
    user_achievements.update_stat('tools_used')

# ОБРАБОТЧИК ВОПРОСОВ ПОЛЬЗОВАТЕЛЯ

@dp.message_handler(state=UserStates.waiting_for_question)
async def answer_user_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    style = user_data.get('answer_style', 'student')
    
    question_text = message.text.lower()
    
    # Обновляем статистику
    user_achievements = get_user_achievements(message.from_user.id)
    user_achievements.update_stat('questions_asked')
    
    # Определяем тип вопроса по ключевым словам
    if any(word in question_text for word in ['возраст', 'сколько лет', 'с какого']):
        question_type = "возраст"
    elif any(word in question_text for word in ['паспорт', 'за другого', 'по паспорту']):
        question_type = "паспорт" 
    elif any(word in question_text for word in ['молчание', 'тишина', 'агитац']):
        question_type = "молчание"
    elif any(word in question_text for word in ['бюллетень', 'домой', 'забрать']):
        question_type = "бюллетень"
    elif any(word in question_text for word in ['ошибк', 'испортил', 'неправильно']):
        question_type = "ошибка"
    else:
        question_type = "unknown"
    
    # Генерация ответа в выбранном стиле
    if style == 'lawyer':
        answer = AnswerStyle.lawyer_style(question_type)
    elif style == 'grandma':
        answer = AnswerStyle.grandma_style(question_type)
    else:
        answer = AnswerStyle.student_style(question_type)
    
    if question_type == "unknown":
        answer += "\n\nПока я умею отвечать на основные вопросы про:\n• Возраст голосования\n• Голосование по чужому паспорту\n• День тишины\n• Бюллетени\n• Ошибки при голосовании"
    
    await message.answer(answer, reply_markup=get_main_keyboard())
    await state.finish()

@dp.message_handler(state=UserStates.waiting_for_neural_question)
async def handle_neural_question(message: types.Message, state: FSMContext):
    # Показываем, что бот "печатает"
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Обновляем статистику
    user_achievements = get_user_achievements(message.from_user.id)
    user_achievements.update_stat('neural_used')
    
    # Отправляем вопрос в Mistral AI
    user_question = message.text
    response = mistral_client.get_legal_answer(user_question)
    
    # Форматируем ответ
    formatted_response = f"🤖 Ai-юрист отвечает:\n\n{response}"
    
    await message.answer(formatted_response, reply_markup=get_main_keyboard())
    await state.finish()

# ЗАПУСК БОТА

if __name__ == '__main__':
    print("Бот 'Право на право' запущен!")
    print("Для работы нейросети убедитесь, что указали правильный API ключ")
    print("Замените URL файлов в STUDY_MATERIALS!")
    executor.start_polling(dp, skip_updates=True)