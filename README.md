# 🎵 Universal Music & Media Downloader Telegram Bot (Aiogram 3 + SQLite)

Ushbu bot **Python (Aiogram 3.x)**, **aiosqlite (SQLite)** va **yt-dlp** texnologiyalari asosida professional arxitekturada yozilgan bo'lib, musiqa qidirish, Instagram/TikTok/YouTube'dan video va MP3 yuklab olish, majburiy obuna, Telegram Premium savdosi (chek qabul qilish), kurslar va to'liq dinamik Admin panelni o'z ichiga oladi.

---

## 🌟 Asosiy Imkoniyatlar (18+ Funksiyalar)

### 👤 Foydalanuvchi Funksiyalari:
1. **🎵 Musiqa Qidirish (Nom yoki Ijrochi bo'yicha):** Istalgan qo'shiq nomini yozganda 10 ta variant (1..10 tugmalar bilan) chiqaradi va tanlanganini MP3 formatda yuboradi.
2. **📥 Instagram / TikTok / YouTube Video Yuklash:** Havola (link) yuborilganda suv belgisiz (watermark-free) sifatli videoni yuklab beradi.
3. **🎧 Videodan MP3 Ajratib Olish:** Yuklangan har bir video ostida **«🎵 MP3 (Musiqasini) tortish»** tugmasi bor — bir bosishda videoning musiqasini MP3 qilib beradi.
4. **📢 Majburiy Obuna Tizimi (Force Subscribe):** Admin qo'shgan kanallarga obuna bo'lmaguncha botdan foydalanishni cheklaydi va **«✅ Obuna bo'ldim (Tekshirish)»** tugmasi orqali real vaqtda tekshiradi.
5. **💎 Telegram Premium & Stars Xarid Qilish + To'lov Cheki:** Foydalanuvchi tarifni tanlaydi, `@username` kiritadi, karta raqamga to'lov qilib chek (skrinshot) yuboradi. Chek darhol adminga **«✅ Tasdiqlash / ❌ Rad etish / 💬 Javob yozish»** tugmalari bilan boradi.
6. **✍️ Adminga Bog'lanish (Ikki Tomonlama Support):** Foydalanuvchi bot ichidan matn, rasm, ovozli xabar yoki video yuborib adminga murojaat qiladi va admin o'sha xabarning o'zidan foydalanuvchiga javob qaytara oladi.
7. **❤️ Sevimlilar (Shaxsiy Play-list):** Yoqqan musiqalarni bir tugma bilan saqlab qo'yish va istalgan payt qayta tinglash yoki o'chirish.
8. **🔥 Top Xitlar (Real-Vaqt Charti):** Botda eng ko'p qidirilgan xit qo'shiqlar reytingi va ularni bir bosishda yuklash.
9. **🎲 Tasodifiy Qo'shiq (Random Hit):** Kayfiyat uchun tasodifiy mashhur xit taronani topib berish.
10. **📝 Qo'shiq Matni (Lyrics Finder):** Qo'shiq nomini yozib uning to'liq matnini (so'zlarini) topish.
11. **🎓 Kurslarimiz + Kursga Yozilish:** O'quv kurslari katalogi, narxlari va telefon raqam yuborib ro'yxatdan o'tish (ariza darhol adminga boradi).
12. **📍 Lokatsiyamiz (Xarita + Manzil):** GPS xarita nuqtasi va manzil tavsifi.
13. **📞 Bizning Raqamlar:** Telefon raqamlar va ijtimoiy tarmoq havolalari.
14. **👥 Referal va Bonus Tizimi:** Shaxsiy taklif havolasi orqali do'stlarni chaqirib balans yig'ish.
15. **👤 Shaxsiy Kabinet (Profil):** ID, yuklashlar soni, qidiruvlar, referallar va bonus balans statistikasi.
16. **❓ Ko'p Beriladigan Savollar (FAQ):** Interaktiv savol-javoblar bo'limi.
17. **🆘 Yordam (Help) & Bot Haqida:** To'liq qo'llanma va ma'lumot.
18. **🎙 Audio / Voice Qidiruv:** Yuborilgan audio fayl metama'lumoti orqali musiqani topish.

---

### 🛠 Dinamik Admin Panel (`/admin` yoki `🛠 Admin Panel` tugmasi):
1. **📊 Real-Vaqt Statistikasi:** Jami va bugungi foydalanuvchilar, yuklashlar, qidiruvlar, kutilayotgan to'lovlar.
2. **📢 Majburiy Obuna Kanallari Boshqaruvi:** Kodga tegmasdan kanal qo'shish, o'chirish va majburiy obunani Yoqish/O'chirish.
3. **⚙️ Dinamik Matnlar va GPS Lokatsiya:** Salomlashish matni, Help, Raqamlar, Lokatsiya manzili, GPS koordinatalar, Karta rekvizitlari va Referal bonus miqdorini bot ichidan o'zgartirish.
4. **💎 Premium Tariflarni Boshqarish:** Yangi tarif qo'shish, narxlarni o'zgartirish va o'chirish.
5. **🎓 Kurslarni Boshqarish:** Yangi o'quv kursi qo'shish yoki eskisini o'chirish.
6. **🎛 Dinamik Menyu Konstruktori:** Dasturchisiz asosiy menyuga yangi tugmalar (masalan: *🎁 Aksiyalar*, *📢 Yangiliklar*) qo'shish va javobini sozlash!
7. **❓ FAQ Boshqaruvi:** Savol-javoblarni qo'shish va o'chirish.
8. **📨 Ommaviy Xabar Tarqatish (Rassilka):** Barcha foydalanuvchilarga rasm, video, audio yoki tugmali post yuborish.
9. **👤 Foydalanuvchi Qidirish / Ban / Unban:** ID orqali foydalanuvchini topish, bloklash yoki shaxsiy xabar yozish.
10. **👮‍♂️ Adminlar Boshqaruvi:** Bot ichidan yangi admin tayinlash yoki adminlikdan olish.
11. **📥 Bazani CSV (Excel) Formatda Yuklab Olish:** Barcha foydalanuvchilar ro'yxatini bir tugma bilan eksport qilish.

---

## 🚀 Ishga Tushirish Qo'llanmasi

1. Kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

2. `.env` fayliga `BOT_TOKEN` va `ADMIN_IDS` ni yozing:
```env
BOT_TOKEN=1234567890:AAHxyz...
ADMIN_IDS=123456789
```

3. Botni ishga tushiring:
```bash
python bot.py
```
