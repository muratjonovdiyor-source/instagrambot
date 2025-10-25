import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import requests
import json

# Telegram bot tokeningizni kiriting
BOT_TOKEN = "8417451062:AAG_oBc3u5Aux9S9nyeFKwXx2viGXkudj3w"

# Instagram login
INSTAGRAM_USERNAME = "x571.dx"
INSTAGRAM_PASSWORD = "Diyorbek2008"

def is_instagram_url(url):
    """Instagram URL ekanligini tekshirish"""
    pattern = r'(https?://)?(www\.)?(instagram\.com|instagr\.am)/(p|reel|tv)/([A-Za-z0-9_-]+)'
    return re.match(pattern, url)

def is_youtube_url(url):
    """YouTube URL ekanligini tekshirish"""
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*'
    return re.match(pattern, url)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Men siz uchun video va qo'shiq yuklab beraman!\n\n"
        "📹 Qo'llab-quvvatlanadigan platformalar:\n"
        "• Instagram (post, reels, video)\n"
        "• YouTube (video, audio)\n\n"
        "🎵 Qo'shiq qidirish:\n"
        "Qo'shiq nomini yozing, men topib beraman!\n"
        "Masalan: \"Xamdam Sobirov - Janze\"\n\n"
        "🎼 Qo'shiq tanish (Shazam):\n"
        "Video yoki audio yuborib, qaysi qo'shiq ekanligini bilib oling!\n"
        "Ijrochi, nomi va variantlari ko'rsatiladi!\n\n"
        "Foydalanish:\n"
        "1️⃣ Link yuboring yoki qo'shiq nomini yozing\n"
        "2️⃣ Video/audio yuborib qo'shiqni taniting\n"
        "3️⃣ Biroz kuting!\n"
        "4️⃣ Video/qo'shiq tayyor! 🎉\n\n"
        "Admin- @diyorbek_muratjonov"
    )

async def recognize_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video yoki audio dan qo'shiqni tanish (AudD API)"""
    status_msg = await update.message.reply_text("🎵 Qo'shiq tanilmoqda, iltimos kuting...")
    
    try:
        # Video yoki audio faylni olish
        if update.message.video:
            file = await update.message.video.get_file()
            file_name = f"temp_video_{update.message.video.file_id}.mp4"
        elif update.message.audio:
            file = await update.message.audio.get_file()
            file_name = f"temp_audio_{update.message.audio.file_id}.mp3"
        elif update.message.voice:
            file = await update.message.voice.get_file()
            file_name = f"temp_voice_{update.message.voice.file_id}.ogg"
        else:
            await status_msg.edit_text("❌ Iltimos, video yoki audio yuboring!")
            return
        
        # Faylni yuklab olish
        await file.download_to_drive(file_name)
        
        await status_msg.edit_text("🔍 Qo'shiq qidirilmoqda...")
        
        # AudD API bilan tanish (bepul, API key kerak emas)
        api_url = "https://api.audd.io/"
        
        with open(file_name, 'rb') as audio_file:
            files = {'file': audio_file}
            response = requests.post(api_url, files=files, timeout=30)
        
        # Faylni o'chirish
        if os.path.exists(file_name):
            os.remove(file_name)
        
        if response.status_code != 200:
            await status_msg.edit_text("❌ Qo'shiq tanib bo'lmadi. Iltimos, qaytadan urinib ko'ring.")
            return
        
        result = response.json()
        
        # Natijani tekshirish
        if result.get('status') != 'success' or not result.get('result'):
            await status_msg.edit_text(
                "❌ Qo'shiq tanilmadi.\n\n"
                "Sabablari:\n"
                "• Qo'shiq shovqinli bo'lishi mumkin\n"
                "• Qo'shiq juda qisqa\n"
                "• Qo'shiq bazada yo'q\n\n"
                "Boshqa qo'shiq bilan sinab ko'ring!"
            )
            return
        
        track = result['result']
        
        # Qo'shiq ma'lumotlari
        title = track.get('title', 'Noma\'lum')
        artist = track.get('artist', 'Noma\'lum')
        album = track.get('album', '')
        release_date = track.get('release_date', '')
        label = track.get('label', '')
        
        # Linklar
        spotify_link = track.get('spotify', {}).get('external_urls', {}).get('spotify', '')
        apple_music_link = track.get('apple_music', {}).get('url', '')
        
        # Rasm - qo'shiq va ijrochi rasmini olish
        cover_url = None
        artist_image = None
        
        # Spotify dan rasm olish
        if 'spotify' in track:
            # Album rasmi
            if 'album' in track['spotify'] and 'images' in track['spotify']['album']:
                images = track['spotify']['album']['images']
                if images:
                    cover_url = images[0].get('url')
            
            # Ijrochi rasmini olish (Spotify artist ID orqali)
            if 'artists' in track['spotify'] and track['spotify']['artists']:
                artist_id = track['spotify']['artists'][0].get('id')
                if artist_id:
                    # Spotify Web API orqali ijrochi rasmini olish
                    try:
                        artist_api_url = f"https://api.spotify.com/v1/artists/{artist_id}"
                        # Bu endpoint token talab qiladi, shuning uchun boshqa usul
                    except:
                        pass
        
        # Agar Spotify dan rasm olmasa, yt-dlp orqali YouTube dan qidiramiz
        if not cover_url:
            try:
                search_query = f"{artist} {title}"
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'default_search': 'ytsearch1',
                    'extract_flat': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_result = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                    if 'entries' in search_result and search_result['entries']:
                        video = search_result['entries'][0]
                        # Thumbnail dan eng yuqori sifatli rasmni olish
                        if 'thumbnails' in video and video['thumbnails']:
                            cover_url = video['thumbnails'][-1].get('url')
            except:
                pass
        
        # Xabar tayyorlash
        message = f"✅ Qo'shiq topildi!\n\n"
        message += f"🎵 Nomi: {title}\n"
        message += f"👤 Ijrochi: {artist}\n"
        
        if album:
            message += f"💿 Album: {album}\n"
        if release_date:
            message += f"📅 Chiqgan sana: {release_date}\n"
        if label:
            message += f"🏷️ Label: {label}\n"
        
        message += "\n🔗 Linklar:\n"
        
        # YouTube qidirish linki
        youtube_search = f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+{artist.replace(' ', '+')}"
        message += f"▶️ YouTube: {youtube_search}\n"
        
        if spotify_link:
            message += f"🎧 Spotify: {spotify_link}\n"
        if apple_music_link:
            message += f"🍎 Apple Music: {apple_music_link}\n"
        
        message += f"\n\nAdmin- @diyorbek_muratjonov"
        
        # Agar rasm bo'lsa, rasm bilan yuborish
        if cover_url:
            try:
                await status_msg.delete()
                await update.message.reply_photo(
                    photo=cover_url,
                    caption=message
                )
            except:
                # Agar rasm yuklanmasa, oddiy xabar yuborish
                await status_msg.edit_text(message)
        else:
            await status_msg.edit_text(message)
        
        # Qo'shiqni yuklab berish taklifi
        await update.message.reply_text(
            f"💡 Qo'shiqni yuklab olishni xohlaysizmi?\n\n"
            f"Yozib yuboring: {title} {artist}"
        )
        
    except requests.exceptions.Timeout:
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)
        await status_msg.edit_text("❌ Vaqt tugadi. Iltimos, qaytadan urinib ko'ring.")
    except Exception as e:
        # Faylni o'chirish (xatolik bo'lsa ham)
        if 'file_name' in locals() and os.path.exists(file_name):
            os.remove(file_name)
        
        await status_msg.edit_text(
            f"❌ Xatolik yuz berdi: {str(e)[:150]}\n\n"
            "Iltimos, qaytadan urinib ko'ring."
        )

async def search_and_download_music(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """YouTube dan qo'shiq qidirish va yuklab olish"""
    status_msg = await update.message.reply_text(f"🔍 '{query}' qidirilmoqda...")
    
    try:
        # YouTube dan qidirish
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',  # Birinchi natijani olish
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_msg.edit_text("🎵 Qo'shiq topildi!")
            
            # Avval ma'lumot olish (rasm uchun)
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch1',
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl_info:
                search_result = ydl_info.extract_info(f"ytsearch1:{query}", download=False)
                
                if 'entries' in search_result:
                    video_info = search_result['entries'][0]
                else:
                    video_info = search_result
                
                # Thumbnail (rasm) olish
                thumbnail_url = None
                if 'thumbnails' in video_info and video_info['thumbnails']:
                    # Eng yuqori sifatli rasmni olish
                    thumbnail_url = video_info['thumbnails'][-1].get('url')
                elif 'thumbnail' in video_info:
                    thumbnail_url = video_info['thumbnail']
                
                title = video_info.get('title', "Qo'shiq")
                artist = video_info.get('artist') or video_info.get('uploader', 'Noma\'lum')
                duration = video_info.get('duration', 0)
                view_count = video_info.get('view_count', 0)
                
                # Agar rasm topilsa, avval rasmni ko'rsatish
                if thumbnail_url:
                    await status_msg.delete()
                    
                    duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
                    views_str = f"{view_count:,}" if view_count else "N/A"
                    
                    caption = (
                        f"🎵 {title}\n"
                        f"👤 {artist}\n"
                        f"⏱ {duration_str}\n"
                        f"👁 {views_str} ko'rishlar\n\n"
                        f"📥 Yuklanmoqda..."
                    )
                    
                    photo_msg = await update.message.reply_photo(
                        photo=thumbnail_url,
                        caption=caption
                    )
                else:
                    await status_msg.edit_text("📥 Yuklanmoqda...")
            
            # Endi qo'shiqni yuklab olish
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            
            if 'entries' in info:
                info = info['entries'][0]
            
            # Fayl nomini topish
            audio_file = None
            for ext in ['webm', 'm4a', 'opus', 'mp3', 'mp4']:
                test_file = f"{info['id']}.{ext}"
                if os.path.exists(test_file):
                    audio_file = test_file
                    break
            
            if not audio_file:
                if thumbnail_url:
                    await photo_msg.edit_caption("❌ Audio fayl topilmadi.")
                else:
                    await status_msg.edit_text("❌ Audio fayl topilmadi.")
                return
            
            file_size = os.path.getsize(audio_file)
            
            # Telegram 50MB limit
            if file_size > 50 * 1024 * 1024:
                os.remove(audio_file)
                if thumbnail_url:
                    await photo_msg.edit_caption("❌ Fayl juda katta (50MB dan oshiq).")
                else:
                    await status_msg.edit_text("❌ Fayl juda katta (50MB dan oshiq).")
                return
            
            if thumbnail_url:
                await photo_msg.edit_caption(
                    f"🎵 {title}\n"
                    f"👤 {artist}\n"
                    f"⏱ {duration_str}\n"
                    f"👁 {views_str} ko'rishlar\n\n"
                    f"📤 Yuborilmoqda..."
                )
            else:
                await status_msg.edit_text("📤 Qo'shiq yuborilmoqda...")
            
            # Audio yuborish
            with open(audio_file, 'rb') as audio:
                duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
                caption = f"🎵 {title}\n👤 {artist}\n⏱ {duration_str}\n\nAdmin- @diyorbek_muratjonov"
                
                await update.message.reply_audio(
                    audio=audio,
                    caption=caption,
                    title=title,
                    performer=artist
                )
            
            os.remove(audio_file)
            
            # Rasmni SAQLAB qolish, faqat captionni yangilash
            if thumbnail_url:
                try:
                    await photo_msg.edit_caption(
                        f"✅ Tayyor!\n\n"
                        f"🎵 {title}\n"
                        f"👤 {artist}\n"
                        f"⏱ {duration_str}\n"
                        f"👁 {views_str} ko'rishlar\n\n"
                        f"Admin- @diyorbek_muratjonov"
                    )
                except:
                    pass
            else:
                await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)[:150]}")

async def download_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal yuklab olish funksiyasi"""
    text = update.message.text.strip()
    
    # URL tekshirish
    if is_instagram_url(text):
        await download_instagram(update, context, text)
    elif is_youtube_url(text):
        await download_youtube(update, context, text)
    else:
        # Agar URL bo'lmasa, qo'shiq qidirish
        await search_and_download_music(update, context, text)

async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Instagram videoni yuklab olish"""
    status_msg = await update.message.reply_text("⏳ Instagram video yuklanmoqda...")
    
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
        elif INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            ydl_opts['username'] = INSTAGRAM_USERNAME
            ydl_opts['password'] = INSTAGRAM_PASSWORD
        
        await status_msg.edit_text("🔍 Video qidirilmoqda...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info.get('_type') == 'playlist':
                await status_msg.edit_text("❌ Playlist yuklab bo'lmaydi.")
                return
            
            await status_msg.edit_text("📥 Video yuklab olinmoqda...")
            ydl.download([url])
            
            video_file = f"{info['id']}.{info['ext']}"
            
            if not os.path.exists(video_file):
                possible_files = [f for f in os.listdir('.') if f.startswith(info['id'])]
                if possible_files:
                    video_file = possible_files[0]
                else:
                    await status_msg.edit_text("❌ Video yuklab olinmadi.")
                    return
            
            file_size = os.path.getsize(video_file)
            
            if file_size > 50 * 1024 * 1024:
                os.remove(video_file)
                await status_msg.edit_text("❌ Video juda katta (50MB+).")
                return
            
            await status_msg.edit_text("📤 Video yuborilmoqda...")
            
            with open(video_file, 'rb') as video:
                uploader = info.get('uploader', 'Instagram')
                caption = f"📹 {uploader}\n\n\nMarhamat video tayor!\nBizni tanlaganingiz uchun raxmat🙂‍↔️\n\nSavollar uchun Admin-@diyorbek_muratjonov"
                await update.message.reply_video(
                    video=video,
                    caption=caption,
                    supports_streaming=True
                )
            
            os.remove(video_file)
            await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)[:150]}")

async def download_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """YouTube video/audio yuklab olish"""
    status_msg = await update.message.reply_text(
        "YouTube video topildi!\n\n"
        "Nima yuklaymiz?\n"
        "Video uchun: /video\n"
        "Audio uchun: /audio"
    )
    
    # URL ni context ga saqlash
    context.user_data['youtube_url'] = url
    
async def download_youtube_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """YouTube videoni yuklab olish"""
    url = context.user_data.get('youtube_url')
    
    if not url:
        await update.message.reply_text("❌ Avval YouTube link yuboring!")
        return
    
    status_msg = await update.message.reply_text("⏳ YouTube video yuklanmoqda...")
    
    try:
        ydl_opts = {
            'format': 'best[height<=720]',  # 720p gacha
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        await status_msg.edit_text("📥 Video yuklab olinmoqda...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            video_file = f"{info['id']}.{info['ext']}"
            
            if not os.path.exists(video_file):
                possible_files = [f for f in os.listdir('.') if f.startswith(info['id'])]
                if possible_files:
                    video_file = possible_files[0]
                else:
                    await status_msg.edit_text("❌ Video yuklab olinmadi.")
                    return
            
            file_size = os.path.getsize(video_file)
            
            if file_size > 50 * 1024 * 1024:
                os.remove(video_file)
                await status_msg.edit_text("❌ Video juda katta (50MB+). Qisqaroq video tanlang.")
                return
            
            await status_msg.edit_text("📤 Video yuborilmoqda...")
            
            with open(video_file, 'rb') as video:
                title = info.get('title', 'YouTube Video')
                caption = f"📹 {title[:100]}\n\nAdmin- @diyorbek_muratjonov"
                
                await update.message.reply_video(
                    video=video,
                    caption=caption,
                    supports_streaming=True
                )
            
            os.remove(video_file)
            await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)[:150]}")

async def download_youtube_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """YouTube audio yuklab olish"""
    url = context.user_data.get('youtube_url')
    
    if not url:
        await update.message.reply_text("❌ Avval YouTube link yuboring!")
        return
    
    status_msg = await update.message.reply_text("⏳ YouTube audio yuklanmoqda...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        await status_msg.edit_text("📥 Audio yuklab olinmoqda...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            audio_file = None
            for ext in ['webm', 'm4a', 'opus', 'mp3', 'mp4']:
                test_file = f"{info['id']}.{ext}"
                if os.path.exists(test_file):
                    audio_file = test_file
                    break
            
            if not audio_file:
                await status_msg.edit_text("❌ Audio fayl topilmadi.")
                return
            
            file_size = os.path.getsize(audio_file)
            
            if file_size > 50 * 1024 * 1024:
                os.remove(audio_file)
                await status_msg.edit_text("❌ Audio juda katta (50MB+).")
                return
            
            await status_msg.edit_text("📤 Audio yuborilmoqda...")
            
            with open(audio_file, 'rb') as audio:
                title = info.get('title', 'YouTube Audio')
                uploader = info.get('uploader', 'YouTube')
                
                await update.message.reply_audio(
                    audio=audio,
                    caption=f"🎵 {title[:100]}\n\nAdmin- @diyorbek_muratjonov",
                    title=title,
                    performer=uploader
                )
            
            os.remove(audio_file)
            await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {str(e)[:150]}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam komandasi"""
    await update.message.reply_text(
        "📖 Qo'llanma:\n\n"
        "🎬 VIDEO YUKLAB OLISH:\n"
        "• Instagram linkini yuboring\n"
        "• YouTube linkini yuboring\n\n"
        "🎵 QO'SHIQ QIDIRISH:\n"
        "• Qo'shiq nomini yozing\n"
        "Masalan: \"Dadaboyev Onamga\"\n"
        "Masalan: \"Eminem Lose Yourself\"\n\n"
        "🎼 QO'SHIQ TANISH (Shazam):\n"
        "• Video yoki audio yuboring\n"
        "• Bot qaysi qo'shiq ekanligini topadi\n"
        "• Ijrochi, nomi, variantlar ko'rsatiladi\n\n"
        "⚙️ KOMANDALAR:\n"
        "/start - Botni boshlash\n"
        "/video - YouTube video yuklash\n"
        "/audio - YouTube audio yuklash\n"
        "/help - Yordam\n\n"
        "⚠️ Eslatma:\n"
        "- Maksimal hajm: 50MB\n"
        "- Private postlar yuklanmaydi\n\n"
        "Admin- @diyorbek_muratjonov"
    )

def main():
    """Botni ishga tushirish"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("video", download_youtube_video))
    application.add_handler(CommandHandler("audio", download_youtube_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_content))
    
    # Video va audio yuborilganda qo'shiq tanish
    application.add_handler(MessageHandler(filters.VIDEO | filters.AUDIO | filters.VOICE, recognize_song))
    
    print("🚀 Bot ishga tushdi...")
    print("📱 Instagram, YouTube, qo'shiq qidirish va tanish (AudD API)!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()