import telebot
import random
import threading
import time
from telebot import types
from functools import wraps
import os

BOT_TOKEN = 'Token'
bot = telebot.TeleBot(BOT_TOKEN)

user_scores = {}
admin_ids = [6849235855,6849235855]
game_start_times = {}
reedem_codes = {}
current_word = {}
game_active = False
last_word_time = 0

## Kullanıcının kanalda ve sohbette olup olmadığını kontrol eden dekoratör
# Gerekli kanal ve sohbet ID'leri
required_channel_id = -1001726075997  # Kanal ID'si (Buton1)
required_chat_id = -1002066666012     # Sohbet ID'si (Buton2)

# Kullanıcının kanalda ve sohbette olup olmadığını kontrol eden dekoratör
def kanalz(func):
    def wrapper(message):
        user_id = message.from_user.id
        allowed_status = ['member', 'administrator', 'creator']
        
        # Kullanıcının hem kanalda hem de sohbette olup olmadığını kontrol et
        chat_member_channel = bot.get_chat_member(required_channel_id, user_id)
        chat_member_chat = bot.get_chat_member(required_chat_id, user_id)

        if chat_member_channel.status in allowed_status and chat_member_chat.status in allowed_status:
            return func(message)
        else:
            # Eğer kullanıcı her iki yere de üye değilse, yönlendirme butonlarını göster
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Katıl 🗃️ Kanal", url="Https://T.Me/japearsiv
            markup.add(InlineKeyboardButton("💬 Katıl 📝 Sohbet", url="https://t.me/+TljnbAYcGuEyNDI0"))
            markup.add(InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeltag_bey"))
            
            bot.send_message(message.chat.id, "❗ Lütfen aşağıdaki kanal ve sohbete katılın: 👇", reply_markup=markup)
    
    return wrapper

def kanalz(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        not_joined_channels = []

        for channel in required_channels:
            try:
                member_status = bot.get_chat_member(channel["id"], user_id).status
                if member_status not in ['member', 'administrator', 'creator']:
                    not_joined_channels.append(channel)
            except telebot.apihelper.ApiException as e:
                bot.reply_to(message, f"{channel['name']} kanalına erişim sağlanamadı: {e.result_json['description']}")
                return

        if not_joined_channels:
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = []
            
            # Her kanal için kullanıcı adını ID'den alıyoruz ve buton oluşturuyoruz
            for ch in not_joined_channels:
                try:
                    chat_info = bot.get_chat(ch["id"])
                    username = chat_info.username
                    if username:
                        url = f"https://t.me/{username}"
                        buttons.append(types.InlineKeyboardButton(text=ch["name"], url=url))
                    else:
                        bot.reply_to(message, f"{ch['name']} kanalında bir kullanıcı adı bulunamadı.")
                        return
                except telebot.apihelper.ApiException as e:
                    bot.reply_to(message, f"{ch['name']} kanalının bilgilerine erişim sağlanamadı: {e.result_json['description']}")
                    return

            markup.add(*buttons)
            bot.reply_to(message, "Önce aşağıdaki kanallara katılın!", reply_markup=markup)
            return

        return func(message, *args, **kwargs)
    return wrapper

# Kelime ve ipucu çiftleri
word_hint_pairs = [
    ("telefon", "Elle tutulabilen çok özellikli alet"),
    ("televizyon", "Küçük sinemaya benzer alet"),
    ("bilgisayar", "İnternet bağlantısı ve program çalıştırma yeteneği olan cihaz"),
    ("buzdolabı", "Yiyecekleri soğuk tutmaya yarayan ev aleti"),
    ("masa", "Üzerine bir şeyler koyabileceğiniz mobilya")
]

# Oyun başlatma
@bot.message_handler(commands=['kelime'])
@kanalz
def start_game(message):
    global game_active, last_word_time
    if game_active:
        bot.reply_to(message, "Oyun zaten başlatıldı.")
        return

    game_active = True
    bot.reply_to(message, "Oyun Başladı!")
    start_new_word(message.chat.id)
    last_word_time = time.time()

# Yeni kelime başlatma fonksiyonu
def start_new_word(chat_id):
    global last_word_time
    pair = random.choice(word_hint_pairs)
    word, hint = pair
    current_word[chat_id] = word  # Kelimeyi saklıyoruz
    bot.send_message(chat_id, f"Yeni kelimenin ipucu: {hint}")
    last_word_time = time.time()

# Tahmini kontrol etme
@bot.message_handler(func=lambda message: game_active and not (message.text.startswith('/') or message.text.startswith('.')))
def check_word_guess(message):
    chat_id = message.chat.id
    guess = message.text.lower().strip()  # Tahmini küçük harfe çeviriyoruz
    if chat_id in current_word and guess == current_word[chat_id]:
        bot.reply_to(message, "🎉 Doğru tahmin! 10 puan kazandınız.")
        user_scores[message.from_user.id] = user_scores.get(message.from_user.id, 0) + 10
        del current_word[chat_id]
        start_new_word(chat_id)
    elif chat_id in current_word:
        bot.reply_to(message, "❌ Yanlış tahmin. Tekrar deneyin.")

# Kelimeyi atlama
@bot.message_handler(commands=['skip'])
@kanalz
def skip_word(message):
    global last_word_time
    if not game_active:
        bot.reply_to(message, "Oyun henüz başlamadı. /kelime komutunu kullanarak başlatabilirsiniz.")
        return

    if time.time() - last_word_time < 30:
        bot.reply_to(message, "Kelimeyi atlamak için en az 30 saniye geçmesi gerekiyor.")
        return

    chat_id = message.chat.id
    if chat_id in current_word:
        old_word = current_word[chat_id]
        bot.send_message(message.chat.id, f"Kelime atlandı. Doğru kelime `{old_word}` idi.")
        del current_word[chat_id]
        start_new_word(chat_id)
    else:
        bot.reply_to(message, "Şu anda geçerli bir kelime yok.")

# Oyunu bitirme
@bot.message_handler(commands=['kelimebitir'])
@kanalz
def end_game(message):
    global game_active
    if not game_active:
        bot.reply_to(message, "Oyun zaten bitmiş.")
        return

    game_active = False
    chat_id = message.chat.id
    last_word = current_word.get(chat_id, 'yok')
    bot.reply_to(message, f"Oyun bitti. Doğru kelime `{last_word}` idi.")

    if user_scores:
        sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        score_message = "En Fazla Skora Sahip Kullanıcılar:\n"
        for i, (user_id, score) in enumerate(sorted_scores[:10], start=1):
            user_info = bot.get_chat(user_id)
            score_message += f"{i}. {user_info.first_name} - {score}₺\n"
        bot.send_message(message.chat.id, score_message)
    else:
        bot.send_message(message.chat.id, "Kimse puan kazanamadı.")

    current_word.clear()
    user_scores.clear()

# Kullanıcının bakiyesini gösterme
@bot.message_handler(commands=['bakiye'])
@kanalz
def check_balance(message):
    user_id = message.from_user.id
    balance = user_scores.get(user_id, 0)
    bot.reply_to(message, f"Bakiyeniz: {balance}₺")

# Redeem kodunu kullanma
@bot.message_handler(commands=['reedem'])
@kanalz
def redeem(message):
    try:
        _, code = message.text.split()
        if code not in reedem_codes:
            bot.reply_to(message, "Bu Kod Geçersizdir Lütfen Doğruluğundan emin olun yada Bot sahibinden yenisini isteyin")
            return
        
        if reedem_codes[code]['max'] != 0 and reedem_codes[code]['used'] >= reedem_codes[code]['max']:
            bot.reply_to(message, "Bu kodun kullanım limiti dolmuştur.")
            return

        user_id = message.from_user.id
        if user_id not in user_scores:
            user_scores[user_id] = 0
        
        user_scores[user_id] += reedem_codes[code]['value']
        reedem_codes[code]['used'] += 1

        bot.reply_to(message, f"Tebrikler! Bakiyenize {reedem_codes[code]['value']}₺ eklenmiştir.")
    except ValueError:
        bot.reply_to(message, "Lütfen doğru formatta komut girin: /reedem <KOD>")

# Ürünlerin ve dosyalarının listesi
market_items = {
    1: {'name': 'BluTV Random', 'price': 15, 'file': 'blutv.txt'},
    2: {'name': 'PreDünyam Random', 'price': 30, 'file': 'predunyam.txt'},
    3: {'name': 'Exxen Random', 'price': 40, 'file': 'exxen.txt'},
    #Her Bir Ürün için No İsim fiyat ve combonun adını gir örnek: 
    4: {'name': 'Netflix Random', 'price': 90, 'file': 'netflix.txt'},
}

user_scores = {}
user_purchases = {}

def get_random_line(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        return random.choice(lines).strip()

def format_market_list():
    market_list = "🛒 Marketimiz\n\n"
    for item_id, item_info in market_items.items():
        market_list += f"{item_id}. {item_info['name']} {item_info['price']}₺\n"
    return market_list

@bot.message_handler(commands=['market'])
@kanalz
def market(message):
    response_message = format_market_list()
    bot.send_message(message.chat.id, response_message)

@bot.message_handler(commands=['al'])
@kanalz
def buy_item(message):
    user_id = message.from_user.id
    text = message.text.split()
    if len(text) != 2:
        bot.reply_to(message, "Geçersiz komut. Lütfen ürün numarasını belirtin.")
        return

    item_number = int(text[1])
    if item_number not in market_items:
        bot.reply_to(message, "Geçersiz ürün numarası.")
        return

    item_info = market_items[item_number]
    price = item_info['price']
    file_path = item_info['file']

    if user_id not in user_scores:
        user_scores[user_id] = 0

    if user_scores[user_id] < price:
        bot.reply_to(message, "Yeterli bakiyeniz yok.")
        return

    user_scores[user_id] -= price
    content = get_random_line(file_path)
    bot.send_message(message.chat.id, f"{content}\n\nBakiyenizden {price}₺ eksilmiştir.")

user_referals = {}
user_started = set()  # Giriş yapan kullanıcıları takip etmek için

def generate_referral_link(user_id):
    bot_username = 'BotAdı_bot'  # Bot kullanıcı adınızı buraya yazın
    return f"https://t.me/{bot_username}?start={user_id}"

def add_points(user_id, points):
    if user_id not in user_scores:
        user_scores[user_id] = 0
    user_scores[user_id] += points

def handle_new_user_referral(referred_user_id, referrer_user_id):
    if referrer_user_id in user_scores:
        add_points(referrer_user_id, 20)
        bot.send_message(
            referrer_user_id,
            f"{referred_user_id} Referans Linkiniz ile girdiğinden 20₺ kazandınız"
        )

@bot.message_handler(commands=['referans'])
@kanalz
def handle_referans(message):
    user_id = message.from_user.id

    if user_id not in user_referals:
        user_referals[user_id] = 0

    referral_link = generate_referral_link(user_id)
    total_referals = user_referals[user_id]

    response_message = f"Referans Linkiniz: {referral_link}\nToplam Referanslarınız: {total_referals}\n1 Ref == 20₺"
    bot.send_message(message.chat.id, response_message)

@bot.message_handler(commands=['start'])
@kanalz
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_type = message.chat.type

    # ID'yi dosyaya kaydetme
    save_id_to_file(chat_id if chat_type != 'private' else user_id)

    text = message.text.split()
    referrer_id = text[1] if len(text) > 1 else None

    if referrer_id:
        referrer_id = referrer_id.strip()
        if referrer_id.isdigit():
            referrer_id = int(referrer_id)

            if user_id == referrer_id:
                bot.reply_to(message, "Kendi referans linkinizle giremezsiniz.")
                return

            if user_id in user_started:
                bot.reply_to(message, "Zaten botu başlattınız.")
                return

            if referrer_id not in user_scores:
                user_scores[referrer_id] = 0

            if referrer_id not in user_referals:
                user_referals[referrer_id] = 0
            user_referals[referrer_id] += 1

            handle_new_user_referral(user_id, referrer_id)
            user_started.add(user_id)

    bot.reply_to(message, "Botu Başlatmak için /welcome yazınız!")

def save_id_to_file(chat_or_user_id):
    file_path = 'users.txt'
    
    # Dosyanın mevcut olup olmadığını kontrol et
    try:
        with open(file_path, 'r') as file:
            existing_ids = file.read().splitlines()
    except FileNotFoundError:
        existing_ids = []

    # ID'nin zaten kaydedilip kaydedilmediğini kontrol et
    if str(chat_or_user_id) not in existing_ids:
        with open(file_path, 'a') as file:
            file.write(f"{chat_or_user_id}\n")

@bot.message_handler(commands=['welcome'])
@kanalz
def start_game(message):
    user_id = message.from_user.id
    if user_id not in user_scores:
        user_scores[user_id] = 150
        bot.reply_to(message, "Hoş geldiniz! Hesabınıza 150 TL eklendi. Komutlar için /help yazınız")
    else:
        bot.reply_to(message, "Zaten /welcome verdiniz Komutlar için /help")

def initialize_score(user_id):
    if user_id not in user_scores:
        user_scores[user_id] = {'zar': 20, 'dart': 20, 'bowling': 20, 'basketbol': 20, 'futbol': 20}

def update_score(user_id, roll_value, game_type):
    if game_type not in user_scores[user_id]:
        user_scores[user_id][game_type] = 20
    if game_type == 'zar':
        user_scores[user_id][game_type] += roll_value
    elif game_type == 'dart':
        if roll_value == 6:
            user_scores[user_id][game_type] += 50
        else:
            user_scores[user_id][game_type] += roll_value * 10
    elif game_type == 'bowling':
        user_scores[user_id][game_type] += roll_value * 10

@bot.message_handler(commands=['zar', 'dart', 'bowling', 'basketbol', 'futbol'])
@kanalz
def play_game(message):
    user_id = message.from_user.id
    game_type = message.text[1:]

    initialize_score(user_id)

    if user_scores[user_id][game_type] < 20:
        bot.send_message(
            message.chat.id,
            f"Uyarı: {game_type.capitalize()} oyununu oynamak için en az 20₺ olmalı."
        )
        return

    if user_scores[user_id][game_type] >= 20:
        user_scores[user_id][game_type] -= 20

    if game_type == 'zar':
        msg = bot.send_dice(message.chat.id, emoji='🎲')
        time.sleep(5)
        roll_value = msg.dice.value
        update_score(user_id, roll_value, 'zar')
        bot.send_message(
            message.chat.id, 
            f"• Zar sonucu: {roll_value}\n\n🎲 • YENİ SKOR: {user_scores[user_id].get('dice', 20)}"
        )
    elif game_type == 'dart':
        msg = bot.send_dice(message.chat.id, emoji='🎯')
        time.sleep(5)
        roll_value = msg.dice.value
        update_score(user_id, roll_value, 'dart')
        bot.send_message(
            message.chat.id, 
            f"• Dart sonucu: {roll_value}\n\n🎯 • YENİ SKOR: {user_scores[user_id].get('dart', 20)}"
        )
    elif game_type == 'bowling':
        msg = bot.send_dice(message.chat.id, emoji='🎳')
        time.sleep(5)
        roll_value = msg.dice.value
        update_score(user_id, roll_value, 'bowling')
        bot.send_message(
            message.chat.id, 
            f"• Bowling sonucu: {roll_value}\n\n🎳 • YENİ SKOR: {user_scores[user_id].get('bowling', 20)}"
        )
    elif game_type == 'basketbol':
        msg = bot.send_dice(message.chat.id, emoji='🏀')
        time.sleep(5)
        score = random.randint(1, 30)
        update_score(user_id, score, 'basketbol')
        bot.send_message(
            message.chat.id, 
            f"• Basketbol skoru: {score}\n\n🏀 • YENİ SKOR: {user_scores[user_id].get('basketball', 20)}"
        )
    elif game_type == 'futbol':
        msg = bot.send_dice(message.chat.id, emoji='⚽')
        time.sleep(5)
        score = random.randint(0, 5)
        update_score(user_id, score, 'futbol')
        bot.send_message(
            message.chat.id, 
            f"• Futbol skoru: {score}\n\n⚽ • YENİ SKOR: {user_scores[user_id].get('football', 20)}"
        )

@bot.message_handler(commands=['risk'])
@kanalz
def play_risk(message):
    user_id = message.from_user.id
    if user_id not in user_scores:
        bot.reply_to(message, "Hesabınız bulunmuyor. Lütfen önce /start komutunu kullanın.")
        return

    try:
        bet = int(message.text.split()[1])
    except IndexError:
        bot.reply_to(message, "Lütfen bir miktar belirtin.")
        return
    except ValueError:
        bot.reply_to(message, "Geçersiz miktar.")
        return

    if bet > user_scores[user_id]:
        bot.reply_to(message, "Bakiyeniz yetersiz.")
        return

    outcome = random.choice(["win", "lose"])
    if outcome == "win":
        win_amount = bet * 2
        user_scores[user_id] += win_amount
        bot.reply_to(message, f"Tebrikler! {win_amount} TL kazandınız.")
    else:
        user_scores[user_id] -= bet
        bot.reply_to(message, f"Üzgünüz! {bet} TL kaybettiniz.")
        
# Kullanıcıdan gelen ilk mesajı takip etmek için bir sözlük
user_request_state = {}

# /iletisim komutu işleyici
@bot.message_handler(commands=['iletisim'])
def handle_iletisim(message):
    # Kullanıcıya talebini göndermesi için bilgilendirme
    bot.send_message(message.chat.id, "İsteğinizi gönderin:\n- Video\n- Fotoğraf\n- Mesaj\n- Ses")
    
    # Kullanıcının isteğinin içeriği ve durumunu takip et
    user_request_state[message.chat.id] = {'status': 'awaiting_content'}

# Kullanıcının gönderdiği içeriği işleme
@bot.message_handler(func=lambda message: message.chat.id in user_request_state and user_request_state[message.chat.id]['status'] == 'awaiting_content')
def handle_user_content(message):
    chat_id = message.chat.id
    
    # Kullanıcıya onay mesajı gönder
    bot.send_message(chat_id, "Sorun Gönderilmiştir! ✅")

    # Kullanıcı bilgilerini adminlere ilet
    user_info = bot.get_chat_member(chat_id, chat_id)
    user_username = user_info.user.username or 'Bilinmiyor'
    user_balance = user_scores.get(chat_id, 0)  # Kullanıcı bakiyesi

    admsg = (f"🆔 - Kullanıcı ID: {chat_id}\n"
             f"🔰 - Kullanıcı Adı: @{user_username}\n"
             f"💰 - Bakiye: {user_balance}₺")

    # İçeriği adminlere ilet
    for admin_id in admin_ids:
        bot.send_message(admin_id, admsg)  # Kullanıcı bilgileri
        # İçeriği adminlere ilet
        if message.content_type == 'text':
            bot.send_message(admin_id, f"Kullanıcının Gönderdiği:\n{message.text}")
        else:
            bot.forward_message(admin_id, chat_id, message.message_id)

    # Kullanıcıdan gelen isteği temizle
    del user_request_state[chat_id]

def game_timer(user_id):
    while True:
        time.sleep(600)
        if user_id in game_start_times and time.time() - game_start_times[user_id] >= 86400:
            if user_id in user_scores:
                user_scores[user_id] += 150
                bot.send_message(user_id, "🎉 24 saat geçti, 150 TL hesabınıza eklendi.")

@bot.message_handler(commands=['bingo'])
@kanalz
def bingo(message):
    user_id = message.from_user.id
    if user_id not in user_scores:
        bot.reply_to(message, "Hesabınız bulunmuyor. Lütfen önce /start komutunu kullanın.")
        return

    if user_scores[user_id] < 20:
        bot.reply_to(message, "Yetersiz bakiye. Bingo oynamak için en az 20 TL gerekir.")
        return

    user_scores[user_id] -= 20
    bingo_numbers = random.sample(range(1, 76), 5)
    win_number = random.choice(bingo_numbers)
    prize = 100 if win_number in bingo_numbers else 0
    if prize > 0:
        user_scores[user_id] += prize
        result_message = f"Bingo! {prize} TL kazandınız."
    else:
        result_message = "Kaybettiniz!"

    bot.reply_to(message, result_message)

@bot.message_handler(commands=['scratchcard'])
@kanalz
def scratch_card(message):
    user_id = message.from_user.id
    if user_id not in user_scores:
        bot.reply_to(message, "Hesabınız bulunmuyor. Lütfen önce /start komutunu kullanın.")
        return

    if user_scores[user_id] < 20:
        bot.reply_to(message, "Yetersiz bakiye. Kazı kazan kartını almak için en az 20 TL gerekir.")
        return

    user_scores[user_id] -= 20
    result = random.choice(["Kazanamadınız", "Kazandınız! 50 TL", "Kazandınız! 150 TL"])
    if "Kazandınız!" in result:
        prize = int(result.split()[1].replace("TL", ""))
        user_scores[user_id] += prize

    bot.reply_to(message, result)

USER_FILE = 'users.txt'

def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, 'r') as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

def save_users(users):
    with open(USER_FILE, 'w') as f:
        for user_id in users:
            f.write(f"{user_id}\n")

def is_admin(user_id):
    return user_id in admin_ids

def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Admin Yönetimi", callback_data="admin_management"),
        types.InlineKeyboardButton("Reedem", callback_data="redeem"),
        types.InlineKeyboardButton("Bakiye", callback_data="balance"),
        types.InlineKeyboardButton("Cevaplama ve Duyuru", callback_data="response_announcement")
    )
    return markup

def create_admin_management_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Admin Ekle", callback_data="admin_add"),
        types.InlineKeyboardButton("Tüm Bakiye Sıfırla", callback_data="reset_balances"),
        types.InlineKeyboardButton("Bakiye Artır", callback_data="increase_balance"),
        types.InlineKeyboardButton("Yardım", callback_data="admin_help")
    )
    markup.add(
        types.InlineKeyboardButton("Geri", callback_data="main_menu")
    )
    return markup

def create_redeem_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Yeni Redeem Kodu Oluştur", callback_data="new_redeem"),
        types.InlineKeyboardButton("Redeem Kodlarını Listele", callback_data="list_redeem"),
        types.InlineKeyboardButton("Kodu Sil", callback_data="del_redeem")
    )
    markup.add(
        types.InlineKeyboardButton("Geri", callback_data="main_menu")
    )
    return markup

def create_balance_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Bakiye Artır", callback_data="increase_balance"),
        types.InlineKeyboardButton("Tüm Bakiye Sıfırla", callback_data="reset_balances")
    )
    markup.add(
        types.InlineKeyboardButton("Geri", callback_data="main_menu")
    )
    return markup

def create_response_announcement_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Duyuru Gönder", callback_data="send_announcement"),
        types.InlineKeyboardButton("Cevap Gönder", callback_data="send_response")
    )
    markup.add(
        types.InlineKeyboardButton("Geri", callback_data="main_menu")
    )
    return markup

@bot.message_handler(commands=['adhelp'])
def show_help(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return

    bot.reply_to(
        message,
        "🏷️ **Yardım Menüleri** 🏷️\n\n"
        "Aşağıdaki butonlara tıklayarak komut kategorilerini görebilirsiniz.",
        reply_markup=create_main_menu_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("main_menu"))
def main_menu_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🏷️ **Ana Menü** 🏷️",
        reply_markup=create_main_menu_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_management"))
def admin_management_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔧 **Admin Yönetimi** 🔧",
        reply_markup=create_admin_management_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("redeem"))
def redeem_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="💰 **Reedem** 💰",
        reply_markup=create_redeem_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("balance"))
def balance_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="💵 **Bakiye** 💵",
        reply_markup=create_balance_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("response_announcement"))
def response_announcement_handler(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📣 **Cevaplama ve Duyuru** 📣",
        reply_markup=create_response_announcement_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_add"))
def handle_admin_add(call):
    bot.send_message(call.message.chat.id, "Lütfen admin eklemek istediğiniz ID'yi girin:")
    bot.register_next_step_handler(call.message, add_admin)

def add_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return
    
    try:
        new_admin_id = int(message.text)
        if new_admin_id not in admin_ids:
            admin_ids.append(new_admin_id)
            bot.reply_to(message, f"Yeni admin eklendi: {new_admin_id}")
        else:
            bot.reply_to(message, "Bu kullanıcı zaten admin.")
    except ValueError:
        bot.reply_to(message, "Geçersiz ID.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reset_balances"))
def handle_reset_balances(call):
    if not is_admin(call.from_user.id):
        bot.send_message(call.message.chat.id, "Bu komutu kullanma yetkiniz yok.")
        return

    user_scores.clear()
    bot.send_message(call.message.chat.id, "Tüm kullanıcı bakiyeleri sıfırlandı.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("increase_balance"))
def handle_increase_balance(call):
    bot.send_message(call.message.chat.id, "Lütfen kullanıcı ID'sini ve miktarı girin (örnek: ID miktar):")
    bot.register_next_step_handler(call.message, increase_balance)

def increase_balance(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return
    
    try:
        user_id, amount = map(int, message.text.split())
        if user_id in user_scores:
            user_scores[user_id] += amount
            bot.reply_to(message, f"{user_id} kullanıcısına {amount} TL eklendi.")
        else:
            bot.reply_to(message, "Kullanıcı bulunamadı.")
    except ValueError:
        bot.reply_to(message, "Geçersiz ID veya miktar.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_help"))
def handle_admin_help(call):
    if not is_admin(call.from_user.id):
        bot.send_message(call.message.chat.id, "Bu komutu kullanma yetkiniz yok.")
        return
    
    help_message = (
        "🔧 **Admin Komutları** 🔧\n\n"
        "/admin <ID> - Admin ekler.\n"
        "/sifirlama - Tüm kullanıcıların bakiyelerini sıfırlar.\n"
        "/tlarttir <ID> <miktar> - Belirtilen ID'ye bakiye ekler.\n"
        "/iletisim - Kullanıcının iletişime geçmesini sağlar.\n"
        "/cevap <ID> <mesaj> - Belirtilen kullanıcıya cevap verir.\n"
    )
    bot.send_message(call.message.chat.id, help_message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("new_redeem"))
def handle_new_redeem(call):
    bot.send_message(call.message.chat.id, "Lütfen yeni redeem kodu ve değerini girin (örnek: KOD DEĞER):")
    bot.register_next_step_handler(call.message, new_redeem)

def new_redeem(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return
    
    try:
        code, value = message.text.split()
        value = int(value)
        if code in reedem_codes:
            bot.reply_to(message, f"Bu kod zaten var: {code}")
            return

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Evet ✅", callback_data=f"limit_yes {code} {value}"),
            types.InlineKeyboardButton("Hayır ❌", callback_data=f"limit_no {code} {value}")
        )
        bot.reply_to(message, "Kullanıcı sınırı olsun mu?", reply_markup=markup)
    except ValueError:
        bot.reply_to(message, "Lütfen doğru formatta komut girin: /new_redeem <KOD> <DEĞER>")

@bot.callback_query_handler(func=lambda call: call.data.startswith("limit_"))
def handle_limit(call):
    action, code, value = call.data.split()
    value = int(value)

    if action == "limit_yes":
        msg = bot.send_message(call.message.chat.id, "Lütfen max kaç kullanıcı kullanabilir giriniz:")
        bot.register_next_step_handler(msg, set_limit, code, value)
    elif action == "limit_no":
        reedem_codes[code] = {'value': value, 'max': 0, 'used': 0}
        bot.send_message(call.message.chat.id, f"Reedem kodu: `{code}` Değeri: `{value}`₺")

def set_limit(message, code, value):
    try:
        max_users = int(message.text)
        reedem_codes[code] = {'value': value, 'max': max_users, 'used': 0}
        bot.reply_to(message, f"Reedem kodu: `{code}` Değeri: `{value}`₺ Max Kullanım: `{max_users}`")
    except ValueError:
        bot.reply_to(message, "Lütfen geçerli bir sayı girin.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("list_redeem"))
def handle_list_redeem(call):
    if not is_admin(call.from_user.id):
        bot.send_message(call.message.chat.id, "Bu komutu kullanma yetkiniz yok.")
        return

    if not reedem_codes:
        bot.send_message(call.message.chat.id, "Henüz eklenmiş bir redeem kodu yok.")
        return
    
    response = "Reedem Kodlarının Listesi:\n"
    for code, info in reedem_codes.items():
        max_usage = info['max'] if info['max'] != 0 else "Limitsiz"
        response += f"Ad: `{code}` Değer: `{info['value']}`₺ Max: `{max_usage}`\n"
    
    bot.send_message(call.message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_redeem"))
def handle_del_redeem(call):
    bot.send_message(call.message.chat.id, "Lütfen silmek istediğiniz redeem kodunu girin:")
    bot.register_next_step_handler(call.message, del_redeem)

def del_redeem(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return

    try:
        code = message.text.strip()
        if code in reedem_codes:
            del reedem_codes[code]
            bot.reply_to(message, f"`{code}` kodu kaldırılmıştır!")
        else:
            bot.reply_to(message, "Böyle bir kod bulunamadı.")
    except ValueError:
        bot.reply_to(message, "Lütfen geçerli bir kod girin.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_announcement"))
def handle_send_announcement(call):
    bot.send_message(call.message.chat.id, "Duyuruyu yazın:")
    bot.register_next_step_handler(call.message, send_announcement)

def send_announcement(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return
    
    announcement = message.text
    users = load_users()
    success_count = 0
    failed_count = 0

    for user_id in users:
        try:
            bot.send_message(user_id, announcement)
            success_count += 1
        except telebot.apihelper.ApiException:
            failed_count += 1
            users.remove(user_id)

    save_users(users)

    total_users = len(users)
    total_groups = len([user_id for user_id in users if user_id < 0])  # Negatif ID'ler grupları temsil eder

    response = (
        f"Duyuru iletildi\n"
        f"Toplam Kullanıcı: {total_users}\n"
        f"Toplam Grup: {total_groups}\n"
        f"Toplam Hatalı Gönderim: {failed_count}\n"
        f"Toplam Başarılı Gönderim: {success_count}\n"
    )
    bot.reply_to(message, response)

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_response"))
def handle_send_response(call):
    bot.send_message(call.message.chat.id, "Lütfen cevap vermek istediğiniz kullanıcı ID'sini ve mesajı girin (örnek: ID mesaj):")
    bot.register_next_step_handler(call.message, send_response)

def send_response(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Bu komutu kullanma yetkiniz yok.")
        return

    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "Lütfen bir kullanıcı ID'si ve mesaj girin.")
            return
        
        target_id = int(parts[0])
        response = parts[1]

        if target_id in user_scores:
            bot.send_message(target_id, f"📬 Admin cevabı: {response}")
            bot.reply_to(message, f"Mesaj gönderildi: {response}")
        else:
            bot.reply_to(message, "Kullanıcı bulunamadı.")
    except ValueError:
        bot.reply_to(message, "Geçersiz ID. Lütfen sayısal bir ID girin.")
    except Exception as e:
        bot.reply_to(message, f"Bir hata oluştu: {str(e)}")

@bot.message_handler(commands=['help'])
@kanalz
def help_message(message):
    help_text = (
        "🎉 **Yardım Menüsü** 🎉\n\n"
        "/start - Oyunu başlatır ve 150 TL bakiye ekler.\n"
        "/risk <miktar> - Belirtilen miktarda bahis oynar.\n"
        "/bingo - Bingo oyunu oynar.\n"
        "/scratchcard - Kazı kazan kartı alır.\n"
        "/skip - Bir kelimeyi atlar.\n"
        "/iletisim - Admin ile iletişim kurar.\n"
        "/help - Bu yardım menüsünü gösterir.\n"
        "/futbol - Futbol Oynar.\n"
        "/zar - Zar atar. \n"
        "/bowling - Bowling Oynar.\n"
        "/basketbol - Basket atar.\n"
        "/dart - Dart atar.\n"
        "/market - Marketi Açar\n"
        "/referans - Referans Linkini Gösterir\n"
        "/bakiye - Bakiyenizi Gösterir\n"
        "/reedem - Reedem Kodları girmenizi sağlar\n"
        "/kelime - Kelime Tahmin etme oyunu başlatır\n"
        "/skip - kelimeyi atlar\n"
        "/kelimebitir - Kelime oyununu bitirir ve skorları gösterir\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: message.text and message.text.startswith("/"))
def handle_command(message):
    pass

if __name__ == '__main__':
    threading.Thread(target=bot.polling, args=(True,)).start()
    threading.Thread(target=game_timer, args=(1234567890,)).start()