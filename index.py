from nextcord.ext import commands
import nextcord
from gtts import gTTS
import asyncio
import time
from collections import defaultdict

intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="T ", intents=intents)
bot.remove_command("help")

# Ini akan menyimpan waktu pengiriman pesan dari setiap user
user_message_times = defaultdict(list)

# Daftar user yang akan menerima laporan
target_users = ["exclau", "aizenc", "ryuuuhokaaa"]  # Tambahkan username lainnya di sini

@bot.event
async def on_message(message):
    # Abaikan pesan dari bot sendiri
    if message.author == bot.user:
        return

    # Log waktu pesan terakhir dari user
    user_message_times[message.author.id].append(time.time())

    # Hitung pesan yang dikirim dalam 5 detik terakhir
    recent_messages = [
        t for t in user_message_times[message.author.id]
        if time.time() - t < 5
    ]

    # Update daftar dengan hanya pesan terbaru
    user_message_times[message.author.id] = recent_messages

    # Jika ada lebih dari 10 pesan dalam 5 detik terakhir, anggap sebagai spam
    if len(recent_messages) > 10:
        await message.channel.send("SABAR JANGAN SPAMM!")

        # Cek apakah user berada di voice channel
        if message.author.voice:
            channel = message.author.voice.channel
            vc = message.guild.voice_client

            if not vc or not vc.is_connected():
                vc = await channel.connect()

            # Generate and play TTS "SABAR"
            sound = gTTS(text="SABAR", lang='id', slow=False)
            sound.save("sabar.mp3")

            if vc.is_playing():
                vc.stop()

            source = await nextcord.FFmpegOpusAudio.from_probe("sabar.mp3", method="fallback")
            vc.play(source)
        else:
            await message.channel.send("Anda harus berada di voice channel agar bot dapat berbicara.")

    # Tambahan untuk mengirim DM ke beberapa user dan menghapus pesan 'T Report'
    if message.content.startswith('T Report'):
        saran_pesan = message.content[len('T Report'):].strip()

        # Loop melalui setiap user dalam daftar target_users
        for username in target_users:
            target_user = nextcord.utils.get(message.guild.members, name=username)
            if target_user:
                try:
                    # Kirim teks report
                    await target_user.send(f"Saran dari {message.author}: {saran_pesan}")

                    # Kirim setiap file yang dilampirkan
                    for attachment in message.attachments:
                        file = await attachment.to_file()
                        await target_user.send(file=file)

                except nextcord.Forbidden:
                    await message.channel.send(f"Tidak bisa mengirim DM ke {username}.")
            else:
                await message.channel.send(f"User {username} tidak ditemukan.")
        
        # Hapus pesan report setelah diproses
        await message.delete()

    # Memastikan command lain tetap bisa digunakan
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        em = nextcord.Embed(title=f"Slow it down bro!",
                            description=f"Try again in {error.retry_after:.2f}s.", color=nextcord.Color.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the permissions to do that!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found.")
    else:
        print(type(error))
        print(error)

from asyncio import Lock, Queue

# Queue untuk antrian TTS
tts_queue = Queue()
tts_lock = Lock()

@bot.command(name='tts')
async def tts(ctx, *args):
    # Ambil teks yang ingin diucapkan
    text = " ".join(args)
    
    # Gabungkan nama pengguna dengan teks yang akan diucapkan
    tts_text = f"{ctx.author.display_name} berkata: {text}"
    
    # Tambahkan TTS ke dalam antrian
    await tts_queue.put((ctx, tts_text))
    
    # Proses antrian TTS
    await process_tts_queue()

async def process_tts_queue():
    async with tts_lock:
        while not tts_queue.empty():
            ctx, tts_text = await tts_queue.get()

            # Cek apakah pengguna berada di voice channel
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                vc = ctx.voice_client
                
                if not vc or not vc.is_connected():
                    vc = await channel.connect()
                
                # Generate TTS dengan teks yang telah digabungkan
                sound = gTTS(text=tts_text, lang='id', slow=False)
                sound.save("tts-audio.mp3")
                
                if vc.is_playing():
                    vc.stop()

                source = await nextcord.FFmpegOpusAudio.from_probe("tts-audio.mp3", method="fallback")
                vc.play(source)
                
                # Tunggu sampai TTS selesai diputar sebelum melanjutkan ke antrian berikutnya
                while vc.is_playing():
                    await asyncio.sleep(0.5)
            else:
                await ctx.send("You need to be in a voice channel for me to join and play the TTS!")

    # Jika lebih dari satu pesan ada di antrian, beri tahu pengguna untuk bersabar
    if tts_queue.qsize() > 1:
        await ctx.send("SABAR DULU SATU-SATU!")

@bot.command(name='leave')
async def leave(ctx):
    await ctx.voice_client.disconnect()
    await ctx.send("Goodbye!")

@bot.command(name='sabarr')
async def sabarr(ctx):
    await ctx.send("SABARRRR!!!")


